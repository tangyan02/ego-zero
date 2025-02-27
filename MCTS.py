import random
from math import sqrt, log

import Network
import Utils
from Game import Game
from tqdm import tqdm

from Network import get_network


class Node:
    def __init__(self, parent=None, move=None, game=None):
        self.parent = parent  # 父节点
        self.move = move  # 从父节点到当前节点的落子动作
        self.game = game  # 当前的游戏状态
        self.children = []  # 子节点列表
        self.wins = 0  # 该节点获胜的次数
        self.visits = 0  # 该节点被访问的次数

    def expand(self):
        """
        扩展节点，选择一个未被探索的动作并创建新的子节点
        """
        valid_moves = self.game.get_all_valid_moves_include_pass()
        untried_moves = [move for move in valid_moves if move not in [child.move for child in self.children]]
        for move in untried_moves:
            new_game = self.game.copy()  # 假设 Game 类有 copy 方法来复制游戏状态
            new_game.make_move(*move)
            new_node = Node(parent=self, move=move, game=new_game)
            self.children.append(new_node)

    def select_child(self, exploration_constant=1.414):
        """
        选择具有最大 UCT 值的子节点
        """

        def uct(child):
            if child.visits == 0:
                return float('inf')
            return (child.wins / child.visits) + exploration_constant * sqrt(log(self.visits) / child.visits)

        return max(self.children, key=uct)

    def update(self, result):
        """
        反向传播，更新从当前节点到根节点的所有节点的访问次数和获胜次数
        """
        self.visits += 1
        self.wins += result
        if self.parent:
            self.parent.update(1 - result)

    def is_leaf(self):
        """
        判断当前节点是否为终局节点
        """
        return len(self.children) == 0


class MCTS:
    def __init__(self, model, iterations=1000, exploration_constant=1.414):
        self.root = None
        self.iterations = iterations
        self.model = model
        self.exploration_constant = exploration_constant

    def search(self, game):
        """
        进行 MCTS 搜索
        """
        self.root = Node(game=game)

        bar = tqdm(total=self.iterations)
        for i in range(self.iterations):
            # print(f"第 {i} 次模拟")
            bar.update(1)
            self.simulate(node.game.copy())

        bar.close()

    def random_simulate(self, game):
        start_player = game.current_player
        while True:
            moves = game.get_all_valid_moves_include_pass()
            # print("moves", moves)
            move = random.choice(moves)
            # print('move ', move)
            game.make_move(move[0], move[1])
            # game.render()

            if game.end_game_check():
                result = game.calculate_winner()
                if result == 0:
                    return 0
                if result == start_player:
                    return 1
                if result == 3 - start_player:
                    return -1

    def simulate(self, game):
        if game.end_game_check():
            return

        node = self.root
        while not node.is_leaf():
            result = node.select_child()
            game.make_move(result.move[0], result.move[1])
            node = result

        if game.end_game_check():
            value = -1
        else:
            value = model(game.get_state())[0].item()
            node.expand()

        node.update(value)


if __name__ == "__main__":
    # 测试代码
    game = Game(board_size=9)
    game.reset()
    game.render()

    lr = 1e-3
    device = Utils.getDevice()

    model, _ = Network.get_network(device, lr)
    node = Node(game=game)
    mcts = MCTS(iterations=1000, model=model)
    mcts.root = node

    for i in range(1000):
        print(f"第 {i} 步")

        mcts.search(game)
        best_child = max(mcts.root.children, key=lambda child: child.visits)
        sorted_children = sorted(mcts.root.children, key=lambda child: child.visits, reverse=True)
        moves = [(child.move, child.visits) for child in sorted_children]
        print("可选落子", moves)
        print("玩家 ", game.current_player, "落子 ", best_child.move, " 访问次数 ", best_child.visits)
        game.make_move(best_child.move[0], best_child.move[1])
        if game.end_game_check():
            break

        game.render()
