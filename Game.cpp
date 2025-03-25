#include "Game.h"
#include <stack>

Point::Point() {
    this->x = -1;
    this->y = -1;
}

Point::Point(int x, int y) {
    this->x = x;
    this->y = y;
}

bool Point::isNull() {
    return x == -1 && y == -1;
}

bool Board::eq(Board &board, int size) {
    for (int i = 0; i < size; i++) {
        for (int j = 0; j < size; j++) {
            if (this->board[i][j] != board.board[i][j]) {
                return false;
            }
        }
    }
    return true;
}

void Board::loadData(vector<vector<int> > data) {
    for (int i = 0; i < data.size(); i++) {
        for (int j = 0; j < data[i].size(); j++) {
            this->board[i][j] = data[i][j];
        }
    }
}

pair<int, int> Game::countAround(int x, int y) {
    //交叉
    int cross_not_self_count = 0;
    for (int i = 0; i < 4; i++) {
        int px = x + crossDx[i];
        int py = y + crossDy[i];
        if (px >= 0 && px < boardSize && py >= 0 && py < boardSize) {
            if (board.board[px][py] != currentPlayer)
                cross_not_self_count++;
        }
    }

    //对角
    int corner_not_self_count = 0;
    for (int i = 0; i < 4; i++) {
        int px = x + cornerDx[i];
        int py = y + cornerDy[i];
        if (px >= 0 && px < boardSize && py >= 0 && py < boardSize) {
            if (board.board[px][py] != currentPlayer)
                corner_not_self_count++;
        }
    }

    return make_pair(corner_not_self_count, cross_not_self_count);
}

tuple<int, int, int> Game::countCross(int x, int y) {
    int blank_count = 0;
    int self_count = 0;
    int opp_count = 0;

    for (int i = 0; i < 4; i++) {
        int px = x + crossDx[i];
        int py = y + crossDy[i];
        if (px >= 0 && px < boardSize && py >= 0 && py < boardSize) {
            if (board.board[px][py] == NONE_P)
                blank_count++;
            if (board.board[px][py] == currentPlayer)
                self_count++;
            if (board.board[px][py] == 3 - currentPlayer)
                opp_count++;
        }
    }
    return make_tuple(blank_count, self_count, opp_count);
}

bool Game::isCrossEye(int x, int y, int player) {
    if (player == 0) {
        player = currentPlayer;
    }
    for (int i = 0; i < 4; i++) {
        int px = x + crossDx[i];
        int py = y + crossDy[i];
        if (px >= 0 && px < boardSize && py >= 0 && py < boardSize) {
            if (board.board[px][py] != player)
                return false;
        }
    }
    return true;
}

bool Game::isOnSide(int x, int y) {
    return x == 0 || y == 0 || x == boardSize - 1 || y == boardSize - 1;
}

bool Game::isOnBoard(int x, int y) {
    return x >= 0 && y >= 0 && x < boardSize && y < boardSize;
}

bool Game::isEyePair(int x, int y) {
    int self_corner_count_limit = 2;
    if (isOnSide(x, y)) {
        self_corner_count_limit = 1;
    }
    auto aroundPair = countAround(x, y);
    int corner_not_self_count = aroundPair.first;
    int cross_not_self_count = aroundPair.second;
    if (cross_not_self_count > 0 or corner_not_self_count > self_corner_count_limit) {
        return false;
    }

    //对角
    for (int i = 0; i < 4; i++) {
        int px = x + cornerDx[i];
        int py = y + cornerDy[i];
        int p_self_corner_count_limit = 3;
        if (isOnSide(x, y) and isOnSide(px, py)) {
            p_self_corner_count_limit = 2;
        }
        if (isOnBoard(px, py) and isCrossEye(px, py)) {
            auto p_aroundPair = countAround(px, py);
            int p_corner_not_self_count = p_aroundPair.first;
            int p_cross_not_self_count = p_aroundPair.second;
            if (p_cross_not_self_count == 0 && p_corner_not_self_count + corner_not_self_count <=
                p_self_corner_count_limit) {
                return true;
            }
        }
    }
    return false;
}

bool Game::isEye(int x, int y) {
    auto aroundPair = countAround(x, y);
    int corner_not_self_count = aroundPair.first;
    int cross_not_self_count = aroundPair.second;
    int corner_limit = 1;
    if (isOnSide(x, y)) {
        corner_limit = 0;
    }
    if (cross_not_self_count == 0 && corner_not_self_count <= corner_limit) {
        return true;
    }
    if (isEyePair(x, y)) {
        return true;
    }
    return false;
}

