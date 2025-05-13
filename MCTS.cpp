//
// Created by 唐雁 on 2025/4/9.
//

#include "MCTS.h"

using namespace std;

Node::Node(Node *parent) : parent(parent), visits(0), value_sum(0), prior_prob(0), ucb(0) {
}

bool Node::isLeaf() {
    return children.empty();
}

Node *Node::selectChild(double exploration_factor) {
    int total_visits = visits;
    vector<double> ucb_values;
    for (const auto &child: children) {
        double q = 0;
        if (child.second->visits > 0) {
            q = child.second->value_sum / child.second->visits;
        }
        double ucb_value = q + exploration_factor * child.second->prior_prob *
                           sqrt(total_visits) / (1 + child.second->visits);
        child.second->ucb = ucb_value;
    }
    Node *selected;
    double max_ucb = numeric_limits<double>::lowest();
    for (const auto &child: children) {
        if (child.second->ucb > max_ucb) {
            max_ucb = child.second->ucb;
            selected = child.second;
        }
    }
    return selected;
}

void Node::expand(Game &game, vector<Point> &moves, const vector<float> &prior_probs) {
    // 计算概率总和
    float sum_probs = 0.0;
    for (auto &prob: prior_probs) {
        sum_probs += prob;
    }

    for (auto &move: moves) {
        Node *child = new Node(this);
        int moveIndex = game.getMoveIndex(move.x, move.y);
        child->move = move;

        // 归一化处理
        if (sum_probs != 0) {
            child->prior_prob = prior_probs[moveIndex] / sum_probs;
        } else {
            child->prior_prob = prior_probs[moveIndex];
        }

        children[move] = child;
    }
}

void Node::update(double value) {
    visits++;
    value_sum += value;
}

MonteCarloTree::MonteCarloTree(Model *model, float exploration_factor)
    : model(model), root(nullptr), exploration_factor(exploration_factor) {
}

void MonteCarloTree::simulate(Game game) {
    // cout << "新的模拟" << endl;
    Node *node = root;
    while (!node->isLeaf()) {
        Node *child = node->selectChild(exploration_factor);
        Point move = child->move;
        game.makeMove(move.x, move.y);
        node = child;
    }

    float value = 0;
    if (game.endGameCheck()) {
        const int winner = game.calculateWinner();
        if (winner == game.currentPlayer) {
            value = 1;
        }
        if (winner == 3 - game.currentPlayer) {
            value = -1;
        }
        // cout << "游戏结束 赢家" << winner << endl;
    } else {
        auto state = Model::get_state(game);
        auto [value, probs] = model->evaluate_state(state);
        auto moves = game.getMoves();
        node->expand(game, moves, probs);
        // cout << "扩展完成" << endl;
    }

    backPropagate(node, -value);
}

void MonteCarloTree::search(Game &game, Node *node, int num_simulations) {
    root = node;

    for (int i = 0; i < num_simulations; i++) {
        // cout << "开始模拟，次数 " << i << endl;
        simulate(game);
    }
}

void MonteCarloTree::backPropagate(Node *node, float value) {
    while (node != nullptr) {
        node->update(value);
        node = node->parent;
        value = -value;
    }
}

pair<vector<Point>, vector<float> > MonteCarloTree::get_action_probabilities(Game game) {
    Node *node = root;
    vector<pair<Point, int> > action_visits;
    for (auto &item: node->children) {
        action_visits.emplace_back(item.first, item.second->visits);
    }

    vector<Point> moves;
    vector<int> visits;
    for (auto &item: action_visits) {
        moves.push_back(item.first);
        visits.push_back(item.second);
    }

    // 计算总和
    int sum = 0;
    for (int visit: visits) {
        sum += visit;
    }

    // 归一化为概率分布
    vector<float> action_probs;
    for (const int visit: visits) {
        float prob = static_cast<float>(visit) / static_cast<float>(sum);
        action_probs.push_back(prob);
    }

    vector<float> probs(game.boardSize * game.boardSize, 0);
    for (int i = 0; i < moves.size(); i++) {
        probs[i] = action_probs[i];
    }

    return make_pair(moves, probs);
}

vector<float> MonteCarloTree::apply_temperature(vector<float> action_probabilities, float temperature) {
    if (temperature == 1)
        return action_probabilities;
    for (float &prob: action_probabilities) {
        prob = pow(prob, 1 / temperature);
    }
    float sum = accumulate(action_probabilities.begin(), action_probabilities.end(), 0.0f);
    for (float &prob: action_probabilities) {
        prob /= sum;
    }
    return action_probabilities;
}

void Node::release() {
    for (const auto &item: this->children) {
        item.second->release();
    }
    if (this->parent != nullptr) {
        delete this;
    }
}
