#ifndef MODEL_H
#define MODEL_H

#include <vector>
#include <onnxruntime_cxx_api.h>
#include <iostream>
#include <numeric>
#include <codecvt>

#include "Game.h"

using namespace std;

class Model {
public:
    Model();

    void init(string model_path);

    pair<float, vector<float> > evaluate_state(vector<vector<vector<float> > > &state);

    static vector<vector<vector<float> > > get_state(Game &game);

private:
    Ort::Env *env;
    Ort::SessionOptions *sessionOptions;
    Ort::Session *session;
    Ort::MemoryInfo memoryInfo;
};


#endif //MODEL_H
