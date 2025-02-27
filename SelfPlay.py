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
from Game import Game
from MCTS import Node, MCTS


def selfPlay(boardSize, numGames, numSimulations, temperatureDefault, explorationFactor, model):
    # 测试代码
    game = Game(board_size=boardSize)
    game.reset()
    game.render()

    node = Node(game=game)
    mcts = MCTS(model=model, iterations=numSimulations)
    mcts.root = node

    for i in range(numGames):
        print(f"第 {i} 步")

        mcts.search(game)
        best_child = max(mcts.root.children, key=lambda child: child.visits)
        sorted_children = sorted(mcts.root.children, key=lambda child: child.visits, reverse=True)
        moves = [(child.move, child.visits) for child in sorted_children]
        print("可选落子", moves)
        print("玩家 ", game.current_player, "落子 ", best_child.move, " 访问次数 ", best_child.visits)
        game.make_move(best_child.move[0], best_child.move[1])
        if game.end_game_check():
            break

        game.render()
