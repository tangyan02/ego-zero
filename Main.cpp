#define DOCTEST_CONFIG_IMPLEMENT

#include <iostream>
#include "Game.h"
#include "Model.h"
#include "test/TestAssistant.cpp"
#include "SelfPlay.h"
#include "ConfigReader.cpp"

using namespace std;

void selfPlay(int argc, char *argv[]) {
    int shard;
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

    Model model;
    model.init(modelPath);
    recordSelfPlay(
        boardSize,
        numGames,
        numSimulation,
        temperatureDefault,
        explorationFactor,
        shard,
        &model);
}

int main(int argc, char *argv[]) {
    // return startTest(argc, argv);
    selfPlay(argc, argv);
    return 0;
}
