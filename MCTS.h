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
#include <random>
#include <numeric>

class Node {
public:
    Node *parent;
    Point move;
    int visits;
    double value_sum;
    double prior_prob;
    double ucb;
    unordered_map<Point, Node *, PointHash> children;

    Node(Node *parent = nullptr);

    bool isLeaf();

    Node *selectChild(double exploration_factor);

    void expand(Game &game, vector<Point> &actions, const vector<float> &prior_probs);

    void update(double value);

    void release();
};

class MonteCarloTree {
public:
    MonteCarloTree(Model *model, float exploration_factor = 5, bool useNoice = false);

    void simulate(Game game, int i);

    void search(Game &game, Node *node, int num_simulations);

    void backPropagate(Node *node, float value);

    pair<vector<Point>, vector<float>> get_action_probabilities();

    Point get_max_visit_move();

private:
    Node *root;
    Model *model;
    float exploration_factor;
    bool useNoice = false;

    static std::vector<double> sample_dirichlet(int size, double alpha, std::mt19937 &rng);

    static void add_dirichlet_noise(
        std::vector<float> &priors, // 原始概率
        double epsilon, // 混合系数
        double alpha, // Dirichlet参数
        std::mt19937 &rng
    );
};


#endif //MCTS_H
