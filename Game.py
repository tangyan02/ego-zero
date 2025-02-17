import numpy as np
import random


class Point:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y


class Game:
    def __init__(self, board_size=19):
        self.board_size = board_size
        self.board = np.zeros((board_size, board_size), dtype=int)
        self.current_player = 1
        self.history = []
        self.ko_point = None  # 用于记录劫的位置
        self.pass_count = 0  # 记录双方连续 passes 的次数，用于终局判定
        self.ko_history = []  # 记录劫的历史状态，用于处理单劫循环

    def reset(self):
        self.board = np.zeros((self.board_size, self.board_size), dtype=int)
        self.current_player = 1
        self.history = []
        self.ko_point = None
        self.pass_count = 0
        self.ko_history = []
        return self.board

    def is_valid_move(self, x, y):
        if x < 0 or x >= self.board_size or y < 0 or y >= self.board_size:
            return False
        if self.board[x, y] != 0:
            return False

        # 临时落子
        temp_board = self.board.copy()
        temp_board[x, y] = self.current_player

        # 检查并移除对手的死子
        opponent = 3 - self.current_player
        dead_stones = []
        for nx, ny in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
            if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                if temp_board[nx, ny] == opponent:
                    group, has_liberty = self.get_group(nx, ny, temp_board)
                    if not has_liberty:
                        dead_stones.extend(group)

        for dx, dy in dead_stones:
            temp_board[dx, dy] = 0

        # 检查落子后己方棋块是否有气
        group, has_liberty = self.get_group(x, y, temp_board)
        if not has_liberty:
            return False

        # 检查是否违反打劫规则
        if len(self.history) > 0 and self.ko_point == (x, y) and np.array_equal(temp_board, self.history[-1]):
            return False

        # 检查单劫循环
        if (x, y) in self.ko_history and np.array_equal(temp_board, self.history[-1]):
            return False

        # 检查是否为己方的眼位
        if self.is_eye(x, y, self.current_player, temp_board):
            return False

        return True

    def place_stone(self, x, y):
        if not self.is_valid_move(x, y):
            return False

        self.board[x, y] = self.current_player
        self.history.append(self.board.copy())

        # 检查并移除对手的死子
        opponent = 3 - self.current_player
        dead_stones = []
        for nx, ny in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
            if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                if self.board[nx, ny] == opponent:
                    group, has_liberty = self.get_group(nx, ny)
                    if not has_liberty:
                        dead_stones.extend(group)

        for dx, dy in dead_stones:
            self.board[dx, dy] = 0

        # 更新劫的位置
        if len(dead_stones) == 1:
            self.ko_point = dead_stones[0]
            self.ko_history.append(self.ko_point)
        else:
            self.ko_point = None

        self.current_player = opponent
        self.pass_count = 0  # 落子后重置 pass 计数
        return True

    def get_all_valid_moves(self):
        """
        获取所有可落子的点
        """
        valid_moves = []
        for x in range(self.board_size):
            for y in range(self.board_size):
                if self.is_valid_move(x, y):
                    valid_moves.append((x, y))
        return valid_moves

    def place_random_stone(self):
        """
        随机选择一个可落子的点落子
        """
        print(f"当前玩家 {game.current_player}")
        valid_moves = self.get_all_valid_moves()
        if not valid_moves:
            return False
        x, y = random.choice(valid_moves)
        return self.place_stone(x, y)

    def pass_move(self):
        """
        玩家选择 pass
        """
        self.pass_count += 1
        self.current_player = 3 - self.current_player
        print("pass count:", self.pass_count)
        if self.pass_count >= 2:
            return self.end_game()
        return -1

    def end_game(self):
        """
        处理终局情况，计算双方得分并判断胜负
        """
        black_score, white_score = self.calculate_scores()
        if black_score > white_score:
            return 1
        elif white_score > black_score:
            return 2
        else:
            return 0

    def calculate_scores(self):
        """
        计算双方的得分，只计算棋子数，不计算领地
        """
        black_score = np.sum(self.board == 1)
        white_score = np.sum(self.board == 2)

        # 添加调试信息
        print(f"黑方棋子数: {black_score}")
        print(f"白方棋子数: {white_score}")

        return black_score, white_score

    def get_group(self, x, y, board=None):
        if board is None:
            board = self.board
        player = board[x, y]
        group = []
        has_liberty = False
        visited = np.zeros((self.board_size, self.board_size), dtype=bool)
        stack = [(x, y)]
        visited[x, y] = True

        while stack:
            cx, cy = stack.pop()
            group.append((cx, cy))
            for nx, ny in [(cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)]:
                if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                    if board[nx, ny] == 0:
                        has_liberty = True
                    elif board[nx, ny] == player and not visited[nx, ny]:
                        visited[nx, ny] = True
                        stack.append((nx, ny))

        return group, has_liberty

    def is_eye(self, x, y, player, board=None):
        """
        判断指定位置是否为某一方的眼位
        """
        if board is None:
            board = self.board
        if board[x, y] != 0:
            return False

        # 获取周围的合法邻点
        neighbors = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        valid_neighbors = [
            (nx, ny) for nx, ny in neighbors if 0 <= nx < self.board_size and 0 <= ny < self.board_size
        ]

        # 如果周围的点不全是己方棋子，则不是眼位
        if not all(board[nx, ny] == player for nx, ny in valid_neighbors):
            return False

        # 检查对角点
        diagonal_neighbors = [(x - 1, y - 1), (x - 1, y + 1), (x + 1, y - 1), (x + 1, y + 1)]
        valid_diagonal_neighbors = [
            (nx, ny) for nx, ny in diagonal_neighbors if 0 <= nx < self.board_size and 0 <= ny < self.board_size
        ]

        # 如果对角点有一个为空，且与之相邻的己方棋子块有超过一个棋子，则是真眼
        for nx, ny in valid_diagonal_neighbors:
            if board[nx, ny] == 0:
                adjacent_neighbors = [(nx - 1, ny), (nx + 1, ny), (nx, ny - 1), (nx, ny + 1)]
                valid_adjacent_neighbors = [
                    (ax, ay) for ax, ay in adjacent_neighbors if 0 <= ax < self.board_size and 0 <= ay < self.board_size
                ]
                for ax, ay in valid_adjacent_neighbors:
                    if board[ax, ay] == player:
                        group, _ = self.get_group(ax, ay, board)
                        if len(group) > 1:
                            return True

        # 检查是否为假眼
        for nx, ny in valid_neighbors:
            group, _ = self.get_group(nx, ny, board)
            if len(group) == 1:
                return False

        return True

    def render(self):
        for row in self.board:
            print(' '.join(['.' if x == 0 else 'x' if x == 1 else 'o' for x in row]))
        print()


if __name__ == "__main__":
    # 测试代码
    game = Game(board_size=9)
    game.reset()
    game.render()

    for i in range(1000):
        print(f"i = {i}")
        if not game.place_random_stone():
            if game.pass_move() in [0, 1, 2]:
                break
        game.render()

    print(game.calculate_scores())
