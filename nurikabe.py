# class of rules for the puzzle type Nurikabe

from typing import List, Tuple, Dict
from boards import Board, BoardData
from rules import Rule, SuperRule
from sat_solver import CNFSolver
from pprint import pp

class AtLeastOneOfStateInCell(Rule):
    """
    Simple rule requiring that each cell must
    have at least one state True.
    """

    def __init__(self, board: Board, states: list[str]) -> None:
        super().__init__(board, states)

    def add_formulas(self) -> None:
        for cell in self.board.get_all_cells():
            cell_states = [self.gen_state_int(*cell, state_name) for state_name in self.states]
            clause = {var: True for var in cell_states}
            self.add_clause(clause)
        return None

class InitialAuxiliaryConditions(Rule):
    """
    Simple rule relating a set of cells to a state.
    """

    def __init__(self, board: Board, coords: List[tuple[int, int]], literals: List[bool], state_name: str) -> None:
        """
        Args:
            board: the game board
            coords: a list of (row, col) tuples for the rule to apply to
            literals: a list of booleans with same length as coords, represents
                for each coordinate, whether the state is known to be True or False
            state_name: the name of the state to apply this over
        """
        assert len(coords) == len(literals)
        self.coords = coords
        self.literals = literals
        self.state_name = state_name
        super().__init__(board, [state_name])

    def add_formulas(self):
        for cell, literal in zip(self.coords, self.literals):
            clause = {self.gen_state_int(*cell, self.state_name): literal}
            self.add_clause(clause)
        return None

class NoTwoByTwoSquare(Rule):
    """
    Rule requiring that no 2x2 square of cells can share the
    same state.
    """

    def __init__(self, board: Board, states: List[str]) -> None:
        super().__init__(board, states)

    def add_formulas(self):
        coords = self.gen_squares()
        for state_name in self.states:
            for square in coords:
                clause = {self.gen_state_int(*pair, state_name): False
                          for pair in square}
                self.add_clause(clause)
        return None

    def gen_squares(self) -> List[Tuple[int, int]]:
        """
        Returns a list of tuples, where each tuple
        contains four (row, col) coordinates for
        each possible square on the board.
        """
        height, width = self.board.height, self.board.width
        out = []
        for row in range(height-1):
            for col in range(width-1):
                square = ((row, col), (row+1, col), (row, col+1), (row+1, col+1))
                out.append(square)
        return out

class NoAdjacenciesBetweenStates(Rule):
    """
    Rule requiring that any cells with different states cannot
    be adjacent.
    """

    def __init__(self, board: Board, states: list[str]) -> None:
        super().__init__(board, states)

    def add_formulas(self) -> None:
        all_edges = []
        all_coords = self.board.get_all_cells()
        for cell in all_coords:
            for adj_cell in self.board.get_adjacencies(*cell):
                new_edge = (cell, adj_cell)
                all_edges.append(new_edge)
        state_name_pairs= list(Rule.construct_subsets(self.states, 2))
        for cell_pair in all_edges:
            for state_pair in state_name_pairs:
                clause = {self.gen_state_int(*cell, state): False
                          for cell, state in zip(cell_pair, state_pair)}
                self.add_clause(clause)
        return None

