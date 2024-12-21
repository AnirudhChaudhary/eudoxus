from typing import Dict, List, Tuple

import eudoxus.ast.expression as e
import eudoxus.ast.module as m
import eudoxus.ast.node as n
import eudoxus.ast.statement as s
import eudoxus.ast.type as t
from eudoxus.ast.node import HoleId, Node, Position
from eudoxus.repair.interface import Checker


class LTLChecker(Checker):
    """
    Checks to make sure LTL is all defined in the correct spots.
    """

    def visit_ltl(self, cls, pos, children):
        """
        Will nodes and determine whether LTL should be valid in that spot or not.
        """
        # if allow LTL then if you see an LTL expression keep it, or else add the pos and cls to the rewrite list

        # print("cls: ", cls)
        # if cls in (s.InputDecl, s.LocalDecl):
        #     self.recent_decl_pos = pos

        # if isinstance(cls, s.Declaration):
        #     self.recent_decl_pos = pos
        if cls == n.Identifier:
            if children[0] == "Globally":
                print(
                    f"AHHHHHH GLOBALLY so the closest parent to {pos} needs to be rewritten"
                )
                self.needs_rewrite.append(pos)
                # self.rewrites[pos] = HoleId(pos)

        if cls == e.Globally:
            if pos not in self.position_mappings[self.allowed_pos[0]]:
                print(
                    "i found a globally that was defined in the ast that I don't like"
                )
                # TODO: May need to handle the rewriting here separately
                self.rewrites[pos] = HoleId(pos)

        """
        be careful in the future, you may run into a case where you have the "Globally" come
        as an expression but that should not be allowed.
        Right now we have a situation where, in bad cases, globally comes as an identifier.
        However globally gets properly parsed in the returns bc
        it has some good syntax. There may be a case where the globally comes inside
        something like an assert, gets properly classified but not caught
        by this checker because right now we only look for Identifiers.
        """

        # if pos in self.allowed_pos:
        #     self.allowed_pos.append(children[0][0])

        # print("allowed pos: ", self.allowed_pos)

        return (pos, *children)

    def find_best_rewritable_parent(self, cls, pos, children):
        """
        This function has to execute after we go through the AST and visit to find all incorrect occurences of LTL
        Right now we are just looking at declared cases where there has been a declaration.

        Input:
        - parent_mapping
        - child_mapping
        - occurences of LTL

        Output:
        - mapping between where LTL occured, and what parent should be rewritten
        """

        # we have the parent mapping
        print(f"cls: {cls} Decl = ? {cls == s.InputDecl}")

        # Go through all the flagged positions who's parents we need to search
        for _pos in self.potential_parents_to_rewrite:
            # go through all possible potential parents

            # establishes all of the positions that should have a replaced parent
            for par_pos in self.potential_parents_to_rewrite[_pos]:
                print(f"pos {pos} | _pos {_pos} | par_pos {par_pos}")
                # if the parent position is the same as the position
                if par_pos == pos:
                    # and that it is the smallest
                    if _pos not in self.best_replacable_parent:
                        # this line is suspicious because unless it's an inputDecl, then it won't work
                        if issubclass(cls, s.Declaration):
                            print("changed best replacable parent to: ", par_pos)
                            self.best_replacable_parent[_pos] = par_pos
                        else:
                            continue

                    if len(self.position_mappings[par_pos]) < len(
                        self.position_mappings[self.best_replacable_parent[_pos]]
                    ):
                        # , s.VariableDecl, s.LocalDecl, s.OutputDecl, s.SharedDecl, s.TypeDecl, s.InstanceDecl):
                        if issubclass(cls, s.Declaration):
                            self.best_replacable_parent[_pos] = par_pos
                            print("changed best replacable parent")
        return (pos, *children)

    def pull_from_tuple(self, _tuple):
        """
        Pulls positions from tuple.
        """
        final_pos_list = []
        for elem in _tuple:
            if isinstance(elem, Position):
                final_pos_list.append(elem)
            elif isinstance(elem, tuple):
                final_pos_list.extend(self.pull_from_tuple(elem))
            elif isinstance(elem, list):
                if elem != []:
                    hidden_tuple = elem[0]
                    if isinstance(hidden_tuple, tuple):
                        final_pos_list.extend(self.pull_from_tuple(hidden_tuple))
        return final_pos_list

    def unpeel_list(self, _list):
        """
        Takes a list and unpeels it
        """
        return _list[0]

    def map_children(self, cls, pos, children):
        children_pos = []
        # print("new_call: ", pos, children)

        # base case
        if children == []:  # []
            return (pos, *children)

        # peel layers of list
        original_children_copy = children.copy()
        if type(children[0]) == list:  # peel the onion layers
            children = children[
                0
            ]  # operating on assumption that we don't have list of lists,
            # but just one list inside another list at max
            if children == []:  # [[]]
                return (pos, *children)

        # at this point we should only have elements nested in one list
        # print("children after peeling: ", children)
        for child in children:
            if isinstance(child, Position):
                children_pos.append(child)

            if isinstance(child, tuple):
                children_pos.extend(self.pull_from_tuple(child))

        # print(f"mapping {pos} to {children_pos}")
        self.position_mappings[pos] = children_pos
        return (pos, *original_children_copy)

    def map_parents(self):
        """
        This is a map that will store the parents for Position.
        Use Case: We have an identifier that we want to replace but
          it doesn't have a `target` attribute which is needed for rewriting.
          So we need to go up the tree to find the parent with the target attribute.
        This function is only responsible for finding the parents

        We start with a map (position mappings) that looks like:
        {
            Position(unique=1) : [Position(unique=2), Position(unique=3)]
            Position(unique=2) : [Position(unique=3)]
        }

        """
        for parent_pos in self.position_mappings:
            for child_pos in self.position_mappings[parent_pos]:
                if child_pos not in self.parents_mapping:
                    self.parents_mapping[child_pos] = set()
                if (
                    parent_pos not in self.parents_mapping
                ):  # this is to handle the one edge case of the root
                    self.parents_mapping[parent_pos] = set()
                self.parents_mapping[child_pos].add(parent_pos)

        # the code beneath is to handle adding your parents parent
        # current error: set size changed during iteration
        # fixed_point = False
        # while not fixed_point:
        #     fixed_point = True
        #     for child_pos in self.parents_mapping:
        #         original_len = len(self.parents_mapping[child_pos])
        #         for parent_pos in self.parents_mapping[child_pos]:
        #             for grandparent_pos in self.parents_mapping[parent_pos]:
        #                 if grandparent_pos not in self.parents_mapping:
        #                     self.parents_mapping[grandparent_pos] = set()
        #                 self.parents_mapping[child_pos].add(grandparent_pos)
        #         if len(self.parents_mapping[child_pos]) != original_len:
        #             fixed_point = False

        # convert to a list but not exactly sure if I need this yet, but it's here for now
        for pos in self.parents_mapping:
            self.parents_mapping[pos] = list(self.parents_mapping[pos])

        return

    def check(self, modules: List[m.Module]) -> Tuple[List[Dict[Position, Node]]]:
        """
        check is called on all of the modules and will contain
        ast's that we have to travers. Visit is the helper function that will go through
        and call visit_ltl
        """
        # print("doing the LTL CHECKER")
        self.rewrites = {}
        self.allow_LTL = False
        self.position_mappings = {}
        self.recent_decl_pos = None
        self.parents_mapping = {}
        self.needs_rewrite = []
        self.potential_parents_to_rewrite = {}
        self.best_replacable_parent = {}

        for module in modules:
            # mapping children
            # print("module: ", module)
            module.visit(self.map_children)
            self.map_parents()
            print("child mappings: ", self.position_mappings)
            # print("parents mapping: ", self.parents_mapping)
            # print("position mappings: ", self.position_mappings)

            # at this point we have the tree structure created with the corresponding children
            # we need a way to determine where the specification is
            if isinstance(
                module.specification, e.BooleanValue
            ):  # usually this means that specification is not defined
                self.allowed_pos = []
            else:
                self.allowed_pos = [module.specification.position]

            # print("starting allowed pos: ", self.allowed_pos)
            module.visit(self.visit_ltl)

            for pos in self.needs_rewrite:
                self.potential_parents_to_rewrite[pos] = self.parents_mapping[pos]

            module.visit(self.find_best_rewritable_parent)
            print("best replacable parents: ", self.best_replacable_parent)

            # for attr in ("init","inputs","instances","is_empty","locals","name"
            # ,"next","outputs","position","sharedvars","specification","traverse",
            # "types","visit","control"):
            for attr in dir(module):
                if "_" in attr:
                    continue
                else:
                    for _pos in self.best_replacable_parent:
                        # print("rewriting: ", rewrite_pos)
                        # print("module.inputs: ", module.inputs)
                        # if isinstance(module.inputs, s.Block):
                        #     print("input attr: ", dir(module.inputs))
                        rewrite_pos = self.best_replacable_parent[_pos]
                        for item in module.inputs.statements:
                            # print("item: ", item)
                            if "position" in dir(item):
                                if item.position == rewrite_pos:
                                    self.rewrites[rewrite_pos] = s.InputDecl(
                                        rewrite_pos,
                                        target=item.target,
                                        type=t.HoleType(position=item.type.position),
                                    )

            print("rewrites: ", self.rewrites)
            # print("ending allowed pos: ", self.allowed_pos)

        return [self.rewrites]
