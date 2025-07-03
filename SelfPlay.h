//
// Created by 唐雁 on 2025/4/16.
//

#ifndef SELFPLAY_H
#define SELFPLAY_H

#include "Model.h"
#include <iostream>
#include "MCTS.h"
#include <random>
#include <iostream>
#include <fstream>
#include <sstream>
#include <thread>
#include <iomanip>
#include <cstdlib>
#include <ctime>
#include <atomic>


class Context
{
public:
        std::atomic<int> counter = atomic(0);
        int max;

        explicit Context(int max)
        {
                this->max = max;
        }
};

void recordSelfPlay(
        int boardSize,
        float tieMu,
        Context* context,
        int numSimulations,
        float temperatureDefault,
        float explorationFactor,
        int shard,
        string* modelPath,
        string* coreType);

#endif //SELFPLAY_H
