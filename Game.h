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
    bool eq(Board& board, int size);
};

class Game {
    Board board;
    vector<Point> historyMoves;
    vector<Point> bannedMoves;
    vector<Board> history;
    vector<pair<Point, vector<Point>> > eatMoves;

    int boardSize;
    int currentPlayer;

    int pass_count;
    int history_max_size;

    int tieMu;

    int crossDx[4] = {1, 0, -1, 0};
    int crossDy[4] = {0, 1, 0, -1};

    int cornerDx[4] = {-1, -1, 1, 1};
    int cornerDy[4] = {1, -1, 1, -1};

    pair<int, int> countAround(int x, int y);

    tuple<int, int, int> countCross(int x, int y);

    bool isCrossEye(int x, int y);

    bool isOnSide(int x, int y);

    bool isOnBoard(int x, int y);

    bool isEyePair(int x, int y);

    bool isEye(int x, int y);

    bool isValidMove(int x, int y);

public:
    Game(int boardSize, float tieMu);

    void render();
};


#endif //GAME_H
