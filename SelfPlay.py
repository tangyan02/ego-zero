# void addAction(Game &game,
#                int action,
#                std::vector<std::tuple<vector<vector<vector<float>>>, int, std::vector<float>>> &game_data,
#                std::vector<float> &action_probs
# ) {
#     auto state = game.getState();
#     std::tuple<vector<vector<vector<float>>>, int, std::vector<float>> record(state, game.currentPlayer, action_probs);
#     game.makeMove(game.getPointFromIndex(action));
#     game_data.push_back(record);
# }
# std::vector<std::tuple<vector<vector<vector<float>>>, std::vector<float>, std::vector<float>>> selfPlay(int boardSize,
#                                                                                                         int numGames,
#                                                                                                         int numSimulations,
#                                                                                                         int mctsThreadSize,
#                                                                                                         float temperatureDefault,
#                                                                                                         float explorationFactor,
#                                                                                                         const std::string &part,
#                                                                                                         Model &model
# ) {
#
#     MonteCarloTree mcts = MonteCarloTree(&model, explorationFactor);
#     std::vector<std::tuple<vector<vector<vector<float>>>, std::vector<float>, std::vector<float>>> training_data;
#
#     for (int i = 0; i < numGames; i++) {
#         Game game(boardSize);
#         std::vector<std::tuple<vector<vector<vector<float>>>, int, std::vector<float>>> game_data;
#
#         game = randomGame(game, part);
#
#         int step = 0;
#         Node *node = new Node();
#         while (!game.isGameOver()) {
#             //剪枝
# //            mcts.search(game, node, 1);
# //            if (node->children.size() > 1) {
# //                game.vctTimeOut = 16000;
# //                pruning(node, game, part);
# //            }
#
#             //开始mcts预测
#             long startTime = getSystemTime();
#             int simiNum = numSimulations - node->visits;
#             int threadNum = mctsThreadSize;
#             mcts.search(game, node, simiNum, threadNum);
#             if (simiNum > 0) {
#                 cout << part << "search cost " << getSystemTime() - startTime << " ms, simi num " << simiNum << ", "
#                      << "per simi " << (getSystemTime() - startTime) / simiNum << " ms" << endl;
#             }
#
#             std::vector<int> actions;
#             std::vector<float> action_probs;
#             std::tie(actions, action_probs) = mcts.get_action_probabilities(game);
#
#             //计算温度
#             float temperature =
#                     temperatureDefault * (game.boardSize * game.boardSize - step * 16) /
#                     (game.boardSize * game.boardSize);
#
#             temperature /= 2;
#             if (temperature < 0.1) {
#                 temperature = 0.1;
#             }
#
#             std::vector<float> action_probs_temperature = mcts.apply_temperature(action_probs, temperature);
#
#             // 归一化概率分布
#             std::vector<float> action_probs_normalized;
#             float sum = std::accumulate(action_probs_temperature.begin(), action_probs_temperature.end(), 0.0f);
#             for (const auto &prob: action_probs_temperature) {
#                 action_probs_normalized.push_back(prob / sum);
#             }
#
#             // 随机选择
#             std::discrete_distribution<int> distribution(action_probs_normalized.begin(),
#                                                          action_probs_normalized.end());
#             int action = actions[distribution(gen)];
#
#             addAction(game, action, game_data, action_probs);
#             printGame(game, action, action_probs_normalized, temperature, part, node->selectInfo, &model);
#             step++;
#
#             //更新node
#             for (const auto &item: node->children) {
#                 if (item.first != action) {
#                     item.second->release();
#                 }
#             }
#             for (const auto item: node->children) {
#                 if (item.first == action) {
#                     node = item.second;
#                 }
#             }
#         }
#
#         bool win = game.checkWin(game.lastAction.x, game.lastAction.y, game.getOtherPlayer());
#         int winner = 0;
#         if (win) {
#             winner = game.getOtherPlayer();
#         }
#         for (const auto &[state, player, mcts_probs]: game_data) {
#             float value = (winner == player) ? 1.0f : ((winner == (3 - player)) ? -1.0f : 0.0f);
#             training_data.emplace_back(state, mcts_probs, std::vector<float>{value});
#         }
#
#         cout << part << "winner is " << winner << endl;
#     }
#     return training_data;
# }
import numpy as np

import Network
import Utils
from Game import Game
from MCTS import Node, MCTS


def selfPlay(boardSize, numGames, numSimulations, temperatureDefault, explorationFactor, model):
    training_data = []

    for _ in range(numGames):
        game = Game(board_size=boardSize, device=Utils.getDevice())
        root = Node()
        mcts = MCTS(model=model, iterations=numSimulations, exploration_constant=explorationFactor)
        mcts.root = root

        step = 0

        actions = []
        while True:
            step += 1
            print(f"第 {step} 步")

            mcts.search(game)

            # 步骤 1: 提取 visit 的数值
            # 步骤 2: 归一化得到概率分布
            # 步骤 3: 以这个分布的概率，随机取一个对象的索引

            visit_values = np.array([obj.visits for obj in mcts.root.children])
            values_sum = visit_values.sum()
            probabilities = visit_values / values_sum
            # print(visit_values)
            # print(probabilities)
            random_index = np.random.choice(len(mcts.root.children), p=probabilities)
            node = mcts.root.children[random_index]

            # 打印决策
            probs_matrix = np.zeros((game.board_size, game.board_size))
            for child in mcts.root.children:
                if child.move[0] >= 0:
                    probs_matrix[child.move[0]][child.move[1]] = child.visits / values_sum
            print(probs_matrix)

            actions.append((Network.get_state(game), game.current_player, probs_matrix))

            print("玩家 ", game.current_player, "落子 ", node.move, " 访问次数 ", node.visits)
            game.make_move(node.move[0], node.move[1])

            # print(actions)
            if game.end_game_check():
                break

            game.render()

        game.render()

        winner = game.calculate_winner()
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
    selfPlay(9, 1, 800, 1, 3, model)
