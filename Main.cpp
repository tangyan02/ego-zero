#define DOCTEST_CONFIG_IMPLEMENT

#include <iostream>
#include "Game.h"
#include "Model.h"
#include "test/TestAssistant.cpp"
#include "SelfPlay.h"
#include "ConfigReader.cpp"

using namespace std;

void selfPlay(int argc, char *argv[]) {
    int shard = 0;
    if (argc > 1) {
        string firstArg = argv[1];
        cout << "current shard " << firstArg << endl;
        shard = stoi(firstArg);
    }

    // Read configuration
    auto config = readConfigFile("application.conf");

    // Parse parameters with defaults if not found
    int boardSize = config.count("boardSize") ? stoi(config["boardSize"]) : 9;
    int numGames = config.count("numGames") ? stoi(config["numGames"]) : 1;
    int numSimulation = config.count("numSimulation") ? stoi(config["numSimulation"]) : 100;
    float temperatureDefault = config.count("temperatureDefault") ? stof(config["temperatureDefault"]) : 1;
    float explorationFactor = config.count("explorationFactor") ? stof(config["explorationFactor"]) : 3;
    string modelPath = config.count("modelPath") ? config["modelPath"] : "./model/model_latest.onnx";
    int numProcesses = config.count("numProcesses") ? stoi(config["numProcesses"]) : 1;
    string coreType = config.count("coreType") ? config["coreType"] : "cpu";

    Model model;
    model.init(modelPath, coreType);

    std::vector<std::thread> threads;
    // 启动多个线程
    for (int i = 0; i < numProcesses; ++i) {
        threads.emplace_back(recordSelfPlay, boardSize,
            numGames,
            numSimulation,
            temperatureDefault,
            explorationFactor,
            i,
            &model);
    }

    // 等待所有线程完成
    for (auto& t : threads) {
        if (t.joinable()) {
            t.join();
        }
    }

    //recordSelfPlay(
    //    boardSize,
    //    numGames,
    //    numSimulation,
    //    temperatureDefault,
    //    explorationFactor,
    //    shard,
    //    &model);
}

int main(int argc, char *argv[]) {
     return startTest(argc, argv);
    selfPlay(argc, argv);
    return 0;
}
