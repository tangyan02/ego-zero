#include"../Model.h"

TEST_CASE("is_valid_move") {
    Game game(19);
    Model model;
    model.init("../test/model/model_latest.onnx");

    auto state = Model::get_state(game);
    auto result = model.evaluate_state(state);
    cout << result.first;
    for (int i = 0; i < result.second.size(); i++) {
        cout << result.second[i] << " ";
    }

}
