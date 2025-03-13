import numpy as np
from torch.utils.data import DataLoader

import Network
import Utils
from Game import Game
from MCTS import Node, MCTS
from SampleSet import SampleSet


def selfPlay(boardSize, tie_mu, numGames, num_processes,
             numSimulations, temperatureDefault, explorationFactor):
    onnx_model = Network.load_onnx_model("model/model_latest.onnx")

    if onnx_model is None:
        return []

    training_data = []

    for i_numGames in range(numGames):
        game = Game(board_size=boardSize, device=Utils.getDevice(), tie_mu=tie_mu)
        root = Node()
        mcts = MCTS(model=onnx_model, iterations=numSimulations, exploration_constant=explorationFactor)
        mcts.root = root

        step = 0

        actions = []
        while True:
            step += 1
            print(f"进程 {num_processes}, 第 {i_numGames} 局, 第 {step} 步")

            mcts.search(game)
            mcts.root = Node()

            # 步骤 1: 提取 visit 的数值
            # 步骤 2: 归一化得到概率分布
            # 步骤 3: 以这个分布的概率，随机取一个对象的索引

            visit_values = np.array([obj.visits for obj in mcts.root.children])
            visit_sum = visit_values.sum()

            probabilities = visit_values / visit_sum

            # print(visit_values)
            # print(probabilities)
            random_index = np.random.choice(len(mcts.root.children), p=probabilities)
            node = mcts.root.children[random_index]

            # 打印决策
            probs_matrix = np.zeros((game.board_size, game.board_size))
            for child in mcts.root.children:
                if child.move[0] >= 0:
                    probs_matrix[child.move[0]][child.move[1]] = child.visits / visit_sum
            # print(probs_matrix)

            actions.append((Network.get_state(game).cpu(), game.current_player, probs_matrix))

            print("玩家 ", game.current_player, "落子 ", node.move, " 访问次数 ", node.visits)
            game.make_move(node.move[0], node.move[1])



            if game.end_game_check():
                break
            # print(actions)
            game.render()

        winner = game.calculate_winner()
        print(f"本局胜方 玩家 {winner}")

        game.render()

        for (state, player, probs) in actions:
            value = 0
            if winner == player:
                value = 1.0
            if winner == 3 - player:
                value = -1.0
            training_data.append((state, probs, value))

    del onnx_model
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
