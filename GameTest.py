import numpy as np

from Game import Game


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


def test_is_eye_pair():
    game = Game(board_size=6)
    game.board = np.array([
        [1, 1, 1, 0, 0, 0],
        [1, 0, 1, 0, 0, 0],
        [1, 1, 0, 1, 0, 0],
        [0, 1, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 1],
        [0, 0, 0, 1, 1, 1]
    ])
    assert game.is_eye_pair(1, 1, 1, game.board)
    assert game.is_eye_pair(2, 2, 1, game.board)

    game = Game(board_size=6)
    game.board = np.array([
        [1, 1, 1, 0, 0, 0],
        [1, 0, 1, 0, 0, 0],
        [1, 1, 0, 1, 0, 0],
        [0, 1, 1, 1, 1, 1],
        [0, 0, 0, 0, 1, 0],
        [0, 0, 0, 1, 0, 1]
    ])
    assert not game.is_eye_pair(4, 5, 1, game.board)
    assert not game.is_eye_pair(5, 4, 1, game.board)

    game = Game(board_size=6)
    game.board = np.array([
        [0, 1, 0, 1, 0, 1],
        [1, 0, 1, 1, 1, 0],
        [1, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 1, 1],
        [0, 0, 0, 1, 0, 1],
        [0, 0, 0, 1, 1, 1]
    ])
    assert game.is_eye_pair(0, 0, 1, game.board)
    assert game.is_eye_pair(1, 1, 1, game.board)


def test_is_eye():
    game = Game(board_size=6)
    game.board = np.array([
        [1, 1, 0, 0, 0, 0],
        [1, 0, 1, 0, 0, 0],
        [1, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 1, 0],
        [0, 0, 0, 1, 0, 1],
        [0, 0, 0, 1, 1, 1]
    ])

    assert game.is_eye(1, 1, 1, game.board)
    assert game.is_eye(4, 4, 1, game.board)

    game = Game(board_size=6)
    game.board = np.array([
        [0, 1, 0, 1, 0, 0],
        [1, 1, 1, 1, 0, 0],
        [1, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 1, 1],
        [0, 0, 0, 1, 0, 1],
        [0, 0, 0, 1, 1, 1]
    ])

    assert game.is_eye(0, 0, 1, game.board)
    assert game.is_eye(0, 2, 1, game.board)
    assert game.is_eye(4, 4, 1, game.board)

    game = Game(board_size=6)
    game.board = np.array([
        [0, 1, 0, 1, 0, 1],
        [1, 0, 0, 1, 1, 0],
        [1, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 1, 1],
        [0, 0, 0, 1, 0, 1],
        [0, 0, 0, 1, 1, 1]
    ])
    assert not game.is_eye(0, 0, 1, game.board)
    assert not game.is_eye(0, 4, 1, game.board)

    print("test_is_eye测试通过")


# 测试落子操作
def test_place_stone():
    game = Game(board_size=9)
    x, y = 0, 0
    assert game.make_move(x, y)  # 第一次落子应该成功
    assert game.board[x, y] == 1  # 落子后该位置应该是黑棋（当前玩家为1）
    print("落子操作测试通过")


# 测试 pass 操作
def test_pass_move():
    game = Game(board_size=9)
    game.pass_move()
    assert not game.end_game_check()  # 第一次 pass 不应该结束游戏
    game.pass_move()  # 第二次 pass 应该结束游戏
    assert game.calculate_winner() in [0, 1, 2]  # 终局结果应该是 0（平局）、1（黑方胜）或 2（白方胜）
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
    expected_black_score = np.sum(game.board == 1) - game.tie_mu
    expected_white_score = np.sum(game.board == 2) + game.tie_mu
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
    game.refresh_eat_moves()
    assert game.make_move(0, 1)
    game.render()
    assert game.make_move(1, 0)
    game.render()
    assert game.make_move(1, 2)
    game.render()
    assert game.board[0, 2] == 0
    print("测试落子后吃子通过")


def test_place_stone_for_remove2():
    game = Game(board_size=3)
    # 手动设置棋盘状态以测试得分计算
    game.board = np.array([
        [1, 2, 1],
        [2, 0, 2],
        [1, 2, 1]
    ])
    game.refresh_eat_moves()
    game.make_move(1, 1)
    game.render()
    assert game.board[0, 1] == 0
    assert game.board[1, 0] == 0
    assert game.board[1, 2] == 0
    assert game.board[2, 1] == 0
    print("测试落子后吃子2通过")


def test_single_ko_cycle():
    game = Game(board_size=4)
    game.current_player = 2

    game.board = np.array([
        [2, 0, 0, 1],
        [0, 2, 1, 0],
        [0, 2, 1, 0],
        [2, 1, 0, 1]
    ])

    game.render()
    game.make_move(0, 2)
    game.render()
    game.make_move(0, 1)
    game.render()
    assert not game.is_valid_move(0, 2)
    print("测试单劫通过")


def test_make_move():
    data = """
    . x x x x x . x .
    x x x x x x x . x
    x . x . x x x x x
    x x x x x . x o .
    x x x x x x x x x
    . x x x o x o x x
    x x x o o o o o o
    x x o o o o . o o
    x o o o o o o . o
    """
    game = Game(board_size=9)
    game.parse(data)
    print(game.get_all_valid_moves_include_pass())
    assert len(game.get_all_valid_moves_include_pass()) == 1

    game.render()


def test_ko():
    game = Game(board_size=4)
    game.make_move(0, 0)
    game.render()
    game.make_move(0, 1)
    game.render()
    game = Game(board_size=6)
    game.current_player = 2

    game.board = np.array([
        [2, 0, 0, 1, 0, 0],
        [0, 2, 1, 0, 0, 2],
        [0, 0, 0, 0, 2, 0],
        [0, 0, 0, 0, 1, 2],
        [0, 2, 1, 0, 0, 1],
        [2, 1, 0, 1, 0, 0]
    ])

    game.render()
    game.make_move(0, 2)

    game.render()

    game.make_move(0, 1)
    game.render()

    game.make_move(5, 2)
    game.render()

    game.make_move(2, 5)
    game.render()

    game.make_move(0, 2)
    game.render()

    game.make_move(5, 1)
    game.render()

    game.make_move(3, 5)
    game.render()

    assert not game.is_valid_move(0, 1)
    print("循环劫测试通过")


def test_banned_moves():
    game = Game(board_size=4)
    game.current_player = 2
    data = """
    x o . x
    . x x .
    . . . .
    . . . .
    """
    game.parse(data)
    assert not game.is_valid_move(0, 2)

    game = Game(board_size=4)
    game.current_player = 2
    data = """
     x o . x
     . x . .
     . . . .
     . . . .
     """
    game.parse(data)
    assert game.is_valid_move(0, 2)

    print("禁止点测试通过")


def test_eat_moves():
    game = Game(board_size=4)
    game.current_player = 1
    data = """
     x o . x
     . x o o
     . . x o
     . . x o
     """
    game.parse(data)
    assert len(game.eat_moves[0, 2]) == 5

    print("打吃点测试通过")


if __name__ == '__main__':
    # 运行测试用例
    test_is_valid_move()
    test_place_stone()
    test_pass_move()
    test_calculate_scores()
    test_place_stone_for_remove()
    test_place_stone_for_remove2()
    test_is_eye()
    test_is_eye_pair()
    test_single_ko_cycle()
    test_ko()
    test_banned_moves()
    test_eat_moves()
