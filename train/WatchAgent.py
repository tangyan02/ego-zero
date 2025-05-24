import subprocess

import Network
import Utils
from Game import Game
from GameUI import GameUI
from MCTS import MCTS, Node
from train.ConfigReader import ConfigReader

game = Game(board_size=9)
game.render()
gameUi = GameUI(board_size=9)

board_size = 9
tie_mu = 3.25

game = Game(board_size=board_size, device=Utils.getDevice(), tie_mu=tie_mu)

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


while True:

    if game.end_game_check():
        gameUi.render(game.board,
                      f"胜利玩家 {game.calculate_winner()} 得分对比 {game.calculate_scores()[0]} : {game.calculate_scores()[1]}")
        continue

    if len(game.get_all_valid_moves()) == 0:
        game.pass_move()
        continue

    while True:
        if gameUi.next_move is not None:
            print("move")
            line = callInCpp(f"MOVE {gameUi.next_move[0]},{gameUi.next_move[1]}")
            game.make_move(gameUi.next_move[0], gameUi.next_move[1])
            gameUi.next_move = None
            visitCount = 0
            game.render()
            break

        probs = None
        if hint[game.current_player]:
            line = callInCpp("PREDICT 1")
            visitCount += 1
            probs_arr = line.strip().split(" ")
            probs = []
            for str in probs_arr:
                items = str.split(",")
                x = int(items[0])
                y = int(items[1])
                prob = float(items[2])
                probs.append((x, y, prob))

            # mcts.search(game, 1)
            # probs = [(child.move[0], child.move[1], child.visits / mcts.root.visits) for child in
            #          mcts.root.children]

        gameUi.render(game.board,
                      f"模拟次数: {visitCount}",
                      probs)
