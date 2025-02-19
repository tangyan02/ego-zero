import numpy as np

from Game import Game


# 测试重置棋盘
def test_reset():
    game = Game(board_size=9)
    initial_board = game.board.copy()
    game.board[0, 0] = 1
    game.reset()
    assert np.array_equal(game.board, initial_board)
    print("重置棋盘测试通过")


# 测试落子有效性
def test_is_valid_move():
    game = Game(board_size=9)
    # 边界外落子，应无效
    assert not game.is_valid_move(-1, 0)
    assert not game.is_valid_move(9, 0)
    assert not game.is_valid_move(0, -1)
    assert not game.is_valid_move(0, 9)
    # 已有棋子的位置落子，应无效
    game.board[0, 0] = 1
    assert not game.is_valid_move(0, 0)
    print("落子有效性测试通过")


# 测试落子操作
def test_place_stone():
    game = Game(board_size=9)
    x, y = 0, 0
    assert game.place_stone(x, y)  # 第一次落子应该成功
    assert game.board[x, y] == 1  # 落子后该位置应该是黑棋（当前玩家为1）
    assert not game.place_stone(x, y)  # 再次落子到同一位置应该失败
    print("落子操作测试通过")


# 测试 pass 操作
def test_pass_move():
    game = Game(board_size=9)
    game.pass_move()
    assert not game.end_game_check()  # 第一次 pass 不应该结束游戏
    game.pass_move()  # 第二次 pass 应该结束游戏
    assert game.end_game() in [0, 1, 2]  # 终局结果应该是 0（平局）、1（黑方胜）或 2（白方胜）
    print("pass 操作测试通过")


# 测试终局计算得分
def test_calculate_scores():
    game = Game(board_size=3)
    # 手动设置棋盘状态以测试得分计算
    game.board = np.array([
        [1, 0, 2],
        [0, 1, 0],
        [2, 0, 1]
    ])
    black_score, white_score = game.calculate_scores()
    # 根据手动设置的棋盘状态计算预期得分
    # 这里只计算棋子数
    expected_black_score = np.sum(game.board == 1)
    expected_white_score = np.sum(game.board == 2)
    assert black_score == expected_black_score
    assert white_score == expected_white_score
    print("得分计算测试通过")


# 测试落子后吃子
def test_place_stone_for_remove():
    game = Game(board_size=3)
    # 手动设置棋盘状态以测试得分计算
    game.board = np.array([
        [1, 0, 2],
        [0, 1, 0],
        [2, 0, 1]
    ])
    assert game.place_stone(0, 1)
    assert not game.place_stone(1, 2)
    assert game.place_stone(1, 0)
    assert game.place_stone(1, 2)
    assert not game.place_stone(1, 2)
    assert not game.place_stone(2, 0)
    print()
    game.render()
    print("测试落子后吃子通过")

def test_place_stone_for_remove2():
    game = Game(board_size=3)
    # 手动设置棋盘状态以测试得分计算
    game.board = np.array([
        [1, 2, 1],
        [2, 0, 2],
        [1, 2, 1]
    ])
    assert game.place_stone(1, 1)
    print()
    game.render()
    print("测试落子后吃子2通过")

if __name__ == '__main__':
    # 运行测试用例
    test_reset()
    test_is_valid_move()
    test_place_stone()
    test_pass_move()
    test_calculate_scores()
    test_place_stone_for_remove()
    test_place_stone_for_remove2()
