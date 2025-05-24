//
// Created by 唐雁 on 2025/5/24.
//

#ifndef EGO_ZERO_BRIDGE_H
#define EGO_ZERO_BRIDGE_H

#include "ConfigReader.h"
#include "game.h"
#include "MCTS.h"
#include <iostream>
#include <string>
#include <sstream>
#include <stdexcept>


class Bridge {
public:
    void startGame();
    Bridge();

private:
    Game *game;
    Model *model;
    MonteCarloTree *mcts;
    Node *node;

    void parse_coordinates(const string &args, int &x, int &y);

    void move(int x, int y);

    vector<tuple<int, int, float>> predict(int simiNum);
};


#endif //EGO_ZERO_BRIDGE_H
