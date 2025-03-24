import numpy as np
from torch.utils.data import DataLoader

import Logger
import Network
import Utils
from Game import Game
from MCTS import Node, MCTS
from SampleSet import SampleSet
import time

import gc


def sub_log(num_processes, i_numGames, text):
    Logger.info(f"进程{num_processes} 第{i_numGames}局 - {text} ")


def selfPlay(boardSize, tie_mu, numGames, num_processes,
             numSimulations, temperatureDefault, explorationFactor):
    onnx_model = Network.load_onnx_model("model/model_latest_fp16.onnx")

    if onnx_model is None:
        return []

    training_data = []

    for i_numGames in range(numGames):
        game = Game(board_size=boardSize, device=Utils.getDevice(), tie_mu=tie_mu)
        root = Node()
        mcts = MCTS(model=onnx_model, exploration_constant=explorationFactor)
        mcts.root = root

        step = 0

        actions = []
        while True:
            start_time = time.time()

            step += 1

            needSearchCount = numSimulations - mcts.root.visits

            sub_log(num_processes, i_numGames, f"计划模拟次数 {needSearchCount},  第 {step} 步")
            mcts.search(game, needSearchCount)

            # 步骤 1: 提取 visit 的数值
            # 步骤 2: 归一化得到概率分布
            # 步骤 3: 以这个分布的概率，随机取一个对象的索引

            visit_values = np.array([obj.visits for obj in mcts.root.children])
            visit_sum = visit_values.sum()

            probabilities = visit_values / visit_sum

            random_index = np.random.choice(len(mcts.root.children), p=probabilities)
            node = mcts.root.children[random_index]

            # 打印决策
            probs_matrix = np.zeros((game.board_size, game.board_size))
            for child in mcts.root.children:
                if child.move[0] >= 0:
                    probs_matrix[child.move[0]][child.move[1]] = child.visits / visit_sum
            # print(probs_matrix)

            actions.append((Network.get_state(game), game.current_player, probs_matrix))

            end_time = time.time()
            sub_log(num_processes, i_numGames,
                    f"玩家 {game.current_player}, 落子  {node.move},  访问次数 {node.visits} "
                    f", 速度 {round(needSearchCount / (end_time - start_time), 1)} 次/秒")
            game.make_move(node.move[0], node.move[1])

            if game.end_game_check():
                break
            # print(actions)
            game.render()

            # 重置跟节点，并清理其他分支内存
            node.parent = None
            mcts.root.children.remove(node)

            mcts.root.clear()
            del mcts.root

            mcts.root = node

            ### 强制进行垃圾回收
            gc.collect()

        winner = game.calculate_winner()
        sub_log(num_processes, i_numGames, f"本局胜方 玩家 {winner}")

        game.render()

        for (state, player, probs) in actions:
            value = 0
            if winner == player:
                value = 1.0
            if winner == 3 - player:
                value = -1.0
            training_data.append((state, probs, value))

    return training_data


if __name__ == "__main__":
    model, _ = Network.get_model(Utils.getDevice(), 1e-3)
    training_data = selfPlay(9, 3, 1, 0, 10, 1, 3)
    print(training_data)
    sample_set = SampleSet(training_data)
    dataloader = DataLoader(sample_set, batch_size=32, shuffle=True)
    # 训练循环
    running_loss = 0.0
    for batch_data in dataloader:
        states = batch_data[0].float().to(Utils.getDevice())
        mcts_probs = batch_data[1].float().to(Utils.getDevice())
        values = batch_data[2].float().to(Utils.getDevice())
        values = values.unsqueeze(dim=0)
        print(values.shape)
