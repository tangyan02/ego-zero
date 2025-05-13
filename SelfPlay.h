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

void recordSelfPlay(
        int boardSize,
        int numGames,
        int numSimulations,
        float temperatureDefault,
        float explorationFactor,
        const std::string& shard,
        Model* model);

#endif //SELFPLAY_H
