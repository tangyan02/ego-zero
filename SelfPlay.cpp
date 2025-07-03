
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


tuple<float, Point, float> getNextMove(int step, float temperatureDefault,vector<float>& move_probs,
                                       vector<Point>& moves, MonteCarloTree& mcts)
{
    //按温度决策
    float temperature;
    Point move;
    float rate;

    if (step < stoi(ConfigReader::get("temperatureDownBeginStep")))
    {
        //前n步，温度>0
        temperature = temperatureDefault;
        std::discrete_distribution<int> distribution(move_probs.begin(), move_probs.end());
        int index = distribution(gen);
        move = moves[index];
        rate = move_probs[index];
    }
    else
    {
        //温度为0
        temperature = 0;
        move = mcts.get_max_visit_move();
        rate = 1;
    }
    return tuple(temperature, move, rate);
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

            auto [moves, moves_probs] = mcts.get_action_probabilities();
            //决策下一步
            auto [temperature, move, rate] = getNextMove(step, temperatureDefault, moves_probs, moves, mcts);
            std::tie(moves, moves_probs) = mcts.get_action_probabilities();

            // 随机选择
            std::discrete_distribution<int> distribution(moves_probs.begin(),
                                                         moves_probs.end());

            // 构造矩阵
            vector<float> probs_matrix(game.boardSize * game.boardSize, 0);

            if (!moves[0].isNull()) {
                for (int k = 0; k < moves.size(); k++) {
                    auto p = moves[k];
                    probs_matrix[game.getMoveIndex(p.x, p.y)] = moves_probs[k];
                }
            }
            game_data.emplace_back(Model::get_state(game), game.currentPlayer, probs_matrix);

            // cout << "bannedMoves: ";
            // for (auto move: game.bannedMoves) {
            //     cout << "(" << move.x << "," << move.y << ") ";
            // }
            // cout << endl;
            //
            // cout << "eatMoves: ";
            // for (auto [move, gourp]: game.eatMoves) {
            //     cout << "(" << move.x << "," << move.y << ") ";
            // }
            // cout << endl;

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
        auto [blackScore,whiteScore] = game.calculateScore();
        cout << "winner is " << ((winner == 1) ? "x" : ((winner == 2) ? "o" : " nobody"))
                << " score " << blackScore << ":" << whiteScore << endl;
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
