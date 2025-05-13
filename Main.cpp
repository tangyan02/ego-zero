#define DOCTEST_CONFIG_IMPLEMENT

#include <iostream>
#include "Game.h"
#include "Model.h"
#include "test/TestAssistant.cpp"
#include "SelfPlay.h"

using namespace std;

void selfPlay() {
    Model model;
    model.init("../test/model/model_latest.onnx");
    recordSelfPlay(19, 1, 100, 1, 3, "", &model);
}

int main(int argc, char *argv[]) {
    // return startTest(argc, argv);
    selfPlay();
    return 0;
}
