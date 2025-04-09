//
// Created by 唐雁 on 2025/4/9.
//

#ifndef MCTS_H
#define MCTS_H


#include <utility>
#include <unordered_map>
#include <vector>
#include <cmath>
#include <limits>
#include "Game.h"
#include "Model.h"

class Node {
public:
    Node *parent;
    int visits;
    double value_sum;
    double prior_prob;
    double ucb{};
    std::unordered_map<Point, Node *, PointHash> children;

    Node(Node *parent = nullptr);

    bool isLeaf();

    pair<Point, Node *> selectChild(double exploration_factor);

    void expand(Game &game, std::vector<Point> &actions, const std::vector<float> &prior_probs);

    void update(double value);

    void release();
};

class MonteCarloTree {
public:
    MonteCarloTree(Model *model, float exploration_factor = 5);

    void simulate(Game game);

    void search(Game &game, Node *node, int num_simulations);

    void backpropagate(Node *node, float value);

    std::pair<std::vector<int>, std::vector<float>> get_action_probabilities(Game game);

    std::vector<float> apply_temperature(std::vector<float> action_probabilities, float temperature);


private:
    Node *root;
    Model *model;
    float exploration_factor;
};


#endif //MCTS_H
