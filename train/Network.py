import os

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import optim

import Utils
from Game import Game
import onnxruntime as ort
import onnx

from onnxconverter_common import float16


# 定义一个Residual block
class ResidualBlock(nn.Module):
    def __init__(self, channels):
        super(ResidualBlock, self).__init__()

        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(channels)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(channels)

    def forward(self, x):
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)

        out += residual
        out = self.relu(out)

        return out


class PolicyValueNetwork(nn.Module):
    def __init__(self):
        self.board_size = 9
        self.input_channels = 17
        self.residual_channels = 128
        super(PolicyValueNetwork, self).__init__()

        # common layers
        self.conv1 = nn.Conv2d(self.input_channels, self.residual_channels, kernel_size=(3, 3), padding=1)

        self.residual_blocks = nn.Sequential(
            ResidualBlock(self.residual_channels),
            ResidualBlock(self.residual_channels),
            ResidualBlock(self.residual_channels),
            ResidualBlock(self.residual_channels),
            ResidualBlock(self.residual_channels),
            ResidualBlock(self.residual_channels),
            ResidualBlock(self.residual_channels),
            ResidualBlock(self.residual_channels),
            ResidualBlock(self.residual_channels),
            ResidualBlock(self.residual_channels)
        )

        # action policy layers
        self.act_conv1 = nn.Conv2d(self.residual_channels, 4, kernel_size=(1, 1), bias=False)
        self.act_bn1 = nn.BatchNorm2d(4)
        self.act_fc1 = nn.Linear(4 * self.board_size * self.board_size,
                                 self.board_size * self.board_size)
        # state value layers
        self.val_conv1 = nn.Conv2d(self.residual_channels, 2, kernel_size=(1, 1), bias=False)
        self.val_bn1 = nn.BatchNorm2d(2)
        self.val_fc1 = nn.Linear(2 * self.board_size * self.board_size, 64)
        self.val_fc2 = nn.Linear(64, 1)

    def forward(self, state_input):
        if state_input.dim() == 3:
            state_input = torch.unsqueeze(state_input, dim=0)

        # common layers
        x = F.relu(self.conv1(state_input))
        x = self.residual_blocks(x)

        # action policy layers
        x_act = self.act_conv1(x)
        x_act = self.act_bn1(x_act)
        x_act = F.relu(x_act)
        x_act = x_act.view(-1, 4 * self.board_size * self.board_size)
        x_act = F.log_softmax(self.act_fc1(x_act), dim=1)

        # state value layers
        x_val = self.val_conv1(x)
        x_val = self.val_bn1(x_val)
        x_val = F.relu(x_val)
        x_val = x_val.view(-1, 2 * self.board_size * self.board_size)
        x_val = F.relu(self.val_fc1(x_val))
        x_val = torch.tanh(self.val_fc2(x_val))

        return x_val, x_act


def get_model(device, lr):
    model = PolicyValueNetwork()
    model.to(device)  # 将网络移动到设备

    # 定义优化器
    optimizer = optim.Adam(model.parameters(), lr)

    if os.path.exists(f"model/checkpoint.pth"):
        checkpoint = torch.load("model/checkpoint.pth", device)
        model.load_state_dict(checkpoint['model_state_dict'])

        # 重新定义优化器，确保优化器的状态在正确的设备上
        optimizer = optim.Adam(model.parameters(), lr)
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])

    return model, optimizer


def save_model(model, optimizer, boardSize, fp16=False):
    path = f"model/checkpoint.pth"
    torch.save({
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
    }, path)

    # 导出onnx
    model.eval()
    example = torch.randn(model.input_channels, boardSize, boardSize, requires_grad=True,
                          device=next(model.parameters()).device)
    torch.onnx.export(model,
                      (example),
                      'model/model_latest.onnx',
                      input_names=['input'],
                      output_names=['value', "act"],
                      opset_version=17,
                      verbose=False)

    onnx_model = onnx.load("model/model_latest.onnx")
    onnx_model_fp16 = float16.convert_float_to_float16(onnx_model)
    onnx.save(onnx_model_fp16, "model/model_latest_fp16.onnx")

    model.train()


