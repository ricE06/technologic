# Contains boilerplate related to different
# rules in different puzzle types.
import math
from typing import Iterable, Any

class Rule():

    def __init__(self, board, states=None, add_exclusive=False):
        self.board = board # board with various attributes depending on puzzle
        self.states = states
        self.height, self.width = self.board.height, self.board.width
        self.add_exclusive = add_exclusive # add exclusive variables at this level
        self.linked_to_cnf = False

    def flatten_rules(self):
        return [self]

    def cnf_init(self, cnf_obj):
        """
        Creates a reference to the CNFSolver object it will generate rules for.
        """
        self.cnf = cnf_obj
        self.linked_to_cnf = True
        self.formula_contribution = {}

    def add_states_to_overall(self):
        """
        Adds any necessary cell states, and/or looks for states in the given list to use.
        Mutates state_list to add the new states.
        """
        cnf_state_list = self.cnf.states
        state_map = self.cnf.state_map
        idx = len(cnf_state_list)
        for remaining_state in self.states:
            if remaining_state not in cnf_state_list:
                state_map[remaining_state] = idx
                cnf_state_list.append(remaining_state)
                idx += 1
        return None

    def add_exclusive_states(self):
        """
        Adds groups of exclusive states to the cnf exclusive_states list.
        """
        if self.add_exclusive:
            self.cnf.exclusive_states.append([self.cnf.state_map[state] for state in self.states])
        return None

    def gen_state_int(self, row_idx, col_idx, state_name=None, state_num=None):
        return self.cnf.gen_state_int(row_idx, col_idx, state_name, state_num)

    def add_clause(self, clause):
        """
        Adds a clause to the formula and varmap dictionaries.
        Assumes there are no self conflicts (i.e. each clause contains
        each variable exactly once).
        
        Args:
            clause: a dictionary where each item is a variable
            to be solved for and each value is a boolean.
        """
        formula = self.cnf.formula
        var_map = self.cnf.var_map
        idx = len(formula)
        formula[idx] = clause
        self.formula_contribution[idx] = clause # for printing / debugging
        for var, literal in clause.items():
            temp = var_map.setdefault(var, {})
            temp.setdefault(literal, set()).add(idx)
        return None

    def add_formulas(self):
        pass

    def __repr__(self):
        return f"{self.__class__.__name__} over states {self.states} with rules:\n{self.formula_contribution}"

    @staticmethod
    def construct_subsets(inp: list[Any], n: int):
        """
        Given an iterable `inp`, returns a generator object yielding all
        subsets of `inp` of size `n` as tuples. Assumes that n is less than
        len(inp).
        """
        inplen = len(inp)
        idxs = list(range(n))
        max_idxs = tuple(range(inplen-n, inplen))
        total_subset_num = math.comb(inplen, n)
        for _ in range(total_subset_num):
            yield tuple(inp[idx] for idx in idxs)
            for meta_idx in range(n-1, -1, -1):
                idx = idxs[meta_idx]
                if idx >= max_idxs[meta_idx]:
                    continue
                idxs[meta_idx] = idx + 1
                for sub_idx in range(meta_idx+1, n):
                    idxs[sub_idx] = idx + sub_idx - meta_idx + 1
                break


class SuperRule():
    """
    A convenient grouping of multiple Rule objects,
    often of the same type / sharing similarites / sharing states.
    If `add_exclusive` is True, then it should be False for all subrules
    sharing the same states.
    """

    def __init__(self, rules, add_exclusive=False):
        self.rules = rules # list of Rule objects
        self.add_exclusive = add_exclusive

    def cnf_init(self, cnf_obj):
        self.cnf = cnf_obj
        for rule in self.rules:
            rule.cnf_init(cnf_obj)

    def flatten_rules(self):
        out = []
        for rule in self.rules:
            out.extend(rule.flatten_rules())
        return out

    def add_exclusive_states(self):
        if self.add_exclusive:
            self.cnf.exclusive_states.append([self.cnf.state_map[state] for state in self.states])
        for rule in self.flatten_rules():
            rule.add_exclusive_states()
        return None


if __name__ == "__main__":
    test_list = list(range(5))
    n = 4
    gen = Rule.construct_subsets(test_list, n)
    print(list(gen))




