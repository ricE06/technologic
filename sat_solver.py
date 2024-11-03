# Combines CNF constraints and actually solves the
# logic puzzles. Not fully optimized right now, but
# there are some optimizations related to the fact that
# we know these are grid based logic puzzles.

from rules import Rule
import sys
import copy
import pprint


class CNFSolver():

    def __init__(self, board, rules=[]):
        """
        Initiates the solver by linking all rules to this solver, combining the
        states into a centralized representation, and populating the CNF formulas
        (but not solving them yet).

        Args:
            board: board object to solve
            rules: list of Rule or SuperRule objects (or objects that inherit from Rule) that
                the solution must satisfy
        """
        self.rules = self.flatten_rules(rules) # list of rule objects
        self.formula = {} # dictionary of clause dictionaries
        self.var_map = {} # dictionary of variable dictionaries of clause_id sets for T/F
        self.board = board
        self.height, self.width = board.height, board.width
        self.states = [] # strings, indices correspond to internal int representation
        self.state_map = {}
        self.exclusive_states = [] # list of lists of integers
        # set up all the cnf formulas
        for rule in rules:
            rule.cnf_init(self)
        for rule in self.rules: # only atomic Rules do this, not SuperRules
            rule.add_states_to_overall()
        self.numstates = len(self.states)
        for rule in self.rules:
            rule.add_formulas()
        for rule in rules:
            rule.add_exclusive_states()
        self.exclusive_states_lookup = self.parse_exclusive_states()
        self.solution = None # unsolved for now

    def parse_exclusive_states(self):
        """
        Returns a dictionary of {state: ex_states} where ex_states points to an element
        of `self.exclusive_states` containing state.
        """
        out = {}
        for ex_states in self.exclusive_states:
            for state in ex_states:
                assert out.get(state, None) is None, "a state is in multiple exclusive sets"
                out[state] = ex_states
        return out

    def flatten_rules(self, rule_list):
        """
        Given a list of Rules and SuperRules, returns
        a list of only Rules are equivalent.
        """
        out = []
        for rule in rule_list:
            out.extend(rule.flatten_rules())
        return out

    def get_idx_and_state(self, var):
        """
        Returns a tuple of row_idx, col_idx, and state
        associated with a variable.
        """
        row_idx = var // (self.width*self.numstates)
        col_idx = var // self.numstates % self.width
        state = var % self.numstates
        return row_idx, col_idx, state

    def var_to_string(self, var):
        """
        Returns a string representation of the variable's location
        on the grid and the state that it is in.
        Variables are represented as a pair of coordinates and an
        integer describing their state, combined for a unique integer.
        """
        row_idx, col_idx, state_num = self.get_idx_and_state(var)
        state = self.states[state_num]
        return f"{row_idx}_{col_idx}_{state}"

    def gen_state_int(self, row_idx, col_idx, state_name=None, state_num=None):
        """
        Returns the variable associated with a grid cell being in a certain state
        as a unique integer. Either the state number can be provided, or the state
        name (which prompts a lookup into the state_map dictionary).
        """
        if state_num is None:
            state_num = self.state_map[state_name]
        assert state_num >= 0
        assert row_idx >= 0 and col_idx >= 0
        return (self.width*row_idx + col_idx)*self.numstates+state_num

    def find_exclusive_states(self, entry, already_subbed):
        """
        Given a variable that we set to True, checks if the state it represents is part of
        `self.exclusive_states`. If so, returns a set of all the
        vars that should be set to False. If not, returns a set containing itself.
        """
        var, literal = entry
        if not literal:
            return set((entry,)) if var not in already_subbed else set()
        row_idx, col_idx, state = self.get_idx_and_state(var)
        ex_states = self.exclusive_states_lookup.get(state, None)
        if ex_states is None:
            return set((entry,)) if var not in already_subbed else set()
        out_set = set()
        for sub_state in ex_states:
            new_var = self.gen_state_int(row_idx, col_idx, state_num=sub_state)
            if new_var in already_subbed:
                continue
            new_literal = literal if new_var == var else not literal
            out_set.add((new_var, new_literal))
        return out_set
        

    def solve(self, verbose=False, max_sols=100):
        """
        Solves the system. Returns a dictionary of {var: literal} if
        the CNF system is solvable, and None if not.

        Makes heavy use of self.formula and self.varmap. Their formats are as 
        follows:
            self.formula: an enumerated dictionary of clauses. Each clause is
                its own dictionary with {var: literal} pairs. 
            self.var_map: a dictionary with {var: dict} pairs. Each inner dictionary
                has two keys, one for True and one for False. Each value in
                the inner dictionary is a set containing the enumerated numbers
                of all the clauses var appears in associated with the literal.

        As an example, if we wanted to represent (a OR NOT b) AND (a OR b OR NOT c),
            self.formula would be
            {0: {a: True, b: False}, 1: {a: True, b: True, c: False}}
            and self.var_map would be
            {a: {True: {0, 1}, False: set()}, 
             b: {True: {1}, False: {0}}, 
             c: {True: set(), False: {1}}}.
        Notably, self.var_map doesn't necessarily have to contain both True/False keys.
        """
        print("Beginning new test")
        formula_dict, var_map = self.formula, self.var_map
        overall_solutions = [] # only modified if we know it works
        already_subbed = {} # modified as we go, set of vars that already substituted
        changed_visible = {}
        # first pass base cases
        if len(formula_dict) == 0:
            yield overall_out
            return
        for clause in formula_dict.values():
            if len(clause) == 0:
                yield None
                return

        def modify_formula_dict(inp_formula, inp_map, inp_entries):
            """
            Mutates the formula to reflect changes made upon substitution for the 
            first yield. First yield is True if instantly solvable, False if not,
            and None if neither. Second yield is to undo these changes 
            (for instance, if a certain case is unsolvable).
            """
            add_back_clauses = {}
            add_back_entries = {}
            add_back_inp_map = {}
            seen_subvars = {}
            flag = None
            # preprocessing with checking for exclusive states
            sub_entries = set()
            for entry in inp_entries:
                sub_entries.update(self.find_exclusive_states(entry, already_subbed))
            if verbose:
                print(f"{inp_entries=}")
            if not sub_entries:
                raise Exception
            if verbose: print(f"{sub_entries=}")
            for sub_var, sub_literal in sub_entries:
                if sub_var in already_subbed: 
                    continue
                # if sub_var in self.board.visible_states:
                if flag is False or sub_var in seen_subvars:
                    flag = False
                    break # second condition only possible if somehow we forced a variable to be true and false
                seen_subvars[sub_var] = sub_literal
                if inp_map.get(sub_var, None) is None:
                    continue
                for clause_id in inp_map[sub_var].get(sub_literal, set()):
                    target_clause = inp_formula.get(clause_id, None)
                    if target_clause is None:
                        continue
                    add_back_clauses[clause_id] = target_clause
                    del inp_formula[clause_id]  # still exists in add_back_clauses
                for clause_id in inp_map[sub_var].get(not sub_literal, set()):
                    target_clause = inp_formula.get(clause_id, None)
                    if target_clause is None:
                        continue
                    add_back_entries.setdefault(clause_id, []).append(
                        (sub_var, not sub_literal)
                    )
                    del inp_formula[clause_id][sub_var]
                    if not inp_formula[clause_id]:
                        if verbose: print(f"Contradiction found at clause #{clause_id}")
                        flag = False  # impossible, short circuit asap
                        break
                add_back_inp_map[sub_var] = inp_map[sub_var]
                del inp_map[sub_var]
            seen_subvars[sub_var] = sub_literal
            already_subbed.update(seen_subvars)
            if not inp_formula and flag is not False:
                flag = True
            yield flag
            # assert num_entries_deleted == sum(len(clause_entries) for clause_entries in add_back_entries.values())
            # second half of the function, now replaces everything
            for sub_var in seen_subvars:
                del already_subbed[sub_var]
            for var, var_map in add_back_inp_map.items():
                inp_map[var] = var_map
            for clause_id, clause in add_back_clauses.items():
                inp_formula[clause_id] = clause
            for clause_id, entries in add_back_entries.items():
                for entry in entries:
                    inp_formula.setdefault(clause_id, {})[entry[0]] = entry[1]
            yield

        def satisfying_helper_dict(calls_made=0, state="guess", forcing=False):
            """
            Recursive helper function for the dictionary representation.
            """
            if verbose:
               print(f"Substituting at depth #{calls_made}, {state}, {forcing=}")
            if len(overall_solutions) >= max_sols:
                return None

            def get_one_item(dic, unit=True):
                """
                Finds any key, value pair from dic, and then finds
                all of the exclusive states to add as well.
                Returns a set of (var, literal) pairs.
                """
                for key, value in dic.items():
                    entry = key, value
                    return (key, value)
                if unit:
                    return self.find_exclusive_states(entry, already_subbed) 
                return self.find_exclusive_states(entry, already_subbed), entry

            if not formula_dict:
                return True
            unit_clauses = set()
            clause = None
            forcing = False
            for clause in formula_dict.values():
                if len(clause) == 1:
            #         print(f"{clause}")
                    unit_clauses.add(get_one_item(clause))
                    forcing = True
                if len(clause) == 0:
                    print("what")
                    input()
                    return False
            clauses_to_sub = unit_clauses if unit_clauses else set((get_one_item(clause),))
            # kept_formula = copy.deepcopy(formula_dict)
            # kept = copy.deepcopy(already_subbed)
            mutate_gen = modify_formula_dict(formula_dict, var_map, clauses_to_sub)
            gen_out = next(mutate_gen)
            if gen_out is True:
                sol = copy.deepcopy(already_subbed)
                overall_solutions.append(sol)
                if verbose: 
                    print("-------SOLUTION FOUND-----------------------------------------------------")
                    input()
                next(mutate_gen)
                return True
            if gen_out is None and satisfying_helper_dict(calls_made+1, "guess", forcing) and forcing:
                # pass
                if verbose: print(f"Direct backtracking at depth #{calls_made}...")
                next(mutate_gen)
                return True
            if verbose: print(f"Resubstituting at depth #{calls_made}...")
            next(mutate_gen)  # this failed, so we revert the formula
            # assert formula_dict.keys() == kept_formula.keys(), str(set(formula_dict) ^ set(kept)) + str(pass_times)
            # assert already_subbed == kept, str(set(kept.keys())-set(already_subbed.keys())) + str(set(already_subbed.keys())-set(kept.keys()))
            if forcing:
                return False  # current subs don't work, no alternatives
            tup_clause = tuple(clauses_to_sub)
            clause_alt = [(tup_clause[0][0], not tup_clause[0][1])]
            mutate_gen_alt = modify_formula_dict(formula_dict, var_map, clause_alt)
            gen_out_alt = next(mutate_gen_alt)
            if gen_out_alt is True:
                next(mutate_gen_alt)
                return True
            if gen_out_alt is None and satisfying_helper_dict(calls_made+1, "guess_alt"):
                if verbose: print(f"Direct backtracking at depth #{calls_made} as both options were considered...")
                next(mutate_gen_alt)
                return True
            next(mutate_gen_alt)  # this failed, so we revert the formula
            if verbose: print(f"Backtracking at depth #{calls_made} as this path failed...")
            return False

        satisfying_helper_dict()
        if overall_solutions:
            if len(overall_solutions) >= 100:
                print("Warning: search terminated after finding 100 solutions")