class AtMostNInBoard(Rule):
    """
    Rule requiring that at most N cells on the board can have a certain
    state. Assumes that N is less than the total number of cells on the board.
    """

    def __init__(self, board: Board, state_name: str, max_num: int) -> None:
        self.max_num = max_num
        self.target_state = state_name
        self.additional_states = self.create_sequential_states()
        super().__init__(board, [state_name] + self.additional_states)

    def add_formulas_binomial(self) -> None:
        all_states = [self.gen_state_int(*coords, self.target_state)
                      for coords in self.board.get_all_cells()]
        for var_set in Rule.construct_subsets(all_states, self.max_num+1):
            clause = {var: False for var in var_set}
            self.add_clause(clause)
        return None

    def create_aux_state(self, n) -> str:
        return self.target_state + "k" + str(n)

    def create_sequential_states(self) -> list[str]:
        """
        Returns auxiliary states needed for the sequential encoding.
        """
        return [self.create_aux_state(n) for n in range(0, self.max_num)]

    def add_formulas_sequential(self) -> None:
        """
        Encoding scheme based off of section 3.3 in Frisch and Giannoros 
        https://www2.it.uu.se/research/group/astra/ModRef10/papers/Alan%20M.%20Frisch%20and%20Paul%20A.%20Giannoros.%20SAT%20Encodings%20of%20the%20At-Most-k%20Constraint%20-%20ModRef%202010.pdf
        """
        all_cells = self.board.get_all_cells()
        all_states = [self.gen_state_int(*coords, self.target_state)
                      for coords in all_cells]
        # it doesn't matter what order the cells are in, as long as its consistent
        first_cell = all_cells[0]
        first_state = self.additional_states[0]
        last_state = self.additional_states[-1]
        # first register must be true if the cell is true
        for cell in all_cells:
            clause = {self.gen_state_int(*cell, self.target_state): False,
                      self.gen_state_int(*cell, first_state): True}
            self.add_clause(clause)
        # only the first register in the first cell can be true
        for j in range(1, self.max_num):
            clause = {self.gen_state_int(*first_cell, self.additional_states[j]): False}
            self.add_clause(clause)
        # for all other cells, they must contain registers of previous cell
        for i in range(1, len(all_cells)-1):
            cur_cell = all_cells[i]
            prev_cell = all_cells[i-1]
            for reg_num, register in enumerate(self.additional_states):
                clause = {self.gen_state_int(*prev_cell, register): False,
                          self.gen_state_int(*cur_cell, register): True}
                self.add_clause(clause)
                # if the cell is filled, add to the register
                if reg_num > 0:
                    clause = {self.gen_state_int(*cur_cell, self.target_state): False,
                              self.gen_state_int(*prev_cell, self.additional_states[reg_num-1]): False,
                              self.gen_state_int(*cur_cell, register): True}
                    self.add_clause(clause)
        # no register can overflow, otherwise more than k would exist
        for i in range(1, len(all_cells)):
            cur_cell = all_cells[i]
            prev_cell = all_cells[i-1]
            clause = {self.gen_state_int(*cur_cell, self.target_state): False,
                      self.gen_state_int(*prev_cell, last_state): False}
            self.add_clause(clause)
        return None

    def add_formulas(self) -> None:
        # self.add_formulas_binomial()
        self.add_formulas_sequential()

class LinkAuxiliaryWithMainState(Rule):
    """
    Rule that requires any cell with an auxiliary state to also have the
    main state, and a cell with the main state to have at least one
    auxiliary state.
    """

    def __init__(self, board: Board, main_state: str, auxiliary_states: List[str]) -> None:
        self.main_state = main_state
        self.auxiliary_states = auxiliary_states
        states = [main_state] + auxiliary_states
        super().__init__(board, states)

    def add_formulas(self) -> None:
        for cell in self.board.get_all_cells():
            main_num = self.gen_state_int(*cell, self.main_state)
            alt_clause = {main_num: False}
            for aux_state in self.auxiliary_states:
                # auxiliary implies main
                aux_num = self.gen_state_int(*cell, aux_state)
                clause = {aux_num: False, main_num: True}
                self.add_clause(clause)
                alt_clause[aux_num] = True
            # main implies one of auxiliary
            self.add_clause(alt_clause)

