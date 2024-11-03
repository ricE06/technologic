# class for representing game state

from typing import Optional, List, Tuple

BoardData = list[list[str | int | None]]

class Board():

    def __init__(self, data: BoardData, 
                 visible_states: Optional[List[str]] = None, 
                 constraints: Optional[dict] = None):
        """
        Creates a board. Data is a 2D nested list where
        each sublist is a row, and each entry in a sublist is either
        a string representing initial state or None. Assumes data has
        at least size 1x1 and is rectangular.
        """
        self.data = data
        self.height = len(data)
        self.width = len(data[0])
        if visible_states is None:
            visible_states = []
        self.visible_states = visible_states
        if constraints is None:
            constraints = {}
        self.constraints = constraints

    def __repr__(self):
        return "\n".join(str(row) for row in self.data)

    def add_state_to_board(self, row_idx, col_idx, state_name):
        if state_name in self.visible_states:
            self.data[row_idx][col_idx] = state_name

    def find_all_distinct_states(self):
        out = []
        for row in self.data:
            for cell in row:
                if cell is not None and cell not in out:
                    out.append(cell)

    def check_cell_in_bounds(self, row, col):
        """
        Returns True if the (row, col) exists within the board, and
        False otherwise.
        """
        return 0 <= row < self.height and 0 <= col < self.width

    def get_all_cells(self) -> list[tuple[int, int]]:
        """
        Returns a list of (row, col) tuples for every single
        cell in the board.
        """
        return [(row, col) for row in range(self.height) for col in range(self.width)]

    def get_adjacencies(self, row, col):
        """
        Returns a list of (row_idx, col_idx) tuples that are adjacent to (row, col).
        Adjacent tuples must be within bounds.
        """
        to_add = [(row+1, col), (row-1, col), (row, col+1), (row, col-1)]
        out = []
        for coords in to_add:
            if self.check_cell_in_bounds(*coords): 
                out.append(coords)
        return out
        
    @staticmethod
    def gen_empty_board(height: int, width: int) -> BoardData:
        return [[None for _ in range(width)] for _ in range(height)]
