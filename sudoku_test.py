"""
A few sudoku puzzles to test the solver on. 
Puzzles found at https://www.websudoku.com/?select=1&level=1,
and taken from solvomatic examples.
"""
from sudoku import Sudoku
from sat_solver import CNFSolver
from boards import Board
import time
import sys

def test_sudoku(test_boards):
    for board, puzzle in test_boards:
        sudoku_solver = CNFSolver(board, [puzzle])
        start_time = time.perf_counter()
        sudoku_solver.solve()
        end_time = time.perf_counter()
        solved = sudoku_solver.generate_solved_board()
        print(solved)
        print(f"Time to solve: {end_time-start_time} seconds")

data_easy_1 = [["9", "1", None, "7", None, None, None, None, None],
          [None, "3", "2", "6", None, "9", None, "8", None],
          [None, None, "7", None, "8", None, "9", None, None],
          [None, "8", "6", None, "3", None, "1", "7", None],
          ["3", None, None, None, None, None, None, None, "6"],
          [None, "5", "1", None, "2", None, "8", "4", None],
          [None, None, "9", None, "5", None, "3", None, None],
          [None, "2", None, "3", None, "1", "4", "9", None],
          [None, None, None, None, None, "2", None, "6", "1"]]

states_9 = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
board_1 = Board(data_easy_1, states_9)
easy_1 = Sudoku(board_1, states_9, 3, 3)

data_evil_2 = [["8", None, None, None, None, None, None, "5", None],
               [None, "1", None, None, "4", None, "6", None, "8"],
               ["7", None, None, None, None, "3", None, None, None],
               [None, None, None, None, "9", None, None, "2", None],
               [None, "5", None, None, None, None, None, "4", None],
               ["1", None, None, "7", None, None, "9", None, "5"],
               [None, None, None, None, None, None, "2", None, None],
               [None, None, "6", "4", None, None, None, None, None],
               [None, "8", None, None, "6", None, "1", None, "9"]]

board_2 = Board(data_evil_2, states_9)
evil_2 = Sudoku(board_2, states_9, 3, 3)

data_hardest_3 = [["8", None, None, None, None, None, None, None, None],
                  [None, None, "3", "6", None, None, None, None, None],
                  [None, "7", None, None, "9", None, "2", None, None],
                  [None, "5", None, None, None, "7", None, None, None],
                  [None, None, None, None, "4", "5", "7", None, None],
                  [None, None, None, "1", None, None, None, "3", None],
                  [None, None, "1", None, None, None, None, "6", "8"],
                  [None, None, "8", "5", None, None, None, "1", None],
                  [None, "9", None, None, None, None, "4", None, None]]

board_3 = Board(data_hardest_3, states_9)
hardest_3 = Sudoku(board_3, states_9, 3, 3)

data_empty_4 = [[None for _ in range(9)] for _ in range(9)] 

board_4 = Board(data_empty_4, states_9)
empty_4 = Sudoku(board_4, states_9, 3, 3)

test_boards = [(board_1, easy_1), (board_2, evil_2), (board_3, hardest_3), (board_4, empty_4)]

test_sudoku(test_boards)