class ConnectedDecreasingTree(Rule):
    """
    Rule requiring that all cells that share a state must be connected
    vertically or horizontally (but not diagonally). If the maximum size
    of the region is known, it can be provided; otherwise, the solver
    will use the total size of the grid. If the maximum size of the
    region is provided, this rule will not enforce it; make sure to
    use the `AtMostNInBoard` constraint.

    Generally, use `ConnectedRegionOfSizeN` if you want a region of a certain size.
    """

    def __init__(self, board, state_prefix, size=None):
        """
        Args:
            board: game board
            state_prefix: a valid state in the board that the rule will
                build auxiliary states off of
            size: the maximum size of the region (not enforced)
            seed: optional, a (row, col) tuple that is known to have this state
        """
        if size is None:
            size = board.height * board.width 
        self.size = size
        self.state_prefix = state_prefix
        states = [self.auxiliary_name(dist) for dist in range(size)]
        super().__init__(board, states, add_exclusive=True)

    def auxiliary_name(self, dist):
        return self.state_prefix + "_" + str(dist)

    def add_formulas(self):
        all_cells = self.board.get_all_cells()
        # enforce strictly decreasing tree to seed
        for dist in range(1, self.size):
            for central_cell in all_cells:
                clause = {self.gen_state_int(*central_cell, self.auxiliary_name(dist)): False}
                for adj_cell in self.board.get_adjacencies(*central_cell):
                    clause[self.gen_state_int(*adj_cell, self.auxiliary_name(dist-1))] = True
                self.add_clause(clause)
            
class ConnectedRegion(SuperRule):
    """
    Rule requiring that a region must be connected.
    `state_prefix` must be a valid state; in general, it will be the actual (visible)
    state that all the auxiliary states are built on.
    If `size` is specified, it will assume the region is at most `size` cells big,
    but it won't actually enforce it. Use `ConnectedRegionOfSizeAtMostN` instead.
    `seed` is an optional argument that can be specified if at least one cell
    is known to have the `state_prefix` state.
    """

    def __init__(self, board, state_prefix, size=None, seed=None):
        tree_rule = ConnectedDecreasingTree(board, state_prefix, size)
        zero_state_name = tree_rule.auxiliary_name(0)
        aux_states = tree_rule.states
        link_rule = LinkAuxiliaryWithMainState(board, state_prefix, aux_states)
        one_seed_rule = AtMostNInBoard(board, zero_state_name, 1)
        rules = [tree_rule, one_seed_rule, link_rule]
        if seed is not None:
            seed_rule = InitialAuxiliaryConditions(board, [seed], [True], zero_state_name)
            rules.append(seed_rule)
        super().__init__(rules)

class ConnectedRegionOfSizeAtMostN(SuperRule):
    """
    Rule requiring that a region must be connected and that
    it has size at most `size`.
    """

    def __init__(self, board, state_prefix, size, seed=None):
        connected_rule = ConnectedRegion(board, state_prefix, size, seed)
        size_rule = AtMostNInBoard(board, state_prefix, size)
        rules = [connected_rule, size_rule]
        super().__init__(rules)