#             assert overall_out.keys() == already_subbed
            print(f"{len(overall_solutions)} solution(s) found.")
            for solution in overall_solutions:
                self.solution = solution
                yield self.solution
            print(f"No more solutions found")
            return
#             return overall_out
        print("No solutions found")
        self.solution = None
        yield None

    def generate_solved_board(self):
        new_board = copy.deepcopy(self.board)
        if self.solution is None:
            return new_board
        data = new_board.data
        for var, literal in self.solution.items():
            if not literal:
                continue
            row_idx, col_idx, state_num = self.get_idx_and_state(var)
            state = self.states[state_num]
            new_board.add_state_to_board(row_idx, col_idx, state)
        return new_board


if __name__ == "__main__":
    formula = {0: {'a': True, 'b': True}, 1: {'a': False, 'b': False, 'c': True}, 2: {'b': True, 'c': True}, 3: {'b': True, 'c': False}, 4: {'a': False, 'b': False, 'c': False}}
    var_map = {'a': {True: {0}, False: {1, 4}}, 'b': {True: {0, 2, 3}, False: {1, 4}}, 'c': {True: {1, 2}, False: {3, 4}}}
    solver = CNFSolver(1, 1, [])
    solver.formula = formula
    solver.var_map = var_map
    print(solver.solve())
