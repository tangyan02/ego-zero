import os

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import optim

import Utils
from Game import Game


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


def save_model(model, optimizer, boardSize, subfix="", ):
    path = f"model/checkpoint{subfix}.pth"
    torch.save({
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
    }, path)

    torch.jit.save(torch.jit.script(model), "model/model_latest.pt")

    # 导出onnx
    # model.eval()
    # example = torch.randn(1, model.input_channels, boardSize, boardSize, requires_grad=True,
    #                       device=next(model.parameters()).device)
    # torch.onnx.export(model,
    #                   (example),
    #                   'model/model_latest.onnx',
    #                   input_names=['input'],
    #                   output_names=['value', "act"],
    #                   opset_version=17,
    #                   verbose=False)
    #
    # example = torch.randn(1, model.input_channels, boardSize, boardSize, requires_grad=True,
    #                       device=next(model.parameters()).device)
    # torch.onnx.export(model,
    #                   (example),
    #                   'model/model_latest_single_batch.onnx',
    #                   input_names=['input'],
    #                   output_names=['value', "act"],
    #                   opset_version=17,
    #                   verbose=False)
    # model.train()


def evaluate_state(model, state):
    ret = model(state)
    return ret[0].item(), torch.exp(ret[1]).cpu().detach().numpy()


def get_state(game):
    limit = 8
    tensor = torch.zeros(limit * 2 + 1, game.board_size, game.board_size, device=game.device)
    k = 0
    for board in game.history[-limit:][::-1]:
        for x in range(game.board_size):
            for y in range(game.board_size):
                if board[x][y] == game.current_player:
                    tensor[k, x, y] = 1
                else:
                    tensor[k, x, y] = 0
        k = k + 1

    k = limit
    for board in game.history[-limit:][::-1]:
        for x in range(game.board_size):
            for y in range(game.board_size):
                if board[x][y] == 3 - game.current_player:
                    tensor[k, x, y] = 1
                else:
                    tensor[k, x, y] = 0
        k = k + 1
    # 判断自己是先还是后
    if game.current_player == 1:
        for x in range(game.board_size):
            for y in range(game.board_size):
                tensor[k, x, y] = 1

    return tensor


if __name__ == "__main__":
    # 测试代码
    model, optimizer = get_model(device=Utils.getDevice(), lr=0.01)
    game = Game(9)
    game.make_move(1, 1)
    game.make_move(2, 2)
    game.make_move(3, 3)
    # print(game.history)
    # game.render()
    # tensor = convert_game_to_state(game)
    # for i in range(16):
    #     print(i)
    #     print(tensor[i])
    # ret = network(tensor)
    # print(torch.exp(ret[1]))
    # print(ret[0].item())

    print(evaluate_state(model, get_state(game)))