class Nurikabe(SuperRule):
    """
    Describes the rules for the Nurikabe puzzle.
    The offical rules can be found here: https://puzz.link/rules.html?nurikabe
    """

    def __init__(self, board: Board, empty_state: str, filled_state: str) -> None:
        self.board = board
        self.empty_state = empty_state
        self.filled_state = filled_state
        rules, self.states = self.generate_rules()
        super().__init__(rules, add_exclusive=True) # TODO: also add the exclusive states

    def generate_rules(self) -> tuple[list[Rule], list[str]]:
        given_numbers = self.board.constraints["numbers"]
        remaining_size = self.board.height*self.board.width
        out = []
        seed_states = []
        id = 0
        for coords, num in given_numbers.items():
            id += 1
            state_prefix = self.empty_state + "r" + str(id) # name of the state
            seed_states.append(state_prefix)
            # each region takes a state name in seed_states, and must be size num
            region_rule = ConnectedRegionOfSizeAtMostN(self.board, state_prefix, size=num, seed=coords)
            out.append(region_rule)
            remaining_size -= num
            assert remaining_size >= 0
        # black squares are also connected 
        shaded_rule = ConnectedRegionOfSizeAtMostN(self.board, self.filled_state, size=remaining_size, seed=self.find_unshaded_seed())
        square_rule = NoTwoByTwoSquare(self.board, [self.filled_state])
        # an empty square must take one of the region-specific states, and vice versa
        link_rule = LinkAuxiliaryWithMainState(self.board, self.empty_state, seed_states)
        # regions must be separated from each other
        unshaded_disjunct_rule = NoAdjacenciesBetweenStates(self.board, seed_states)
        # a cell is either shaded or unshaded
        shaded_or_unshaded_rule = AtLeastOneOfStateInCell(self.board, [self.empty_state, self.filled_state])
        # each auxiliary unshaded region is exclusive
        exclusive_rule = Rule(self.board, seed_states, add_exclusive=True)
        out.extend([shaded_rule, square_rule, link_rule, shaded_or_unshaded_rule, unshaded_disjunct_rule, exclusive_rule])
        vis_states = [self.empty_state, self.filled_state]
        return out, vis_states

    def find_unshaded_seed(self):
        """
        Finds the first unshaded black square in the givens.
        Used to preseed the solver (optional).
        """
        for row_idx, row in enumerate(self.board.data):
            for col_idx, cell in enumerate(row):
                if cell == self.filled_state:
                    return (row_idx, col_idx)
        return None


class NurikabeBoard(Board):
    """
    Describes a board for the Nurikabe puzzle type.
    `board_data` is a 2d nested array of given cells that are
    known to be shaded or unshaded.
    `board_constraints` is a 2d nested array of cells with numbers.
    This is transformed to a dictionary with keys of (row, col) tuples
    and values the numerical value to put into the Nurikabe ruleset.
    """

    def __init__(self, board_data: BoardData, board_constraints: BoardData, visible_states: List[str]) -> None:
        self.raw_numbers = board_constraints
        constraints = {}
        constraints["numbers"] = self.transform_constraints(board_constraints)
        super().__init__(board_data, visible_states, constraints)

    def transform_constraints(self, board_constraints: BoardData) -> Dict[tuple[int, int], int]:
        out = {}
        for row_idx, row in enumerate(board_constraints):
            for col_idx, cell in enumerate(row):
                if cell is not None:
                    assert isinstance(cell, int)
                    out[(row_idx, col_idx)] = cell
        return out

if __name__ == "__main__":
    data_board = Board.gen_empty_board(4, 4)
    constraints_board = Board.gen_empty_board(4, 4)
    constraints_board[0][3] = 2
    constraints_board[3][0] = 3
    constraints_board[3][2] = 2
    simple_nurikabe = NurikabeBoard(data_board, constraints_board, [".", "x"])
    empty_state = "."
    filled_state = "x"
    puzzle = Nurikabe(simple_nurikabe, empty_state, filled_state)
    # puzzle = AtMostNInBoard(simple_nurikabe, "n", 3)
    # test_1 = AtMostNInBoard(simple_nurikabe, empty_state, 10)
    # test_2 = AtMostNInBoard(simple_nurikabe, filled_state, 10)
    # test_3 = Rule(simple_nurikabe, [empty_state, filled_state], add_exclusive=True)
    # test_4 = AtLeastOneOfStateInCell(simple_nurikabe, [empty_state, filled_state])
    nurikabe_solver = CNFSolver(simple_nurikabe, rules=[puzzle])
    pp(nurikabe_solver.formula)
    pp(nurikabe_solver.states)
    pp(nurikabe_solver.rules)
    pp(nurikabe_solver.exclusive_states_lookup)
    print("\n")
    sol = nurikabe_solver.solve(verbose=False, max_sols=1)
    for x in sol:
        # pp(x)
        solved = nurikabe_solver.generate_solved_board()
        print(solved)
    print(nurikabe_solver.state_map)





