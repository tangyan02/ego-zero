from distutils.command.check import check

import numpy as np
import random

import torch

import Utils


class Point:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y


class Game:
    def __init__(self, board_size=19, device=Utils.getDevice()):
        self.board_size = board_size
        self.board = np.zeros((board_size, board_size), dtype=int)
        self.current_player = 1
        self.history = []
        self.ko_point = None  # 用于记录劫的位置
        self.pass_count = 0  # 记录双方连续 passes 的次数，用于终局判定
        self.ko_history = []  # 记录劫的历史状态，用于处理单劫循环
        self.device = device

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

        # 检查单劫循环
        if (x, y) in self.ko_history and np.array_equal(temp_board, self.history[-1]):
            return False

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

        # 检查是否为己方的眼位
        if self.is_eye(x, y, self.current_player, self.board):
            return False

        return True

    def make_move(self, x, y):
        if x == -1 and y == -1:
            self.pass_move()
            return True

        # if not self.is_valid_move(x, y):
        #     return False

        self.board[x, y] = self.current_player
        self.history.append(self.board.copy())
        # print(f"玩家 {self.current_player} 落子 {x}, {y}")

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
        # self.render()
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
        print(f"当前玩家 {self.current_player}")
        valid_moves = self.get_all_valid_moves()
        if not valid_moves:
            return False
        # print(f"所有落子点 {valid_moves}")
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
                    if self.is_eye(x, y, 1):
                        black_territory += 1
                    elif self.is_eye(x, y, 2):
                        white_territory += 1

        black_score = black_stones + black_territory
        white_score = white_stones + white_territory

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

        if not self.is_cross_eye(x, y, player, board):
            return False

        opp_count, corner_blank_count, cross_blank_count = self.count_around(x, y, player, board)
        if opp_count > 0 or cross_blank_count > 0 or corner_blank_count > 2:
            return False

        # 对角
        corner_list = [(x + 1, y + 1), (x + 1, y - 1), (x - 1, y + 1), (x - 1, y - 1)]
        for px, py in corner_list:
            if 0 <= px < self.board_size and 0 <= py < self.board_size and self.is_cross_eye(px, py, player, board):
                p_opp_count, p_corner_blank_count, p_cross_blank_count = self.count_around(px, py, player, board)
                if p_opp_count == 0 and p_cross_blank_count == 0 and p_corner_blank_count + corner_blank_count <= 3:
                    return True
        return False

    def count_around(self, x, y, player, board=None):
        """
        返回周围对手的点个数和对角空点个数和相邻点空点个数
        """
        if board is None:
            board = self.board

        opp_count = 0
        corner_blank_count = 0
        cross_blank_count = 0

        # 相邻
        cross_list = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        # 对角
        corner_list = [(x + 1, y + 1), (x + 1, y - 1), (x - 1, y + 1), (x - 1, y - 1)]
        for px, py in cross_list:
            if 0 <= px < self.board_size and 0 <= py < self.board_size:
                if board[px][py] == 3 - player:
                    opp_count += 1
                if board[px][py] == 0:
                    cross_blank_count += 1

        for px, py in corner_list:
            if 0 <= px < self.board_size and 0 <= py < self.board_size:
                if board[px][py] == 3 - player:
                    opp_count += 1
                if board[px][py] == 0:
                    corner_blank_count += 1

        return opp_count, corner_blank_count, cross_blank_count

    def is_cross_eye(self, x, y, player, board=None):
        """
        仅判断上下左右均为己方
        """
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

    def is_eye(self, x, y, player, board=None):
        """
        判断指定位置是否为某一方的眼位
        """
        if board is None:
            board = self.board
        if board[x, y] != 0:
            return False

        opp_count, corner_blank_count, cross_blank_count = self.count_around(x, y, player, board)
        if cross_blank_count == 0 and opp_count == 0 and cross_blank_count <= 1:
            return True

        if self.is_eye_pair(x, y, player, board):
            return True

        return False

    def render(self):
        for row in self.board:
            print(' '.join(['.' if x == 0 else 'x' if x == 1 else 'o' for x in row]))
        print()

    def copy(self):
        new_game = Game(board_size=self.board_size, device=self.device)
        new_game.board = self.board.copy()
        new_game.current_player = self.current_player
        new_game.history = [board.copy() for board in self.history]
        new_game.ko_point = self.ko_point
        new_game.pass_count = self.pass_count
        new_game.ko_history = self.ko_history.copy()
        return new_game


if __name__ == "__main__":
    # 测试代码
    game = Game(board_size=9)
    game.reset()
    game.render()

    for i in range(1000):
        print(f"第 {i} 步")

        if not game.make_random_move():
            game.pass_move()

        if game.end_game_check():
            game.render()
            break

        game.render()

    game.calculate_scores()
