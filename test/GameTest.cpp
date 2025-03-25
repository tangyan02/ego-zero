#include "../Game.h"

TEST_CASE("is_valid_move") {
    //边界外落子，无效
    Game game(4);

    CHECK(!game.isValidMove(-1,0));
    CHECK(!game.isValidMove(4,0));
    CHECK(!game.isValidMove(0,-1));
    CHECK(!game.isValidMove(0,4));

    // # 已有棋子的位置落子，应无效
    game.board.board[0][0] = BLACK;
    CHECK(!game.isValidMove(0,0));
}

TEST_CASE("is_eye_pair") {
    Game game(6);
    vector<vector<int> > data = {
        {1, 1, 1, 0, 0, 0},
        {1, 0, 1, 0, 0, 0},
        {1, 1, 0, 1, 0, 0},
        {0, 1, 1, 1, 0, 0},
        {0, 0, 0, 0, 0, 1},
        {0, 0, 0, 0, 0, 1}
    };
    game.board.loadData(data);
    CHECK(game.isEyePair(1,1));
    CHECK(game.isEyePair(2,2));

    data = {
        {1, 1, 1, 0, 0, 0},
        {1, 0, 1, 0, 0, 0},
        {1, 1, 0, 1, 0, 0},
        {0, 1, 1, 1, 1, 1},
        {0, 0, 0, 0, 1, 0},
        {0, 0, 0, 1, 0, 1}
    };
    game.board.loadData(data);
    CHECK(!game.isEyePair(4,5));
    CHECK(!game.isEyePair(5,4));

    data = {
        {0, 1, 0, 1, 0, 1},
        {1, 0, 1, 1, 1, 0},
        {1, 1, 1, 0, 0, 0},
        {0, 0, 1, 1, 1, 1},
        {0, 0, 0, 1, 0, 1},
        {0, 0, 0, 1, 1, 1}
    };
    game.board.loadData(data);
    CHECK(game.isEyePair(0,0));
    CHECK(game.isEyePair(1,1));
}

TEST_CASE("is_eye") {
    Game game(6);
    vector<vector<int> > data = {
        {1, 1, 0, 0, 0, 0},
        {1, 0, 1, 0, 0, 0},
        {1, 1, 1, 0, 0, 0},
        {0, 0, 1, 1, 1, 0},
        {0, 0, 0, 1, 0, 1},
        {0, 0, 0, 1, 1, 1}
    };
    game.board.loadData(data);
    CHECK(game.isEye(1,1));
    CHECK(game.isEye(4,4));

    data = {
        {0, 1, 0, 1, 0, 0},
        {1, 1, 1, 1, 0, 0},
        {1, 1, 1, 0, 0, 0},
        {0, 0, 1, 1, 1, 1},
        {0, 0, 0, 1, 0, 1},
        {0, 0, 0, 1, 1, 1}
    };
    game.board.loadData(data);
    CHECK(game.isEye(0,0));
    CHECK(game.isEye(0,2));
    CHECK(game.isEye(4,4));

    data = {
        {0, 1, 0, 1, 0, 1},
        {1, 0, 0, 1, 1, 0},
        {1, 1, 1, 0, 0, 0},
        {0, 0, 1, 1, 1, 1},
        {0, 0, 0, 1, 0, 1},
        {0, 0, 0, 1, 1, 1}
    };
    game.board.loadData(data);
    CHECK(!game.isEye(0,0));
    CHECK(!game.isEye(0,4));
}

TEST_CASE("calculate_score") {
    Game game(3);
    vector<vector<int> > data = {
        {1, 0, 2},
        {0, 1, 0},
        {2, 0, 1},
    };
    game.board.loadData(data);
    auto pair = game.calculateScore();
    int blackScore = pair.first;
    int whiteScore = pair.second;

    int expected_black_score = 0;
    int expected_white_score = 0;
    for (int i = 0; i < game.boardSize; i++) {
        for (int j = 0; j < game.boardSize; j++) {
            if (game.board.board[i][j] == BLACK)
                expected_black_score++;
            if (game.board.board[i][j] == WHITE)
                expected_white_score++;
        }
    }
    expected_black_score -= game.tieMu;
    expected_white_score += game.tieMu;
    CHECK(expected_black_score == blackScore);
    CHECK(expected_white_score == whiteScore);
}

TEST_CASE("banned_moves") {
    Game game(4);
    vector<vector<int> > data = {
        {1, 2, 0, 1},
        {0, 1, 1, 0},
        {0, 0, 0, 0},
        {0, 0, 0, 0}
    };
    game.board.loadData(data);
    game.currentPlayer = WHITE;
    game.refreshBannedMoves();
    cout << "banned_moves" << endl;
    for (auto banned_move: game.bannedMoves)
        cout << banned_move.x << " " << banned_move.y << endl;

    CHECK(!game.isValidMove(0,2));

    data = {
        {1, 2, 0, 1},
        {0, 1, 0, 0},
        {0, 0, 0, 0},
        {0, 0, 0, 0}
    };
    game.board.loadData(data);
    game.currentPlayer = WHITE;
    game.refreshBannedMoves();
    CHECK(game.isValidMove(0,2));

    //
    // game = Game(board_size=5)
    // game.current_player = 2
    // data = """
    //   x o . o x
    //   . x x x x
    //   . . . . x
    //   . . . . x
    //   """
    // game.parse(data)
    // assert not game.is_valid_move(0, 2)
    //
    // game = Game(board_size=5)
    // game.current_player = 2
    // data = """
    //   x o . o x
    //   . x o x x
    //   . . x . x
    //   . . . . x
    //   """
    // game.parse(data)
    // assert not game.is_valid_move(0, 2)
    //
    // game = Game(board_size=5)
    // game.current_player = 2
    // data = """
    //      x . o o .
    //      . x x x x
    //      . . x . x
    //      . . . . x
    //      """
    // game.parse(data)
    // assert game.is_valid_move(0, 4)
    // assert game.is_valid_move(0, 1)
}
