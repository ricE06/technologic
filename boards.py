# class for representing game state

class Board():

    def __init__(self, data, visible_states=[], constraints=[]):
        """
        Creates a board. Data is a 2D nested list where
        each sublist is a row, and each entry in a sublist is either
        a string representing initial state or None. Assumes data has
        at least size 1x1 and is rectangular.
        """
        self.data = data
        self.height = len(data)
        self.width = len(data[0])
        self.visible_states = visible_states
        self.constraints = constaints

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
