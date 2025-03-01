# 定义棋盘的颜色
import threading

import pygame

BOARD_COLOR = (204, 153, 102)
LINE_COLOR = (0, 0, 0)
BLACK_STONE_COLOR = (0, 0, 0)
WHITE_STONE_COLOR = (255, 255, 255)


class GameUI:

    def createWindow(self):
        # 初始化 pygame
        pygame.init()
        pygame.display.set_caption("围棋棋盘")

    def __init__(self, board_size):
        self.board_size = board_size
        # 计算窗口大小
        self.window_size = 600
        self.cell_size = self.window_size // self.board_size
        # 创建窗口
        self.screen = pygame.display.set_mode((self.window_size, self.window_size))


    def render_task(self, board):
        # 填充背景色
        self.screen.fill(BOARD_COLOR)

        # 计算偏移量，使棋盘从中间开始
        offset_x = (self.window_size - (self.board_size - 1) * self.cell_size) // 2
        offset_y = (self.window_size - (self.board_size - 1) * self.cell_size) // 2

        # 绘制棋盘网格
        for i in range(self.board_size):
            start_x = offset_x + i * self.cell_size
            start_y = offset_y + i * self.cell_size
            pygame.draw.line(self.screen, LINE_COLOR, (start_x, offset_y),
                             (start_x, offset_y + (self.board_size - 1) * self.cell_size), 2)
            pygame.draw.line(self.screen, LINE_COLOR, (offset_x, start_y),
                             (offset_x + (self.board_size - 1) * self.cell_size, start_y), 2)

        # 绘制棋子
        for i in range(self.board_size):
            for j in range(self.board_size):
                if board[i][j] == 1:  # 黑子
                    # 调整坐标到网格交叉点
                    y = offset_x + i * self.cell_size
                    x = offset_y + j * self.cell_size
                    pygame.draw.circle(self.screen, BLACK_STONE_COLOR, (x, y), self.cell_size // 2 - 2)
                elif board[i][j] == 2:  # 白子
                    # 调整坐标到网格交叉点
                    y = offset_x + i * self.cell_size
                    x = offset_y + j * self.cell_size
                    pygame.draw.circle(self.screen, WHITE_STONE_COLOR, (x, y), self.cell_size // 2 - 2)

        # 更新显示
        pygame.display.flip()

    def render(self, board):
        for event in pygame.event.get():  # pygame 推出
            if event.type == pygame.QUIT:
                return
        threading.Thread(target=self.render_task, args=(board,)).start()
