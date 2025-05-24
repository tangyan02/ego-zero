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
    // cout << "banned_moves" << endl;
    // for (auto banned_move: game.bannedMoves)
    //     cout << banned_move.x << " " << banned_move.y << endl;

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

    game.boardSize = 5;
    data = {
        {1, 2, 0, 2, 1},
        {0, 1, 1, 1, 1},
        {0, 0, 0, 0, 1},
        {0, 0, 0, 0, 1},
        {0, 0, 0, 0, 1}
    };
    game.board.loadData(data);
    game.currentPlayer = WHITE;
    game.refreshBannedMoves();
    CHECK(!game.isValidMove(0,2));

    data = {
        {1, 2, 0, 2, 1},
        {0, 1, 2, 1, 1},
        {0, 0, 1, 0, 1},
        {0, 0, 0, 0, 1},
        {0, 0, 0, 0, 1}
    };
    game.board.loadData(data);
    game.currentPlayer = WHITE;
    game.refreshBannedMoves();
    CHECK(!game.isValidMove(0,2));

    data = {
        {1, 0, 2, 2, 0},
        {0, 1, 2, 1, 1},
        {0, 0, 1, 0, 1},
        {0, 0, 0, 0, 1},
        {0, 0, 0, 0, 1}
    };
    game.board.loadData(data);
    game.currentPlayer = WHITE;
    game.refreshBannedMoves();
    CHECK(game.isValidMove(0,4));
    CHECK(game.isValidMove(0,1));


    game = Game(9);
    data = {
        {0,2,0,2,1,2,0,2,0},
        {1,2,1,1,1,1,1,1,1},
        {2,2,2,1,2,2,1,2,0},
        {1,2,1,2,1,2,2,2,1},
        {1,2,1,2,0,1,1,2,1},
        {1,1,1,2,1,2,2,2,2},
        {2,2,1,2,1,2,0,2,0},
        {1,0,1,2,1,2,2,1,1},
        {1,2,1,2,2,0,2,1,0}
    };
    game.board.loadData(data);
    game.refreshBannedMoves();
    game.refreshEatMoves();

    CHECK(game.isValidMove(7, 1));


//. x x o x x x x o 
//x x x x x x o x x 
//x . x o x x x x x 
//x x x o o o x x o 
//x x o o o o o o o 
//. x o o . o o . o 
//x x o o o o o o o 
//x o o . o o o o o 
//o o o o x . o o . 

    game = Game(9);
    data = {
        {0,1,1,2,1,1,1,1,2},
        {1,1,1,1,1,1,2,1,1},
        {1,0,1,2,1,1,1,1,1},
        {1,1,1,2,2,2,1,1,2},
        {1,1,2,2,2,2,2,2,2},
        {0,1,2,2,0,2,2,0,2},
        {1,1,2,2,2,2,2,2,2},
        {1,2,2,0,2,2,2,2,2},
        {2,2,2,2,1,0,2,2,0}
    };
    game.board.loadData(data);
    game.currentPlayer = 2;
    game.refreshBannedMoves();
    game.refreshEatMoves();

    auto moves = game.getMoves();
    CHECK(!game.isValidMove(2, 1));
}

TEST_CASE("make_move") {
    Game game(3);
    vector<vector<int> > data = {
        {1, 1, 2},
        {0, 1, 0},
        {2, 0, 1}
    };
    game.board.loadData(data);
    game.refreshEatMoves();


    CHECK(game.eatMoves.size()==1);


    data = {
        {1, 0, 2},
        {0, 1, 0},
        {2, 0, 1}
    };
    game.board.loadData(data);
    game.refreshEatMoves();

    game.makeMove(0, 1);
    game.makeMove(1, 0);
    game.makeMove(1, 2);
    // game.render();

    CHECK(game.board.board[0][2] == NONE_P);

    data = {
        {1, 2, 1},
        {2, 0, 2},
        {1, 2, 1}
    };
    game.board.loadData(data);
    game.currentPlayer = BLACK;
    game.refreshEatMoves();
    game.makeMove(1, 1);
    // game.render();

    CHECK(game.board.board[0][1] == NONE_P);
    CHECK(game.board.board[1][0] == NONE_P);
    CHECK(game.board.board[1][2] == NONE_P);
    CHECK(game.board.board[2][1] == NONE_P);

    game = Game(4);
    data = {
        {1, 2, 0, 1},
        {0, 1, 2, 2},
        {0, 0, 1, 2},
        {0, 0, 1, 2}
    };
    game.board.loadData(data);
    game.refreshEatMoves();

    CHECK(game.eatMoves[Point(0,2)].size()==5);
}


TEST_CASE("test_ko") {
    Game game = Game(4);
    vector<vector<int> > data = {
        {2, 0, 0, 1},
        {0, 2, 1, 0},
        {0, 2, 1, 0},
        {2, 1, 0, 1}
    };
    game.board.loadData(data);
    game.refreshEatMoves();
    game.refreshBannedMoves();
    game.currentPlayer = WHITE;

    game.makeMove(0, 2);
    game.makeMove(0, 1);
    CHECK(!game.isValidMove(0,2));

    game = Game(6);
    data = {
        {2, 0, 0, 1, 0, 0},
        {0, 2, 1, 0, 0, 2},
        {0, 0, 0, 0, 2, 0},
        {0, 0, 0, 0, 1, 2},
        {0, 2, 1, 0, 0, 1},
        {2, 1, 0, 1, 0, 0}
    };
    game.board.loadData(data);
    game.refreshEatMoves();
    game.refreshBannedMoves();
    game.currentPlayer = WHITE;

    game.makeMove(0, 2);
    game.makeMove(0, 1);
    game.makeMove(5, 2);
    game.makeMove(2, 5);
    game.makeMove(0, 2);
    game.makeMove(5, 1);
    game.makeMove(3, 5);

    CHECK(!game.isValidMove(0,1));

    game = Game(4);
    data = {
            {1, 2, 0, 2},
            {0, 1, 2, 2},
            {1, 2, 0, 2},
            {0, 1, 2, 2}
    };
    game.currentPlayer = 1;
    game.board.loadData(data);
    game.refreshEatMoves();
    game.refreshBannedMoves();
    game.recordToHistory();
    game.makeMove(2,2);
    game.render();
    CHECK(!game.isValidMove(2,1));
}

TEST_CASE("eat_move") {
    auto game = Game(4);
    vector<vector<int> > data = {
       {0, 2, 1, 0},
       {2, 2, 1, 0},
       {1, 1, 0, 0},
       {0, 0, 0, 0}
    };
    game.board.loadData(data);
    game.refreshBannedMoves();
    game.refreshEatMoves();
    CHECK(game.isValidMove(0, 0));
}
