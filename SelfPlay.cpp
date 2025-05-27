//
// Created by 唐雁 on 2025/4/16.
//

#include "SelfPlay.h"

#include "ConfigReader.h"
#include "Utils.h"

// 创建一个随机数生成器
std::random_device rd;
std::mt19937 gen(rd());


void printGame(Model &model, Game &game, Point move, double rate,
               float temperature, vector<float> probs) {
    game.render();

    auto state = Model::get_state(game);
    auto [value, prob_metrix] = model.evaluate_state(state);

    std::string pic = ((3 - game.currentPlayer) == 1) ? "x" : "o";
    cout << pic << " move is " << move.x << ","
            << move.y
            << " on rate " << round(rate * 1000) / 1000
            << " temperature " << temperature
            << " value " << -value
            << endl;


    std::cout << std::fixed << std::setprecision(3);
    for (int i = 0; i < probs.size(); i++) {
        cout << probs[i] << " ";
        if (i % game.boardSize == game.boardSize - 1) {
            cout << endl;
        }
    }
}

std::vector<std::tuple<vector<vector<vector<float> > >, std::vector<float>, std::vector<float> > > selfPlay(
    int shard,
    int boardSize,
    float tieMu,
    int numGames,
    int numSimulations,
    float temperatureDefault,
    float explorationFactor,
    Model &model
) {
    MonteCarloTree mcts = MonteCarloTree(&model, explorationFactor, true);
    std::vector<std::tuple<vector<vector<vector<float> > >, std::vector<float>, std::vector<float> > > training_data;

    for (int i = 0; i < numGames; i++) {
        Game game(boardSize, tieMu);
        std::vector<std::tuple<vector<vector<vector<float> > >, int, std::vector<float> > > game_data;

        int step = 0;
        while (!game.endGameCheck()) {
            Node node;
            //开始mcts预测
            auto startTime = getSystemTime();
            int simiNum = numSimulations;
            mcts.search(game, &node, simiNum);
            if (simiNum > 0) {
                cout << "======== " << shard << "-" << i << " =======" << endl << "search cost " << getSystemTime() -
                        startTime << " ms, simi num " << simiNum << ", "
                        << "per simi " << (getSystemTime() - startTime) / (float) simiNum << " ms" << endl;
            }

            std::vector<Point> moves;
            std::vector<float> moves_probs;
            std::tie(moves, moves_probs) = mcts.get_action_probabilities();
            float temperature = temperatureDefault;

            if (int temperatureDownBeginStep = stoi(ConfigReader::get("temperatureDownBeginStep"));
                game.history.size() > temperatureDownBeginStep) {
                int beginStep = game.history.size() - temperatureDownBeginStep;
                temperature -= static_cast<float>(beginStep) * stof(ConfigReader::get("decreasePerStep"));
                if (temperature < stof(ConfigReader::get("minTemperature"))) {
                    temperature = stof(ConfigReader::get("minTemperature"));
                }
            }

            Point move;

            std::vector<float> action_probs_temperature = mcts.apply_temperature(moves_probs, temperature);

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
            move = moves[index];
            float rate = action_probs_normalized[index];

            // 构造矩阵
            vector<float> probs_matrix(game.boardSize * game.boardSize, 0);

            if (!moves[0].isNull()) {
                for (int k = 0; k < moves.size(); k++) {
                    auto p = moves[k];
                    probs_matrix[game.getMoveIndex(p.x, p.y)] = moves_probs[k];
                }
            }
            game_data.emplace_back(Model::get_state(game), game.currentPlayer, probs_matrix);

            cout << "bannedMoves: ";
            for (auto move: game.bannedMoves) {
                cout << "(" << move.x << "," << move.y << ") ";
            }
            cout << endl;

            cout << "eatMoves: ";
            for (auto [move, gourp]: game.eatMoves) {
                cout << "(" << move.x << "," << move.y << ") ";
            }
            cout << endl;

            game.makeMove(move.x, move.y);

            printGame(model, game, move, rate, temperature, probs_matrix);
            step++;
        }

        auto winner = game.calculateWinner();
        for (const auto &[state, player, mcts_probs]: game_data) {
            float value = 0;
            if (winner == player) {
                value = 1;
            }
            if (winner == 3 - player) {
                value = -1;
            }
            training_data.emplace_back(state, mcts_probs, std::vector<float>{value});
        }

        cout << "winner is " << ((winner == 1) ? "x" : ((winner == 2) ? "o" : " nobody")) << endl;
    }
    return training_data;
}

void recordSelfPlay(
    int boardSize,
    float tieMu,
    int numGames,
    int numSimulations,
    float temperatureDefault,
    float explorationFactor,
    int shard,
    string *modelPath,
    string *coreType) {
    try {
        Model model;
        model.init(*modelPath, *coreType);

        // 创建文件流对象
        std::ofstream file("record/data_" + to_string(shard) + ".txt");

        if (file.is_open()) {
            auto data = selfPlay(shard, boardSize, tieMu, numGames, numSimulations,
                                 temperatureDefault, explorationFactor, model);
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
    } catch (const std::exception &e) {
        // 打印异常信息
        std::cerr << "Exception in shard " << shard << ": " << e.what() << std::endl;
        std::cout << "Exception in shard " << shard << ": " << e.what() << std::endl;
    }
}
