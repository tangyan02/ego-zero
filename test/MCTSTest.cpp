#include "../MCTS.h"

TEST_CASE("search") {
    Game game(19);
    Model model;
    model.init("../test/model/model_latest.onnx", "cpu");

    MonteCarloTree mcts = MonteCarloTree(&model);
    Node node = Node();
    mcts.search(game, &node, 10);
    CHECK(node.children.size() == 19*19);
}
