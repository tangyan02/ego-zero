#ifndef GAME_H
#define GAME_H

#include <iostream>
#include <vector>
#include <unordered_set>
#include <algorithm>

const int MAX_BOARD_SIZE = 19;

#define NONE_P 0
#define BLACK 1
#define WHITE 2

using namespace std;

class Point {
public:
    int x;
    int y;

    Point();

    Point(int x, int y);

    bool isNull();
};


class Board {
public:
    int board[MAX_BOARD_SIZE][MAX_BOARD_SIZE]{};

    bool eq(Board &board, int size);

    void loadData(vector<vector<int> > data);
};

class Game {
    vector<Point> historyMoves;
    vector<Board> history;
    vector<pair<Point, vector<Point> > > eatMoves;


    int pass_count;
    int history_max_size;


    int crossDx[4] = {1, 0, -1, 0};
    int crossDy[4] = {0, 1, 0, -1};

    int cornerDx[4] = {-1, -1, 1, 1};
    int cornerDy[4] = {1, -1, 1, -1};

    pair<int, int> countAround(int x, int y);

    tuple<int, int, int> countCross(int x, int y);

public:
    Board board;
    int boardSize;
    int tieMu;
    int currentPlayer;
    vector<Point> bannedMoves;

    bool isCrossEye(int x, int y, int player = 0);

    bool isOnSide(int x, int y);

    bool isOnBoard(int x, int y);

    bool isEyePair(int x, int y);

    bool isEye(int x, int y);

    bool isValidMove(int x, int y);

    Game(int boardSize, float tieMu = 3.5);

    void render();

    void passMove();

    bool endGameCheck();

    pair<int, int> calculateScore();

    void refreshBannedMoves();

    //待测试
    void refreshEatMoves();

    //待补充
    void makeMove(int x, int y);

};


#endif //GAME_H
