"""
A few nurikabe puzzles to test the solver on. 
Puzzles found at https://www.puzzle-nurikabe.com/.
"""
from nurikabe import Nurikabe
from sat_solver import CNFSolver
from boards import Board
from nurikabe import NurikabeBoard
import time
import sys

def test_sudoku(test_boards):
    for board, puzzle in test_boards:
        sys.setrecursionlimit(20_000)
        puzzle_solver = CNFSolver(board, [puzzle])
        start_time = time.perf_counter()
        solver = puzzle_solver.solve(verbose=False, max_sols=1)
        next(solver)
        end_time = time.perf_counter()
        solved = puzzle_solver.generate_solved_board()
        print(solved)
        print(f"Time to solve: {end_time-start_time} seconds")

def add_constraints_to_board(numbers: list[list[int]], constraints: list[tuple[int, int, int]]) -> None:
    """
    Adds a list of numbers to the corresponding to coordinates.
    """
    for row, col, val in constraints:
        numbers[row][col] = val

# 7x7 easy, puzzle ID 9,027,278
data_easy_1 = Board.gen_empty_board(7, 7)
data_easy_1[2][5] = "x"
numbers_1 = Board.gen_empty_board(7, 7)
constraints = [(1, 5, 5), (2, 0, 1), (3, 1, 1), (3, 5, 3), (4, 6, 5), (5, 1, 1)] 
add_constraints_to_board(numbers_1, constraints)
empty_state = "."
filled_state = "x"
easy_1_board = NurikabeBoard(data_easy_1, numbers_1, [empty_state, filled_state])
easy_1_rule = Nurikabe(easy_1_board, empty_state, filled_state)

data_hard_2 = Board.gen_empty_board(7, 7)
data_hard_2[3][5] = "x"
numbers_2 = Board.gen_empty_board(7, 7)
constraints = [(0, 0, 1), (0, 6, 2), (1, 2, 2), (2, 5, 3), (4, 5, 7), (5, 2, 2), (6, 6, 3)]
add_constraints_to_board(numbers_2, constraints)
hard_2_board = NurikabeBoard(data_hard_2, numbers_2, [empty_state, filled_state])
hard_2_rule = Nurikabe(hard_2_board, empty_state, filled_state)


test_boards = [(easy_1_board, easy_1_rule), (hard_2_board, hard_2_rule)]

test_sudoku(test_boards)
