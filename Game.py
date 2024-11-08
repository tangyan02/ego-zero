import numpy as np


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
        self.ko = None

    def reset(self):
        self.board = np.zeros((self.board_size, self.board_size), dtype=int)
        self.current_player = 1
        self.history = []
        self.ko = None
        return self.board

    def is_valid_move(self, x, y):
        if x < 0 or x >= self.board_size or y < 0 or y >= self.board_size:
            return False
        if self.board[x, y] != 0:
            return False
        if (x, y) == self.ko:
            return False
        return True

    def place_stone(self, x, y):
        if not self.is_valid_move(x, y):
            return False
        self.board[x, y] = self.current_player
        self.history.append((x, y, self.current_player))
        self.ko = None

        # Remove dead stones
        dead_stones = self.remove_dead_stones(3 - self.current_player)
        if len(dead_stones) == 1:
            self.ko = dead_stones[0]

        self.current_player = 3 - self.current_player
        return True

    def remove_dead_stones(self, player):
        dead_stones = []
        visited = np.zeros((self.board_size, self.board_size), dtype=bool)

        def has_liberty(x, y):
            stack = [(x, y)]
            visited[x, y] = True
            while stack:
                cx, cy = stack.pop()
                for nx, ny in [(cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)]:
                    if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                        if self.board[nx, ny] == 0:
                            return True
                        if self.board[nx, ny] == player and not visited[nx, ny]:
                            visited[nx, ny] = True
                            stack.append((nx, ny))
            return False

        for x in range(self.board_size):
            for y in range(self.board_size):
                if self.board[x, y] == player and not visited[x, y]:
                    if not has_liberty(x, y):
                        dead_stones.append((x, y))

        for x, y in dead_stones:
            self.board[x, y] = 0

        return dead_stones

    def check_winner(self):
        black_score = np.sum(self.board == 1)
        white_score = np.sum(self.board == 2)
        return 1 if black_score > white_score else 2 if white_score > black_score else 0

    def render(self):
        for row in self.board:
            print(' '.join(['.' if x == 0 else 'B' if x == 1 else 'W' for x in row]))
        print()


env = Game(board_size=9)
env.reset()
env.render()


env.place_stone(1, 0)
env.render()

env.place_stone(0, 0)
env.render()

env.place_stone(0, 1)
env.render()
