//
// Created by 唐雁 on 2025/5/24.
//

#include "Bridge.h"


void Bridge::move(int x, int y) {
    game->makeMove(x, y);
    Point move(x,y);
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


vector<float> Bridge::predict(int simiNum) {

    mcts->search(*game, node, simiNum);

    std::vector<Point> moves;
    std::vector<float> moves_probs;
    std::tie(moves, moves_probs) = mcts->get_action_probabilities(*game);

    // 构造矩阵
    vector<float> probs_matrix(game->boardSize * game->boardSize, 0);

    if (!moves[0].isNull()) {
        for (int k = 0; k < moves.size(); k++) {
            auto p = moves[k];
            probs_matrix[game->getMoveIndex(p.x, p.y)] = moves_probs[k];
        }
    }

    return probs_matrix;
}

// 解析指令参数
void Bridge::parse_coordinates(const string &args, int &x, int &y) {
    size_t comma = args.find(',');
    if (comma == string::npos) throw invalid_argument("Invalid format");

    x = stoi(args.substr(0, comma));
    y = stoi(args.substr(comma + 1));
}

Bridge::Bridge() {

    // Read configuration
    auto config = readConfigFile("application.conf");

    // Parse parameters with defaults if not found
    int boardSize = config.count("boardSize") ? stoi(config["boardSize"]) : 9;
    float tieMu = config.count("tieMu") ? stof(config["tieMu"]) : 3.25f;
    float explorationFactor = config.count("explorationFactor") ? stof(config["explorationFactor"]) : 3;
    string modelPath = config.count("modelPath") ? config["modelPath"] : "./model/model_latest.onnx";
    string coreType = config.count("coreType") ? config["coreType"] : "cpu";

    model = new Model();
    model->init(modelPath, coreType);

    game = new Game(boardSize, tieMu);
    mcts = new MonteCarloTree(model, explorationFactor);
}

void Bridge::startGame() {

    // Read configuration
    auto config = readConfigFile("application.conf");

    // Parse parameters with defaults if not found
    int boardSize = config.count("boardSize") ? stoi(config["boardSize"]) : 9;
    float tieMu = config.count("tieMu") ? stof(config["tieMu"]) : 3.25f;
    float explorationFactor = config.count("explorationFactor") ? stof(config["explorationFactor"]) : 3;
    string modelPath = config.count("modelPath") ? config["modelPath"] : "./model/model_latest.onnx";
    string coreType = config.count("coreType") ? config["coreType"] : "cpu";

    std::string line;
    while (std::getline(std::cin, line)) {
        try {
            // 分割指令和参数
            istringstream iss(line);
            string command;
            iss >> command;

            string args;
            getline(iss, args);
            args.erase(0, args.find_first_not_of(' ')); // 去除前导空格

            // 处理不同指令
            if (command == "MOVE") {
                int x, y;
                parse_coordinates(args, x, y);
                move(x, y);
                cout << "MOVE SUCCESS" << endl;
            } else if (command == "PREDICT") {
                int simiNum = stoi(args);
                auto result = predict(simiNum);
                for (const auto &item: result) {
                    cout << item << " ";
                }
                cout << endl;
            } else {
                throw invalid_argument("Unknown command");
            }
        } catch (...) {
            std::cerr << "发生异常" << std::endl;
        }
    }

}
