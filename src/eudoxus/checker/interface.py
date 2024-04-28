from typing import Dict, List, Tuple

import z3

from eudoxus.ast.module import Module
from eudoxus.ast.node import Node, Position, pos2str, str2pos


class Checker:
    def __init__(self) -> None:
        self.solver_reset()
        self.hard_constraints = []
        self.soft_constraints = {}

    def solver_reset(self):
        z3.set_option("smt.random_seed", 0)
        self.solver = z3.Solver()
        self.solver.set(unsat_core=True)

    def check(self, modules: List[Module]) -> Dict[Position, Node]:
        raise NotImplementedError("Implement this method in a subclass!")

    def declare_sort(self, name: str) -> z3.SortRef:
        return z3.DeclareSort(name)

    def declare_function(self, name: str, *args: z3.SortRef) -> z3.FuncDeclRef:
        return z3.Function(name, *args)

    def declare_constant(self, name: str, sort: z3.SortRef) -> z3.ExprRef:
        return z3.Const(name, sort)

    def fresh_constant(self, sort: z3.SortRef, prefix="") -> z3.ExprRef:
        return z3.FreshConst(sort, prefix)

    def add_hard_constraint(self, constraint: z3.ExprRef) -> None:
        self.hard_constraints.append(constraint)

    def add_all_diff_hard(self, terms: List[z3.ExprRef]) -> None:
        self.add_hard_constraint(z3.Distinct(*terms))

    def add_soft_constraint(self, constraint: z3.ExprRef, pos: Position) -> None:
        if pos not in self.soft_constraints:
            self.soft_constraints[pos] = []

        self.soft_constraints[pos].append(constraint)

    def add_conflict(self, pos: Position) -> None:
        self.add_soft_constraint(z3.BoolVal(False), pos)

    def solve(self) -> Tuple[List[Position], z3.ModelRef]:
        """
        Check the constraints and return the list of positions that need to be
        changed and a model for inference.
        """

        result = z3.unsat
        positions = []

        while result != z3.sat:
            self.solver_reset()
            for constraint in self.hard_constraints:
                self.solver.add(constraint)
            for pos, constraints in self.soft_constraints.items():
                for i, constraint in enumerate(constraints):
                    pos_name = f"{pos2str(pos)}::{i}"
                    if pos_name in positions:
                        continue
                    self.solver.assert_and_track(constraint, pos_name)

            result = self.solver.check()
            match result:
                case z3.sat:
                    positions = [str2pos(p.split("::")[0]) for p in positions]
                    model = self.solver.model()
                    return positions, model
                case z3.unsat:
                    core = self.solver.unsat_core()
                    if len(core) == 0:
                        raise ValueError("If unsat, there must be a core!")
                    core = sorted([str(c) for c in core])
                    positions.append(core[0])
                case _:
                    raise ValueError("Must be sat or unsat!")

    def solve_maxres(self) -> Tuple[List[Position], z3.ModelRef]:
        """
        Check the constraints and return the list of positions that need to be
        changed and a model for inference.
        """

        result = z3.unsat
        positions = []

        conj_soft_constraints = {
            pos: z3.And(*constraints)
            for pos, constraints in self.soft_constraints.items()
        }

        live_constraints = {pos2str(pos): c for pos, c in conj_soft_constraints.items()}

        while result != z3.sat:
            self.solver_reset()
            for constraint in self.hard_constraints:
                self.solver.add(constraint)
            # After applying MaxRes
            for name, constraint in live_constraints.items():
                self.solver.assert_and_track(constraint, name)

            result = self.solver.check()
            match result:
                case z3.sat:
                    model = self.solver.model()
                    positions = [
                        pos
                        for pos, cons in conj_soft_constraints.items()
                        if not model.evaluate(cons)
                    ]
                    return positions, model
                case z3.unsat:
                    core = self.solver.unsat_core()
                    if len(core) == 0:
                        raise ValueError("If unsat, there must be a core!")
                    core = sorted([str(c) for c in core])
                    non_core_constraints = {
                        name: cons
                        for name, cons in live_constraints.items()
                        if name not in core
                    }
                    if len(core) == 1:
                        live_constraints = non_core_constraints
                    else:
                        maxres_constraints = []
                        prefix = z3.BoolVal(core[0])
                        for clause in core[1:]:
                            new_clause = z3.Or(prefix, live_constraints[clause])
                            prefix = z3.And(prefix, live_constraints[clause])
                            maxres_constraints.append((str(new_clause), new_clause))
                        live_constraints = non_core_constraints
                        live_constraints.update(
                            {name: cons for (name, cons) in maxres_constraints}
                        )
                case _:
                    raise ValueError("Must be sat or unsat!")
