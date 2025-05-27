#define DOCTEST_CONFIG_IMPLEMENT

#include <iostream>
#include "Game.h"
#include "Model.h"
#include "test/TestAssistant.cpp"
#include "SelfPlay.h"
#include "ConfigReader.h"
#include "Bridge.h"

using namespace std;

void selfPlay() {
    // Parse parameters with defaults if not found
    int boardSize = stoi(ConfigReader::get("boardSize"));
    float tieMu = stof(ConfigReader::get("tieMu"));
    int numGames = stoi(ConfigReader::get("numGames"));
    int numSimulation = stoi(ConfigReader::get("numSimulation"));
    float temperatureDefault = stof(ConfigReader::get("temperatureDefault"));
    float explorationFactor = stof(ConfigReader::get("explorationFactor"));
    string modelPath = ConfigReader::get("modelPath");
    int numProcesses = stoi(ConfigReader::get("numProcesses"));
    string coreType = ConfigReader::get("coreType");

    std::vector<std::thread> threads;
    // 启动多个线程
    for (int i = 0; i < numProcesses; ++i) {
        threads.emplace_back(recordSelfPlay,
                             boardSize,
                             tieMu,
                             numGames,
                             numSimulation,
                             temperatureDefault,
                             explorationFactor,
                             i,
                             &modelPath,
                             &coreType);
    }

    // 等待所有线程完成
    for (auto &t: threads) {
        if (t.joinable()) {
            t.join();
        }
    }
}

int main(int argc, char *argv[]) {
    auto mode = ConfigReader::get("mode");
    if (mode == "train") {
        selfPlay();
        return 0;
    }
    if (mode == "predict") {
        Bridge bridge;
        bridge.startGame();
        return 0;
    }
    return startTest(argc, argv);
}
