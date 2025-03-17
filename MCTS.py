from math import sqrt

import Network
import Utils
from Game import Game


class Node:
    def __init__(self, parent=None, move=None):
        self.parent = parent  # 父节点
        self.move = move  # 从父节点到当前节点的落子动作
        self.children = []  # 子节点列表
        self.value = 0  # 该节点获胜的次数
        self.visits = 0  # 该节点被访问的次数
        self.prob = 0

    def expand(self, moves, probs):
        """
        扩展节点，选择一个未被探索的动作并创建新的子节点
        """
        for idx, move in enumerate(moves):
            new_node = Node(parent=self, move=move)
            new_node.prob = probs[idx]
            self.children.append(new_node)

    def select_child(self, exploration_constant):
        """
        选择具有最大 UCT 值的子节点
        """

        def uct(child):
            q = 0
            if child.visits > 0:
                q = child.value / child.visits
            return q + exploration_constant * child.prob * sqrt(self.visits) / (1 + child.visits)

        return max(self.children, key=uct)

    def update(self, result):
        """
        反向传播，更新从当前节点到根节点的所有节点的访问次数和获胜次数
        """
        self.visits += 1
        self.value += result
        if self.parent:
            self.parent.update(-result)

    def is_leaf(self):
        """
        判断当前节点是否为终局节点
        """
        return len(self.children) == 0


class MCTS:
    def __init__(self, model, exploration_constant=1.414):
        self.root = None
        self.model = model
        self.exploration_constant = exploration_constant

    def search(self, game, iterations):
        """
        进行 MCTS 搜索
        """
        if self.root is None:
            self.root = Node()

        for i in range(iterations):
            game_tmp = game.copy()
            self.simulate(game_tmp)
            del game_tmp

    def simulate(self, game):
        node = self.root
        while not node.is_leaf():
            result = node.select_child(self.exploration_constant)
            game.make_move(result.move[0], result.move[1])
            node = result

        value = 0
        if game.end_game_check():
            winner = game.calculate_winner()
            if winner == game.current_player:
                value = 1
            if winner == 3 - game.current_player:
                value = -1
        else:
            value, probs = Network.evaluate_state_onnx(self.model, Network.get_state(game))
            valid_moves = game.get_all_valid_moves_include_pass()
            probs_arr = []
            if len(valid_moves) > 1:
                for move in valid_moves:
                    idx = move[0] * game.board_size + move[1]
                    probs_arr.append(probs[idx])
            else:
                probs_arr.append(1)

            node.expand(valid_moves, probs_arr)

        node.update(-value)


if __name__ == "__main__":
    # 测试代码
    game = Game(board_size=9)
    game.reset()
    game.render()

    lr = 1e-3
    device = Utils.getDevice()

    model, _ = Network.get_model(device, lr)
    node = Node()
    mcts = MCTS(model=model, exploration_constant=3)
    mcts.root = node

    for i in range(1000):
        print(f"第 {i} 步")

        mcts.search(game, 800)
        best_child = max(mcts.root.children, key=lambda child: child.visits)
        sorted_children = sorted(mcts.root.children, key=lambda child: child.visits, reverse=True)
        moves = [(child.move, child.visits, child.value) for child in sorted_children]
        print("可选落子", moves)
        print("玩家 ", game.current_player, "落子 ", best_child.move,
              "访问次数 ", best_child.visits, "得分 ", best_child.value)
        game.make_move(best_child.move[0], best_child.move[1])
        if game.end_game_check():
            break

        game.render()
