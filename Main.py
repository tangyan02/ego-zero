import time

import numpy as np
import multiprocessing

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


def self_play_process(board_size, tie_mu, numGames, total_games_count, numSimulations,
                      temperatureDefault, explorationFactor, ui_enable):
    """
    用于多进程处理的selfPlay函数
    """
    # 在子进程中创建GameUI对象
    game_ui = GameUI(board_size)
    return SelfPlay.selfPlay(board_size, tie_mu, numGames, total_games_count, numSimulations,
                             temperatureDefault, explorationFactor, ui_enable, game_ui)


if __name__ == "__main__":
    dirPreBuild()

    board_size = 9
    tie_mu = 3.25
    numSimulations = 200
    temperatureDefault = 1
    explorationFactor = 5
    numGames = 5
    num_processes = 4
    # 开启4个进程

    lr = 1e-3
    batch_size = 64
    episode = 100000
    total_games_count = update_count(0)

    # 模型初始化
    device = getDevice()
    model, optimizer = get_model(device, lr)
    ui_enable = True

    save_model(model, optimizer, board_size)

    for i_episode in range(1, episode + 1):

        start_time = time.time()

        pool = multiprocessing.Pool(processes=num_processes)
        args = [(board_size, tie_mu, numGames, total_games_count, numSimulations,
                 temperatureDefault, explorationFactor, ui_enable) for _ in range(num_processes)]
        results = pool.starmap(self_play_process, args)

        pool.close()
        pool.join()

        # 合并结果
        training_data = []
        for data in results:
            training_data.extend(data)

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
        count = numGames * num_processes
        total_games_count = update_count(count)