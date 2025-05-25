//
// Created by 唐雁 on 2025/5/24.
//

#include "Bridge.h"


// 解析指令参数
Point Bridge::parse_coordinates(const string &args) {
    size_t comma = args.find(',');
    if (comma == string::npos) throw invalid_argument("Invalid format");
    return {stoi(args.substr(0, comma)), stoi(args.substr(comma + 1))};
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

    node = new Node();
}

void Bridge::startGame() {

    // Read configuration
    auto config = readConfigFile("application.conf");

    // Parse parameters with defaults if not found
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
                move(args);
            } else if (command == "PREDICT") {
                predict(args);
            } else if (command == "END_CHECK") {
                end_check(args);
            } else if (command == "WINNER_CHECK") {
                winner_check(args);
            } else if (command == "CURRENT_PLAYER") {
                current_player(args);
            } else if (command == "BOARD") {
                board(args);
            } else if (command == "GET_MOVES") {
                get_moves(args);
            } else {
                throw invalid_argument("Unknown command");
            }
        } catch (...) {
            std::cerr << "发生异常" << std::endl;
        }
    }

}

void Bridge::move(string &args) {
    auto move = parse_coordinates(args);
    game->makeMove(move.x, move.y);
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
    cout << "MOVE SUCCESS" << endl;
}


void Bridge::predict(string &args) {
    int simiNum = stoi(args);
    mcts->search(*game, node, simiNum);

    std::vector<Point> moves;
    std::vector<float> moves_probs;
    std::tie(moves, moves_probs) = mcts->get_action_probabilities(*game);

    // 构造矩阵
    vector<tuple<int, int, float>> probs;

    for (int k = 0; k < moves.size(); k++) {
        probs.emplace_back(moves[k].x, moves[k].y, moves_probs[k]);
    }

    for (const auto &[x, y, prob]: probs) {
        cout << x << "," << y << "," << prob << " ";
    }
    cout << endl;
}

void Bridge::end_check(string &args) {
    if (game->endGameCheck()) {
        cout << "true" << endl;
    } else {
        cout << "false" << endl;
    }
}

void Bridge::winner_check(string &args) {
    auto [blackScore, whiteScore] = game->calculateScore();
    cout << game->calculateWinner() << " " << blackScore << " " << whiteScore << endl;
}

void Bridge::current_player(string &args) {
    cout << game->currentPlayer << endl;
}

void Bridge::board(string &args) {
    for (int i = 0; i < game->boardSize; i++) {
        for (int j = 0; j < game->boardSize; j++) {
            cout << game->board.board[i][j] << " ";
        }
    }
    cout << endl;
}

void Bridge::get_moves(string &args) {
    auto points = game->getMoves();
    for (const auto &point: points) {
        cout << point.x << "," << point.y << " ";
    }
    cout << endl;
}
