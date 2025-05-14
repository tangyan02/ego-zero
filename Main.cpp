#define DOCTEST_CONFIG_IMPLEMENT

#include <iostream>
#include "Game.h"
#include "Model.h"
#include "test/TestAssistant.cpp"
#include "SelfPlay.h"

using namespace std;

void selfPlay(int argc, char *argv[]) {
    string shard;
    if (argc > 1) {
        string firstArg = argv[1];
        cout << "current shard " << firstArg << endl;
        shard = "_" + firstArg;
    }

    Model model;
    model.init("./model/model_latest.onnx");
    recordSelfPlay(
        9,
        1,
        100,
        1,
        3,
        shard,
        &model);
}

int main(int argc, char *argv[]) {
    // return startTest(argc, argv);
    selfPlay(argc, argv);
    return 0;
}
