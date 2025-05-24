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

onnx_model = Network.load_onnx_model("model/model_latest_fp16.onnx")
game = Game(board_size=board_size, device=Utils.getDevice(), tie_mu=tie_mu)

hint = [0, True, True]

ConfigReader.init()
cppPath = ConfigReader.get("cppPath")

# 启动C++子进程
proc = subprocess.Popen(
    [cppPath],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)


def callInCpp(text):
    proc.stdin.write(f"{x}\n")
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

    root = Node()
    mcts = MCTS(model=onnx_model, exploration_constant=3)
    mcts.root = root
    while True:
        if gameUi.next_move is not None:
            print("move")
            game.make_move(gameUi.next_move[0], gameUi.next_move[1])
            gameUi.next_move = None
            game.render()
            break

        probs = None
        if hint[game.current_player]:
            line = callInCpp("PREDICT  1")
            probs_str = line.split(" ")
            probs = [float(prob) for prob in probs_str]

            # mcts.search(game, 1)
            # probs = [(child.move[0], child.move[1], child.visits / mcts.root.visits) for child in
            #          mcts.root.children]

        gameUi.render(game.board,
                      f"模拟次数: {mcts.root.visits} 当前比分: {game.calculate_scores()[0]} : {game.calculate_scores()[1]}",
                      probs)
