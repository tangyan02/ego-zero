import subprocess

import numpy as np

from GameUI import GameUI
from train.ConfigReader import ConfigReader

gameUi = GameUI(board_size=9)

board_size = 9
tie_mu = 3.25

hint = [0, True, True]

ConfigReader.init()
cppPath = ConfigReader.get("cppPath")
visitCount = 0

# 启动C++子进程
proc = subprocess.Popen(
    [cppPath],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)


def callInCpp(text):
    proc.stdin.write(f"{text}\n")
    proc.stdin.flush()  # 确保数据发送
    return proc.stdout.readline().strip()


def handle_predict():
    line = callInCpp("PREDICT 1")
    probs_arr = line.strip().split(" ")
    probs = []
    for str in probs_arr:
        items = str.split(",")
        x = int(items[0])
        y = int(items[1])
        prob = float(items[2])
        probs.append((x, y, prob))
    return probs


def handle_move(x, y):
    print(f"move {x},{y}")
    callInCpp(f"MOVE {x},{y}")


def handle_end_check():
    line = callInCpp(f"END_CHECK")
    return line.strip() == "true"


def handle_get_moves():
    line = callInCpp(f"GET_MOVES")
    arr = line.strip().split(" ")
    moves = []
    for str in arr:
        items = str.split(",")
        x = int(items[0])
        y = int(items[1])
        moves.append((x, y))
    return moves


def handle_current_player():
    line = callInCpp("CURRENT_PLAYER")
    return int(line.strip())


def handle_board():
    line = callInCpp("BOARD")
    arr = line.strip().split(" ")
    k = 0

    board = np.zeros((board_size, board_size), dtype=np.uint8)
    for i in range(board_size):
        for j in range(board_size):
            board[i][j] = int(arr[k])
            k += 1

    return board


def handle_winner():
    line = callInCpp("WINNER_CHECK")
    arr = line.strip().split(" ")
    winner = int(arr[0])
    black = float(arr[1])
    white = float(arr[2])
    return winner, black, white


board = np.zeros((board_size, board_size), dtype=np.uint8)
while True:

    if handle_end_check():
        winner, black, white = handle_winner()
        gameUi.render(board, f"胜利玩家 {winner} 得分对比 {black} : {white}")
        continue

    moves = handle_get_moves()
    if len(moves) == 1 and moves[0][0] == -1:
        handle_move(moves[0][0], moves[0][1])
        continue

    while True:
        if gameUi.rollback:


        if gameUi.next_move is not None:
            if board[gameUi.next_move[0]][gameUi.next_move[1]] == 0:
                handle_move(gameUi.next_move[0], gameUi.next_move[1])
            gameUi.next_move = None
            visitCount = 0
            break

        probs = None
        if hint[handle_current_player()]:
            visitCount += 1
            probs = handle_predict()

        board = handle_board()
        gameUi.render(board,
                      f"模拟次数: {visitCount}",
                      probs)
