# 定义棋盘的颜色
import threading

import pygame

BOARD_COLOR = (204, 153, 102)
LINE_COLOR = (0, 0, 0)
BLACK_STONE_COLOR = (0, 0, 0)
WHITE_STONE_COLOR = (255, 255, 255)
TEXT_COLOR = (0, 0, 0)  # 文字颜色


class GameUI:


    def __init__(self, board_size):
        self.board_size = board_size

        # 初始化 pygame
        pygame.init()
        # 计算窗口大小
        self.window_size = 800
        self.cell_size = self.window_size // self.board_size
        # 创建窗口
        self.screen = pygame.display.set_mode((self.window_size, self.window_size))
        # 状态栏高度
        self.status_bar_height = 50
        # 创建窗口，包含状态栏高度
        self.screen = pygame.display.set_mode((self.window_size, self.window_size + self.status_bar_height))
        try:
            # 尝试加载黑体字体
            self.font = pygame.font.Font('font/msyhbd.ttc', 20)
        except FileNotFoundError:
            # 如果找不到字体文件，使用默认字体
            self.font = pygame.font.Font(None, 20)
        pygame.display.set_caption("围棋棋盘")

    def render_task(self, board, info_text = ""):
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

        # 如果是9路棋盘，绘制特定小黑点
        if self.board_size == 9:
            dot_coordinates = [(2, 2), (2, 6), (6, 2), (6, 6), (4, 4)]
            for x, y in dot_coordinates:
                dot_x = offset_x + x * self.cell_size
                dot_y = offset_y + y * self.cell_size
                pygame.draw.circle(self.screen, BLACK_STONE_COLOR, (dot_x, dot_y), 7)

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

        # 绘制状态栏背景
        pygame.draw.rect(self.screen, (220, 220, 220), (0, self.window_size, self.window_size, self.status_bar_height))

        # 绘制文字信息栏
        text_surface = self.font.render(info_text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=(self.window_size // 2, self.window_size + self.status_bar_height // 2))
        self.screen.blit(text_surface, text_rect)

        # 更新显示
        pygame.display.flip()

    def render(self, board, text=""):
        for event in pygame.event.get():  # pygame 推出
            if event.type == pygame.QUIT:
                return
        threading.Thread(target=self.render_task, args=(board,text)).start()
