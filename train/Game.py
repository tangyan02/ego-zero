import random
import time

import numpy as np

import Utils


class Point:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y


class Game:
    def __init__(self, board_size=19, device=Utils.getDevice(), tie_mu=6.5):
        self.board_size = board_size
        self.board = np.zeros((board_size, board_size), dtype=np.uint8)
        self.current_player = 1
        self.history = []
        self.move_history = []
        self.banned_moves = set()  # 记录当前玩家的禁止点
        self.eat_moves = {}  # 记录当前玩家的打吃点，和对手的被吃点
        self.history_max_size = 8
        self.pass_count = 0  # 记录双方连续 passes 的次数，用于终局判定
        self.device = device
        self.tie_mu = tie_mu

    def parse(self, data):
        x, y = (0, 0)
        for line in data.split("\n"):
            line = line.strip()
            if line == "":
                continue
            items = line.split(" ")
            for item in items:
                if item == "x":
                    self.board[x, y] = 1
                if item == "o":
                    self.board[x, y] = 2
                if item == ".":
                    self.board[x, y] = 0
                y += 1
            y = 0
            x += 1
        self.refresh_banned_moves()
        self.refresh_eat_moves()

    def is_valid_move(self, x, y):
        if x < 0 or x >= self.board_size or y < 0 or y >= self.board_size:
            return False
        if self.board[x, y] != 0:
            return False

        # 检查落子后己方棋块是否有气
        if (x, y) in self.banned_moves:
            return False

        # 临时落子
        temp_board = self.board.copy()
        temp_board[x, y] = self.current_player

        # 检查并移除对手的死子
        if self.eat_moves.get((x, y)) is not None:
            for dx, dy in self.eat_moves[x, y]:
                temp_board[dx, dy] = 0

            # 检查劫循环
            for idx, (his_x, his_y) in enumerate(self.move_history):
                if x == his_x and y == his_y:
                    if np.array_equal(temp_board, self.history[idx]):
                        return False

        # 检查是否为己方的眼位
        if self.is_eye(x, y, self.current_player, self.board):
            return False

        return True

    def make_move(self, x, y):
        if x == -1 and y == -1:
            self.pass_move()
            self.history.append(self.board.copy())
            return True

        # if not self.is_valid_move(x, y):
        #     return False
        self.board[x, y] = self.current_player
        # print(f"玩家 {self.current_player} 落子 {x}, {y}")

        # 检查并移除对手的死子
        opponent = 3 - self.current_player
        if self.eat_moves.get((x, y)) is not None:
            for dx, dy in self.eat_moves[x, y]:
                self.board[dx, dy] = 0

        self.history.append(self.board.copy())
        # 检查历史记录的长度是否超过 8
        if len(self.history) > self.history_max_size:
            # 截取掉早期的数据，只保留最新的 8 个元素
            self.history = self.history[-self.history_max_size:]

        # 更新落子的历史
        self.move_history.append((x, y))
        if len(self.move_history) > self.history_max_size:
            # 截取掉早期的数据，只保留最新的 8 个元素
            self.move_history = self.move_history[-self.history_max_size:]

        self.current_player = opponent
        self.pass_count = 0  # 落子后重置 pass 计数

        # 更新禁止点和打吃点
        self.refresh_banned_moves()
        self.refresh_eat_moves()
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

    def get_all_valid_moves_include_pass(self):
        """
        获取所有可落子的点
        """
        valid_moves = []
        for x in range(self.board_size):
            for y in range(self.board_size):
                if self.is_valid_move(x, y):
                    valid_moves.append((x, y))
        if self.pass_count < 2 and len(valid_moves) == 0:
            valid_moves.append((-1, -1))
        return valid_moves

    def make_random_move(self):
        """
        随机选择一个可落子的点落子
        """
        valid_moves = self.get_all_valid_moves_include_pass()
        x, y = random.choice(valid_moves)
        return self.make_move(x, y)

    def pass_move(self):
        """
        玩家选择 pass
        """
        self.pass_count += 1
        self.current_player = 3 - self.current_player
        # print("pass count:", self.pass_count)

    def end_game_check(self):
        return self.pass_count >= 2

    def calculate_winner(self):
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
        计算双方的得分，包括棋子数和领地（只计算眼位）
        """
        black_stones = np.sum(self.board == 1)
        white_stones = np.sum(self.board == 2)

        black_territory = 0
        white_territory = 0

        # 遍历棋盘上的每个空位，判断是否为眼位
        for x in range(self.board_size):
            for y in range(self.board_size):
                if self.board[x, y] == 0:
                    if self.is_cross_eye(x, y, 1):
                        black_territory += 1
                    elif self.is_cross_eye(x, y, 2):
                        white_territory += 1

        black_score = black_stones + black_territory - self.tie_mu
        white_score = white_stones + white_territory + self.tie_mu

        # 添加调试信息
        # print(f"黑方棋子数: {black_stones}，领地数: {black_territory}，总分: {black_score}")
        # print(f"白方棋子数: {white_stones}，领地数: {white_territory}，总分: {white_score}")

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

    def is_eye_pair(self, x, y, player, board=None):
        """
        判断相邻的眼位
        x x x .
        x . x x
        x x . x
        . x x x
        """
        if board is None:
            board = self.board

        self_corner_count_limit = 2
        if self.is_on_side(x, y):
            self_corner_count_limit = 1
        corner_not_self_count, cross_not_self_count = self.count_around(x, y, player, board)
        if cross_not_self_count > 0 or corner_not_self_count > self_corner_count_limit:
            return False

        # 对角
        corner_list = [(x + 1, y + 1), (x + 1, y - 1), (x - 1, y + 1), (x - 1, y - 1)]
        for px, py in corner_list:
            p_self_corner_count_limit = 3
            if self.is_on_side(px, py) and self.is_on_side(x, y):
                p_self_corner_count_limit = 2
            if 0 <= px < self.board_size and 0 <= py < self.board_size and self.is_cross_eye(px, py, player, board):
                p_corner_not_self_count, p_cross_not_self_count = self.count_around(px, py, player, board)
                if p_cross_not_self_count == 0 and p_corner_not_self_count + corner_not_self_count <= p_self_corner_count_limit:
                    return True
        return False

    def count_around(self, x, y, player, board=None):
        """
        返回周围对手的点个数和对角空点个数和相邻点空点个数
        """
        if board is None:
            board = self.board

        # 相邻
        cross_list = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        cross_not_self_count = 0

        for px, py in cross_list:
            if 0 <= px < self.board_size and 0 <= py < self.board_size:
                if board[px][py] != player:
                    cross_not_self_count += 1

        # 对角
        corner_list = [(x + 1, y + 1), (x + 1, y - 1), (x - 1, y + 1), (x - 1, y - 1)]
        corner_not_self_count = 0
        for px, py in corner_list:
            if 0 <= px < self.board_size and 0 <= py < self.board_size:
                if board[px][py] != player:
                    corner_not_self_count += 1

        return corner_not_self_count, cross_not_self_count

    def is_on_side(self, x, y):
        if x == 0 or y == 0 or x == self.board_size - 1 or y == self.board_size - 1:
            return True

    def is_cross_eye(self, x, y, player, board=None):
        # """
        # 仅判断上下左右均为己方
        # """
        if board is None:
            board = self.board
        if board[x, y] != 0:
            return False

        # 相邻
        cross_list = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        for px, py in cross_list:
            if 0 <= px < self.board_size and 0 <= py < self.board_size:
                if board[px][py] != player:
                    return False
        return True

    def count_cross(self, x, y, player, board=None):
        if board is None:
            board = self.board

        blank_count = 0
        self_count = 0
        opp_count = 0

        # 相邻
        cross_list = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        for px, py in cross_list:
            if 0 <= px < self.board_size and 0 <= py < self.board_size:
                if board[px][py] == 0:
                    blank_count += 1
                elif board[px][py] == player:
                    self_count += 1
                elif board[px][py] == 3 - player:
                    opp_count += 1
        return blank_count, self_count, opp_count

    def is_eye(self, x, y, player, board=None):
        """
        判断指定位置是否为某一方的眼位
        """
        if board is None:
            board = self.board
        if board[x, y] != 0:
            return False

        corner_not_self_count, cross_not_self_count = self.count_around(x, y, player, board)
        corner_limit = 1
        if self.is_on_side(x, y):
            corner_limit = 0
        if cross_not_self_count == 0 and corner_not_self_count <= corner_limit:
            return True

        if self.is_eye_pair(x, y, player, board):
            return True

        return False

    def refresh_banned_moves(self):
        self.banned_moves = set()
        visited = np.zeros((self.board_size, self.board_size), dtype=bool)
        for x in range(0, self.board_size):
            for y in range(0, self.board_size):
                if self.board[x][y] == 0:
                    # 判断条件：周围没有气，且有对方棋子
                    blank_count, self_count, opp_count = self.count_cross(x, y, self.current_player, self.board)
                    if blank_count == 0:
                        self.board[x][y] = self.current_player
                        # 尝试填充，然后判断有没有气
                        stack = [(x, y)]
                        visited[x, y] = True
                        qi_count = 0

                        near_first_visit = True
                        for nx, ny in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
                            if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                                if visited[nx, ny]:
                                    near_first_visit = False

                        while stack:
                            cx, cy = stack.pop()
                            for nx, ny in [(cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)]:
                                if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                                    if self.board[nx, ny] == 0:
                                        qi_count += 1
                                    elif self.board[nx, ny] == self.current_player and not visited[nx, ny]:
                                        visited[nx, ny] = True
                                        stack.append((nx, ny))
                        if qi_count == 0 and near_first_visit:
                            self.banned_moves.add((x, y))
                        self.board[x][y] = 0

    def refresh_eat_moves(self):
        self.eat_moves = {}
        visited = np.zeros((self.board_size, self.board_size), dtype=bool)
        for x in range(0, self.board_size):
            for y in range(0, self.board_size):
                if self.board[x][y] == 3 - self.current_player and not visited[x][y]:
                    stack = [(x, y)]
                    visited[x, y] = True
                    group = []
                    qi_count = 0
                    qi_move = None
                    while stack:
                        cx, cy = stack.pop()
                        group.append((cx, cy))
                        for nx, ny in [(cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)]:
                            if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                                if self.board[nx, ny] == 0:
                                    qi_count += 1
                                    qi_move = (nx, ny)
                                elif self.board[nx, ny] == 3 - self.current_player and not visited[nx, ny]:
                                    visited[nx, ny] = True
                                    stack.append((nx, ny))
                    if qi_count == 1:
                        if self.eat_moves.get(qi_move) is not None:
                            self.eat_moves[qi_move].extend(group)
                        else:
                            self.eat_moves[qi_move] = group

    def render(self):
        for row in self.board:
            print(' '.join(['.' if x == 0 else 'x' if x == 1 else 'o' for x in row]))
        print()


if __name__ == "__main__":
    # 测试代码
    game = Game(board_size=19)
    start_time = time.time()
    for i in range(1000):
        print(f"第 {i} 步")
        game.make_random_move()
        if game.end_game_check():
            game.render()
            break

        game.render()

    print(game.calculate_scores(), "cost", time.time() - start_time)
