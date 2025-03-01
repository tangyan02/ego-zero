import time

import numpy as np
import torch

import SelfPlay
from GameUI import GameUI
from Network import get_model, save_model
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


if __name__ == "__main__":
    dirPreBuild()

    board_size = 9
    tie_mu = 3
    numSimulations = 200
    temperatureDefault = 1
    explorationFactor = 3
    numGames = 10

    lr = 1e-3
    batch_size = 64
    episode = 100000

    # 模型初始化
    device = getDevice()
    model, optimizer = get_model(device, lr)
    game_ui = GameUI(board_size)
    ui_enable = True

    save_model(model, optimizer, batch_size)

    for i_episode in range(1, episode + 1):

        start_time = time.time()

        training_data = SelfPlay.selfPlay(board_size, tie_mu, numGames, numSimulations,
                                          temperatureDefault, explorationFactor, model,
                                          ui_enable, game_ui)

        end_time = time.time()
        print(getTimeStr() + f"自我对弈完毕，用时 {end_time - start_time} s")

        extended_data = get_extended_data(training_data)
        print(getTimeStr() + f"完成扩展自我对弈数据，条数 " + str(len(extended_data)) + " , " + str(
            round(len(extended_data) / (end_time - start_time), 1)) + " 条/s")

        train(extended_data, model, device, optimizer, batch_size, i_episode)

        if i_episode % 100 == 0:
            save_model(model, optimizer, board_size, f"_{i_episode}")
        save_model(model, optimizer, board_size)
        print(getTimeStr() + f"最新模型已保存 episode:{i_episode}")

        print(f"episode {i_episode} 完成")

        # 更新计数
        count = numGames
        update_count(count)