def evaluate_state(model, state):
    ret = model(state)
    value, probs = ret[0].item(), torch.exp(ret[1]).cpu().detach().numpy()
    return value, probs


def get_state(game):
    limit = 8
    # 直接创建 NumPy 数组
    numpy_array = np.zeros((limit * 2 + 1, game.board_size, game.board_size))
    k = 0
    for board in game.history[-limit:][::-1]:
        for x in range(game.board_size):
            for y in range(game.board_size):
                if board[x][y] == game.current_player:
                    numpy_array[k, x, y] = 1
                else:
                    numpy_array[k, x, y] = 0
        k = k + 1

    k = limit
    for board in game.history[-limit:][::-1]:
        for x in range(game.board_size):
            for y in range(game.board_size):
                if board[x][y] == 3 - game.current_player:
                    numpy_array[k, x, y] = 1
                else:
                    numpy_array[k, x, y] = 0
        k = k + 1

    # 判断自己是先还是后
    if game.current_player == 1:
        for x in range(game.board_size):
            for y in range(game.board_size):
                numpy_array[k, x, y] = 1

    return numpy_array


def load_onnx_model(model_path):
    """
    加载 ONNX 模型
    :param model_path: ONNX 模型的路径
    :return: ONNX 运行时的会话
    """
    try:
        # 获取当前环境中可用的执行提供程序
        available_providers = ort.get_available_providers()

        # 设置优先级顺序（按优先级从高到低）
        preferred_providers = [
            'CUDAExecutionProvider',    # GPU (NVIDIA)
            'CoreMLExecutionProvider',  # Apple Core ML
            'CPUExecutionProvider'      # 默认CPU
        ]

        # 筛选出实际可用的提供程序（按优先级顺序）
        providers = [p for p in preferred_providers if p in available_providers]

        # 如果没有可用的提供程序，则使用默认（通常是CPU）
        if not providers:
            providers = available_providers
        session = ort.InferenceSession(model_path, providers=providers)
        print("当前使用的执行提供程序:", session.get_providers())
        return session
    except Exception as e:
        print(f"Failed to load ONNX model: {e}")
        return None


def evaluate_state_onnx(onnx_model, input):
    """
    使用 ONNX 模型进行推理
    :param session: ONNX 运行时的会话
    :param input_tensor: 输入的张量
    :return: 推理结果
    """

    # 获取输入名称
    input_tensor = torch.from_numpy(input).float()
    input_name = onnx_model.get_inputs()[0].name

    # 将输入张量的精度转换为 fp16
    input_tensor = input_tensor.half()

    # 进行推理
    outputs = onnx_model.run(None, {input_name: input_tensor.cpu().numpy()})
    value, probs = outputs
    value = value[0][0]
    probs = np.exp(probs[0])
    return value, probs


if __name__ == "__main__":
    # 测试代码
    board_size = 9

    model, optimizer = get_model(device=Utils.getDevice(), lr=0.01)
    save_model(model, optimizer, board_size)
    data = """
    x x x x o x o o .
    . x . x o . o . o
    x x x x o o o o .
    x . o . . o . o o
    x . x . o o x o o
    . x . . . o o . o
    . . . . x o . o x
    . x . . . . . . x
    . . . . . . x x x
    """
    game = Game(board_size)
    game.parse(data)

    onnx_session = load_onnx_model('model/model_latest.onnx')
    # 获取输入状态
    state = get_state(game)
    # 进行 ONNX 推理
    value, probs = evaluate_state_onnx(onnx_session, state)
    print("ONNX 推理结果:", value, probs)

    # prob = onnx_outputs[1].reshape(9, 9)
    # print(prob)

    # predicted_values, predicted_action_logits = model(state)
    # print("predicted_values, predicted_action_logits shape", predicted_values.shape, predicted_action_logits.shape)
    # print(predicted_values, predicted_action_logits)
