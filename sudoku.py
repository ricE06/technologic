# rules for the sudoku puzzle type,
# as well as the solver creator itself

from rules import Rule, SuperRule
from sat_solver import CNFSolver
from boards import Board

class InitialConditions(Rule):

    def __init__(self, board, states):
        super().__init__(board, states)

    def add_formulas(self):
        for row_idx, row in enumerate(self.board.data):
            for col_idx, cell in enumerate(row):
                if cell not in self.board.visible_states:
                    continue
                var = self.gen_state_int(row_idx, col_idx, cell)
                clause = {var: True}
                self.add_clause(clause)

class AtMostOneInRegion(Rule):

    def __init__(self, board, states, region_coords):
        """
        Creates a rule requiring that no two cells can have the same state.
        Args:
            board: representation of the board as a dictionary
            states: list of states to apply the rule over
            region_coords: list of (row, col) tuples representing cells in a region
        """
        self.region_coords = region_coords
        super().__init__(board, states)

    def add_formulas(self):
        for state in self.states:
            vars = [self.gen_state_int(*coords, state) for coords in self.region_coords]
            for var_1, var_2 in Rule.construct_subsets(vars, 2):
                clause = {var_1: False, var_2: False}
                self.add_clause(clause)

class AtLeastOneInRegion(Rule):

    def __init__(self, board, states, region_coords):
        """
        Creates a rule requiring that at least one of each state in `states`
        must exist in a region.
        """
        self.region_coords = region_coords
        super().__init__(board, states)

    def add_formulas(self):
        for state in self.states:
            clause = {self.gen_state_int(*coords, state): True for coords in self.region_coords}
            self.add_clause(clause)

class ExactlyOneInRegion(SuperRule):

    def __init__(self, board, states, region_coords):
        assert len(states) == len(region_coords)
        self.rules = [AtMostOneInRegion(board, states, region_coords), 
                      AtLeastOneInRegion(board, states, region_coords)]
        super().__init__(self.rules)

class ExactlyOneInRepeatingRect(SuperRule):

    def __init__(self, board, states, reg_height, reg_width):
        assert board.height % reg_height == 0 and board.width % reg_width == 0
        self.board = board
        self.reg_height, self.reg_width = reg_height, reg_width
        self.regions = self.gen_regions()
        self.rules = [ExactlyOneInRegion(board, states, region_coords) for region_coords in self.regions]
        super().__init__(self.rules)

    def gen_regions(self):
        """
        Returns a list of list of tuples of (row, col) coordinates, where each inner list
        is a rectangle with height `self.reg_height` and width `self.reg_width`,
        and the regions cover the board.
        """
        height, width = self.board.height, self.board.width
        num_regs_vert = height // self.reg_height
        num_regs_hori = width // self.reg_width
        out = [[] for _ in range(num_regs_vert*num_regs_hori)]
        for r in range(height):
            for c in range(width):
                out_idx = (r // self.reg_height) * num_regs_hori + (c // self.reg_width)
                out[out_idx].append((r, c))
        return out
         
class Sudoku(SuperRule):

    def __init__(self, board, states, reg_height, reg_width):
        self.board = board
        self.states = states
        self.height, self.width = board.height, board.width
        row_rule = ExactlyOneInRepeatingRect(board, states, 1, board.width)
        col_rule = ExactlyOneInRepeatingRect(board, states, board.height, 1)
        reg_rule = ExactlyOneInRepeatingRect(board, states, reg_height, reg_width)
        init_cond = InitialConditions(board, states)
        # self.rules = [row_rule, init_cond]
        self.rules = [row_rule, col_rule, reg_rule, init_cond]
        super().__init__(self.rules, True)

class TestSudoku(SuperRule):

    def __init__(self, board, states, reg_height, reg_width):
        self.board = board
        self.states = states
        self.height, self.width = board.height, board.width
        row_rule = ExactlyOneInRepeatingRect(board, states, 1, board.width)
        # col_rule = ExactlyOneInRepeatingRect(board, states, board.height, 1)
        # reg_rule = ExactlyOneInRepeatingRect(board, states, reg_height, reg_width)
        init_cond = InitialConditions(board, states)
        self.rules = [row_rule, init_cond]
        # self.rules = [row_rule, col_rule, reg_rule, init_cond]
        super().__init__(self.rules, True)

if __name__ == "__main__":
    simple_sudoku = Board([["4", None, None, "4"]])
    states = ["1", "2", "3", "4"]
    reg_height, reg_width = 2, 2
    puzzle = TestSudoku(simple_sudoku, states, reg_height, reg_width)
    sudoku_solver = CNFSolver(simple_sudoku, rules=[puzzle])
    print(sudoku_solver.solve())
    solved = sudoku_solver.generate_solved_board()
    print(solved)