bool Game::isValidMove(int x, int y) {
    if (!isOnBoard(x, y)) {
        return false;
    }

    if (board.board[x][y] != NONE_P) {
        return false;
    }

    //判断禁止点
    for (auto banned_move: bannedMoves) {
        if (x == banned_move.x and y == banned_move.y) {
            return false;
        }
    }

    //临时落子
    auto tmpBoard = Board(board);
    tmpBoard.board[x][y] = currentPlayer;

    //检查并移除对手死子
    for (auto eat_move: eatMoves) {
        Point eatPoint = eat_move.first;
        if (eatPoint.x == x && eatPoint.y == y) {
            auto eatenMoves = eat_move.second;
            for (auto eaten_move: eatenMoves) {
                tmpBoard.board[eaten_move.x][eaten_move.y] = 0;
            }
        }
        //检查循环劫
        for (int i = 0; i < historyMoves.size(); i++) {
            if (x == historyMoves[i].x && y == historyMoves[i].y) {
                if (tmpBoard.eq(history[i], boardSize)) {
                    return false;
                }
            }
        }
    }

    if (isEye(x, y)) {
        return false;
    }

    return true;
}

Game::Game(int boardSize, float tieMu) {
    currentPlayer = 1;
    this->tieMu = tieMu;
    this->boardSize = boardSize;
    for (int i = 0; i < boardSize; i++)
        for (int j = 0; j < boardSize; j++)
            board.board[i][j] = 0;
}

void Game::render() {
    for (int i = 0; i < boardSize; i++) {
        for (int j = 0; j < boardSize; j++) {
            if (board.board[i][j] == BLACK)
                cout << "x ";
            if (board.board[i][j] == WHITE)
                cout << "o ";
            if (board.board[i][j] == NONE_P)
                cout << ". ";
        }
        cout << endl;
    }
}

void Game::passMove() {
    pass_count += 1;
    currentPlayer = 3 - currentPlayer;
}

bool Game::endGameCheck() {
    return pass_count >= 2;
}

pair<int, int> Game::calculateScore() {
    int black_score = 0;
    int white_score = 0;

    for (int i = 0; i < boardSize; i++) {
        for (int j = 0; j < boardSize; j++) {
            if (board.board[i][j] == BLACK)
                black_score += 1;
            if (board.board[i][j] == WHITE)
                white_score += 1;
            if (board.board[i][j] == NONE_P) {
                if (isCrossEye(i, j, BLACK))
                    black_score += 1;
                if (isCrossEye(i, j, WHITE))
                    white_score += 1;
            }
        }
    }

    black_score -= tieMu;
    white_score += tieMu;

    return make_pair(black_score, white_score);
}

void Game::refreshBannedMoves() {
    bannedMoves.clear();
    bool visited[MAX_BOARD_SIZE][MAX_BOARD_SIZE] = {false};

    for (int i = 0; i < boardSize; i++) {
        for (int j = 0; j < boardSize; j++) {
            if (board.board[i][j] == NONE_P) {
                auto tuple_around = countCross(i, j);
                int blank_count = get<0>(tuple_around);
                // 判断条件：周围没有气，且有对方棋子
                if (blank_count == 0) {
                    cout << i << " " << j << endl;
                    board.board[i][j] = currentPlayer;
                    // 尝试填充，然后判断有没有气
                    stack<pair<int, int> > stk;
                    stk.emplace(i, j);
                    int qiCount = 0;

                    bool near_first_visit = true;
                    for (int k = 0; k < 4; k++) {
                        int px = i + crossDx[k];
                        int py = j + crossDy[k];
                        if (isOnSide(px, py)) {
                            if (visited[px][py])
                                near_first_visit = false;
                        }
                    }

                    cout << "near_first_visit " << near_first_visit << endl;
                    while (!stk.empty()) {
                        pair<int, int> top = stk.top();
                        stk.pop();
                        int cx = top.first;
                        int cy = top.second;
                        for (int k = 0; k < 4; k++) {
                            int px = cx + crossDx[k];
                            int py = cy + crossDy[k];
                            if (isOnSide(px, py)) {
                                if (board.board[px][py] == NONE_P) {
                                    qiCount += 1;
                                } else if (board.board[px][py] == currentPlayer && !visited[px][py]) {
                                    visited[px][py] = true;
                                    stk.emplace(px, py);
                                }
                            }
                        }
                    }
                    cout << "qiCount " << qiCount << endl;
                    if (qiCount == 0 && near_first_visit) {
                        auto p = Point(i, j);
                        bannedMoves.emplace_back(p);
                    }
                    board.board[i][j] = NONE_P;
                }
            }
        }
    }
}
