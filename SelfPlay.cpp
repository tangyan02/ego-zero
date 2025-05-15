//
// Created by 唐雁 on 2025/4/16.
//

#include "SelfPlay.h"
#include "Utils.h"

// 创建一个随机数生成器
std::random_device rd;
std::mt19937 gen(rd());


void printGame(Game &game, Point move, double rate,
               float temperature) {
        game.render();

        std::string pic = ((3-game.currentPlayer) == 1) ? "x" : "o";
        cout << pic << " move is " << move.x << ","
             <<  move.y
             << " on rate " << round(rate * 1000) / 1000
             << " temperature " << round(temperature * 100) / 100
             << endl;

}


void addMove(Game &game,
               std::vector<std::tuple<vector<vector<vector<float>>>, int, std::vector<float>>> &game_data,
               std::vector<float> &action_probs
) {
    auto state = Model::get_state(game);
    std::tuple<vector<vector<vector<float>>>, int, std::vector<float>> record(state, game.currentPlayer, action_probs);
    game_data.push_back(record);
}

std::vector<std::tuple<vector<vector<vector<float> > >, std::vector<float>, std::vector<float> > > selfPlay(
    int shard,
    int boardSize,
    int numGames,
    int numSimulations,
    float temperatureDefault,
    float explorationFactor,
    Model &model
) {

    MonteCarloTree mcts = MonteCarloTree(&model, explorationFactor);
    std::vector<std::tuple<vector<vector<vector<float>>>, std::vector<float>, std::vector<float>>> training_data;

    for (int i = 0; i < numGames; i++) {
        Game game(boardSize);
        std::vector<std::tuple<vector<vector<vector<float>>>, int, std::vector<float>>> game_data;

        int step = 0;
        Node *node = new Node();
        while (!game.endGameCheck()) {

          //开始mcts预测
            long startTime = getSystemTime();
            int simiNum = numSimulations - node->visits;
            mcts.search(game, node, simiNum);
            if (simiNum > 0) {
                cout << "======== "<<shard<<"-" << i <<" =======" << endl << "search cost " << getSystemTime() - startTime << " ms, simi num " << simiNum << ", "
                     << "per simi " << (getSystemTime() - startTime) / simiNum << " ms" << endl;
            }

            std::vector<Point> actions;
            std::vector<float> action_probs;
            std::tie(actions, action_probs) = mcts.get_action_probabilities(game);

            //计算温度
            float temperature = temperatureDefault;
//            float temperature =
//                    temperatureDefault * (game.boardSize * game.boardSize - step * 16) /
//                    (game.boardSize * game.boardSize);
//
//            temperature /= 2;
//            if (temperature < 0.1) {
//                temperature = 0.1;
//            }

            std::vector<float> action_probs_temperature = mcts.apply_temperature(action_probs, temperature);

            // 归一化概率分布
            std::vector<float> action_probs_normalized;
            float sum = std::accumulate(action_probs_temperature.begin(), action_probs_temperature.end(), 0.0f);
            for (const auto &prob: action_probs_temperature) {
                action_probs_normalized.push_back(prob / sum);
            }

            // 随机选择
            std::discrete_distribution<int> distribution(action_probs_normalized.begin(),
                                                         action_probs_normalized.end());
            int index = distribution(gen);
            Point move = actions[index];

            addMove(game, game_data, action_probs);

            game.makeMove(move.x, move.y);

            printGame(game, move, action_probs_normalized[index], temperature);
            step++;

            //更新node
            for (const auto &item: node->children) {
                if (item.first != move) {
                    item.second->release();
                }
            }
            for (const auto item: node->children) {
                if (item.first == move) {
                    node = item.second;
                }
            }
        }

        auto winner = game.calculateWinner();
        for (const auto &[state, player, mcts_probs]: game_data) {
            float value = (winner == player) ? 1.0f : ((winner == (3 - player)) ? -1.0f : 0.0f);
            training_data.emplace_back(state, mcts_probs, std::vector<float>{value});
        }

        cout << "winner is " << ((winner == 1) ? "x" : "o") << endl;
    }
    return training_data;
}

void recordSelfPlay(
        int boardSize,
        int numGames,
        int numSimulations,
        float temperatureDefault,
        float explorationFactor,
        int shard,
        Model* model){

        // 创建文件流对象
        std::ofstream file("record/data_" + to_string(shard) + ".txt");

        if (file.is_open()) {

                auto data = selfPlay(shard, boardSize, numGames, numSimulations,
                                     temperatureDefault, explorationFactor, *model);
                file << data.size() << endl;
                std::cout << "data count " << data.size() << endl;
                for (auto &item: data) {
                        auto state = get<0>(item);

                        // 获取张量的维度
                        int64_t dim0 = state.size();
                        int64_t dim1 = state[0].size();
                        int64_t dim2 = state[0][0].size();

                        file << dim0 << " " << dim1 << " " << dim2 << endl;
                        // 遍历张量并打印数值
                        for (int64_t i = 0; i < dim0; ++i) {
                                for (int64_t j = 0; j < dim1; ++j) {
                                        for (int64_t k = 0; k < dim2; ++k) {
                                                file << state[i][j][k] << " ";
                                        }
                                        file << endl;
                                }
                        }

                        vector<float> mctsProbList = get<1>(item);
                        file << mctsProbList.size() << endl;
                        for (auto f: mctsProbList) {
                                file << f << " ";
                        }
                        file << endl;

                        vector<float> valueList = get<2>(item);
                        file << valueList.size() << endl;
                        for (auto f: valueList) {
                                file << f << " ";
                        }
                        file << endl;
                }

                // 关闭文件
                file.close();
                std::cout << "Data has been written to file." << std::endl;
        } else {
                std::cerr << "Failed to open file." << std::endl;
        }
}
