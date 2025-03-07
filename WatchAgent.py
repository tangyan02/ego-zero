import time

import Network
import Utils
from Game import Game
from GameUI import GameUI
from MCTS import MCTS, Node

game = Game(board_size=9)
game.reset()
game.render()
gameUi = GameUI(board_size=9)

board_size = 9
tie_mu = 3.25

onnx_model = Network.load_onnx_model("model/model_latest.onnx")
game = Game(board_size=board_size, device=Utils.getDevice(), tie_mu=tie_mu)

players = [0, "AI", "HUMAN"]

while True:

    if players[game.current_player] == "AI":

        root = Node()
        mcts = MCTS(model=onnx_model, iterations=200, exploration_constant=3)
        mcts.root = root

        mcts.search(game)

        maxMove = -1, -1
        maxVisit = 0

        for child in mcts.root.children:
            if child.visits > maxVisit:
                maxMove = child.move
                maxVisit = child.visits

        game.make_move(maxMove[0], maxMove[1])

        game.render()
        gameUi.render(game.board, "测试")

    if players[game.current_player] == "HUMAN":
        if gameUi.next_move is not None:
            print("move")
            game.make_move(gameUi.next_move[0], gameUi.next_move[1])
            gameUi.next_move = None
        game.render()
        gameUi.render(game.board, "测试")

    if game.end_game_check():
        break

time.sleep(0)
