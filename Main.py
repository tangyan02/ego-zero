import time

import numpy as np
import torch

from Network import get_network, save_network
from Train import train
from Utils import getDevice, getTimeStr, dirPreBuild


def get_extended_data(play_data):
    extend_data = []
    for state, mcts_porb, value in play_data:
        for i in [1, 2, 3, 4]:
            # rotate counterclockwise
            equi_state = np.array([np.rot90(s, i) for s in state])
            board_size = state.shape[1]
            equi_mcts_prob = np.rot90(mcts_porb.reshape(board_size, board_size), i)
            extend_data.append((equi_state, equi_mcts_prob.flatten(), value))
            # flip horizontally
            equi_state = np.array([np.fliplr(s) for s in equi_state])
            equi_mcts_prob = np.fliplr(equi_mcts_prob)
            extend_data.append((equi_state,
                                equi_mcts_prob.flatten(),
                                value))
    return extend_data


def update_count(k, filepath="model/count.txt"):
    try:
        with open(filepath, 'r') as f:
            count = int(f.read())
    except FileNotFoundError:
        count = 0

    count += k

    with open(filepath, 'w') as f:
        f.write(str(count))

    print(getTimeStr() + f"更新对局计数，当前完成对局 " + str(count))
    return count


dirPreBuild()

lr = 1e-3
batch_size = 64
episode = 100000

# 模型初始化
device = getDevice()
network, optimizer = get_network(device, lr)

save_network(network, optimizer)
network.to("cpu")
torch.cuda.empty_cache()

for i_episode in range(1, episode + 1):

    start_time = time.time()

    training_data = callSelfPlayInCpp(shard_nums, part_nums, worker_nums, node_num)

    end_time = time.time()
    print(getTimeStr() + f"自我对弈完毕，用时 {end_time - start_time} s")

    extended_data = get_extended_data(training_data)
    print(getTimeStr() + f"完成扩展自我对弈数据，条数 " + str(len(extended_data)) + " , " + str(
        round(len(extended_data) / (end_time - start_time), 1)) + " 条/s")

    # 网络移动到GPU中
    network.to(device)
    print(getTimeStr() + f"模型已移动到" + device)

    train(extended_data, network, device, optimizer, batch_size, i_episode)

    if i_episode % 100 == 0:
        save_network(network, optimizer, f"_{i_episode}")
    save_network(network, optimizer)
    print(getTimeStr() + f"最新模型已保存 episode:{i_episode}")

    # 网络移动到CPU用，释放内存
    memory_allocated = torch.cuda.memory_allocated()
    network.to("cpu")
    torch.cuda.empty_cache()
    print(getTimeStr() + f"GPU内存已清理")

    print(f"episode {i_episode} 完成")
    # 更新计数
    # count = sum(shard_nums[i] * part_nums[i] for i in range(node_num))
    # update_count(count)
