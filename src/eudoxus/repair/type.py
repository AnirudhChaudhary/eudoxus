from typing import Dict, List, Set, Tuple

import z3

import eudoxus.ast.expression as e
import eudoxus.ast.module as m
import eudoxus.ast.node as n
import eudoxus.ast.proof as p
import eudoxus.ast.statement as s
import eudoxus.ast.type as t
from eudoxus.ast.node import Identifier, Node, Position
from eudoxus.repair.interface import Checker
from eudoxus.utils import foldl


def get_leafs(parent, mod):
    leafs = {}
    for name, cls in mod.__dict__.items():
        if (
            isinstance(cls, type)
            and issubclass(cls, parent)
            and cls.__module__ == mod.__name__
        ):
            leafs[name] = cls

    to_delete = set()
    for n1, c1 in leafs.items():
        for n2, c2 in leafs.items():
            if n1 != n2 and issubclass(c1, c2):
                to_delete.add(n2)

    for ni in to_delete:
        del leafs[ni]

    return leafs


class Universe:
    def __init__(self):
        self.symbol = z3.DeclareSort("Symbol")

        self.expr = z3.Datatype(e.Expression.__name__)
        self.type = z3.Datatype(t.Type.__name__)
        self.stmt = z3.Datatype(s.Statement.__name__)
        self.cmd = z3.Datatype(p.Command.__name__)
        self.mod = z3.Datatype(m.Module.__name__)

        self.expr_list = z3.Datatype(f"{e.Expression.__name__}_list")
        self.expr_list.declare("empty")
        self.expr_list.declare("cons", ("head", self.expr), ("tail", self.expr_list))

        self.type_list = z3.Datatype(f"{t.Type.__name__}_list")
        self.type_list.declare("empty")
        self.type_list.declare("cons", ("head", self.type), ("tail", self.type_list))

        self.stmt_list = z3.Datatype(f"{s.Statement.__name__}_list")
        self.stmt_list.declare("empty")
        self.stmt_list.declare("cons", ("head", self.stmt), ("tail", self.stmt_list))

        self.cmd_list = z3.Datatype(f"{p.Command.__name__}_list")
        self.cmd_list.declare("empty")
        self.cmd_list.declare("cons", ("head", self.cmd), ("tail", self.cmd_list))

        self.id_type_pair = z3.Datatype("id_type_pair")
        self.id_type_pair.declare("pair", ("id", self.symbol), ("type", self.type))

        self.symbol_set = z3.ArraySort(self.symbol, z3.BoolSort())

        self.id_expr_pair = z3.Datatype("id_expr_pair")
        self.id_expr_pair.declare("pair", ("id", self.symbol), ("expr", self.expr))

        self.id_expr_pair_list = z3.Datatype("id_expr_pair_list")
        self.id_expr_pair_list.declare("empty")
        self.id_expr_pair_list.declare(
            "cons", ("head", self.id_expr_pair), ("tail", self.id_expr_pair_list)
        )

        expr_leafs = get_leafs(e.Expression, e)
        type_leafs = get_leafs(t.Type, t)
        stmt_leafs = get_leafs(s.Statement, s)
        cmd_leafs = get_leafs(p.Command, p)
        mod_leafs = get_leafs(m.Module, m)

        def declare_from_leafs(leafs, adt):
            for name, cls in leafs.items():
                fields = []
                for field_name, field_type in cls.__annotations__.items():
                    if field_type == bool:
                        field_type = z3.BoolSort()
                    elif field_type == int:
                        field_type = z3.IntSort()
                    elif field_type == float:
                        field_type = z3.RealSort()
                    elif field_type == Identifier or field_type == str:
                        field_type = self.symbol
                    elif field_type == e.Expression:
                        field_type = self.expr
                    elif field_type == t.Type:
                        field_type = self.type
                    elif field_type == s.Statement:
                        field_type = self.stmt
                    elif field_type == p.Command:
                        field_type = self.cmd
                    elif field_type == List[e.Expression]:
                        field_type = self.expr_list
                    elif field_type == List[t.Type]:
                        field_type = self.type_list
                    elif field_type == List[s.Statement]:
                        field_type = self.stmt_list
                    elif field_type == List[p.Command]:
                        field_type = self.cmd_list
                    elif field_type == Set[n.Identifier]:
                        field_type = self.symbol_set
                    elif field_type == Set[Tuple[n.Identifier, t.Type]]:
                        field_type = self.symbol_set
                    elif field_type == List[Tuple[n.Identifier, e.Expression]]:
                        field_type = self.id_expr_pair_list
                    else:
                        raise NotImplementedError(
                            f"Unsupported field type {field_type} for {field_name}"
                        )
                    fields.append((field_name, field_type))
                adt.declare(name, *fields)

        declare_from_leafs(expr_leafs, self.expr)
        declare_from_leafs(type_leafs, self.type)
        declare_from_leafs(stmt_leafs, self.stmt)
        declare_from_leafs(cmd_leafs, self.cmd)
        declare_from_leafs(mod_leafs, self.mod)

        (
            self.mod,
            self.expr,
            self.type,
            self.stmt,
            self.cmd,
            self.expr_list,
            self.type_list,
            self.stmt_list,
            self.cmd_list,
            self.id_expr_pair,
            self.id_expr_pair_list,
        ) = z3.CreateDatatypes(
            self.mod,
            self.expr,
            self.type,
            self.stmt,
            self.cmd,
            self.expr_list,
            self.type_list,
            self.stmt_list,
            self.cmd_list,
            self.id_expr_pair,
            self.id_expr_pair_list,
        )


class TypeChecker(Checker):
    """
    Check if the types are correct.
    """

    def reason_to_weight(self, reason: str) -> int:
        match reason:
            case "hole":
                return 0
            case "bad_constant":
                return 1
            case "bad_type":
                return 5
            case other if other.startswith("bad_expr_"):
                depth = int(other.split("_")[2])
                return 10 + depth ^ 2
            case "hard":
                return 5000
            case "default":
                return 1
        raise NotImplementedError(f"Unsupported reason {reason}")

    def get_depth(self, expr: z3.AstRef):
        def get_depth_rec(expr, depth):
            if z3.is_const(expr):
                return depth
            else:
                return max(get_depth_rec(arg, depth + 1) for arg in expr.children())

        return get_depth_rec(expr, 0)

    def str_to_symbol(self, symbol):
        if symbol not in self.symbol_map:
            self.symbol_map[symbol] = self.fresh_constant(self.universe.symbol, symbol)
        return self.symbol_map[symbol]

    def encode(self, cls, pos, children) -> Node:
        # print("encoding: ", cls, pos, children)
        match cls:
            case m.Module:
                # Hard: type(spec') == bool
                # Soft: spec == spec'
                print("children: ", children)
                spec = children[9]
                spec_pos = self.z3_to_pos(spec)
                spec_depth = self.get_depth(spec)
                print("spec: ", spec)
                print("term to type: ", self.term_to_type)
                print("term to type spec: ", self.term_to_type(spec))
                self.add_soft_constraint(
                    self.term_to_type(spec) == self.universe.type.BooleanType,
                    spec_pos,
                    f"bad_expr_{spec_depth}",
                )
                return self.universe.mod.Module(*children)
            case n.Identifier:
                # Input: x
                # Output: x
                x = self.str_to_symbol(self.prefix + children[0])
                # by default, we assume that all symbols are terms or types
                # for enum vals we assert that they are neither with a stronger weight
                # the position is -1 so that we don't get a hole for violating this
                self.add_soft_constraint(
                    z3.Or(self.symbol_is_term(x), self.symbol_is_type(x)), -1, "default"
                )
                return x
            case t.IntegerType:
                # Input: int
                # Soft: int == int'
                # Output: int'
                i = self.universe.type.IntegerType
                ip = self.fresh_constant(self.universe.type, "IntegerTypeHole")
                self.add_soft_constraint(i == ip, pos, "bad_type")
                return ip
            case t.RealType:
                # Input: real
                # Soft: real == real'
                # Output: real'
                r = self.universe.type.RealType
                rp = self.fresh_constant(self.universe.type, "RealTypeHole")
                self.add_soft_constraint(r == rp, pos, "bad_type")
                return rp
            case t.BooleanType:
                # Input: bool
                # Soft: bool == bool'
                # Output: bool'
                bt = self.universe.type.BooleanType
                btp = self.fresh_constant(self.universe.type, "BooleanTypeHole")
                self.add_soft_constraint(bt == btp, pos, "bad_type")
                return btp
            case t.BitVectorType:
                # Input: BitVector(w)
                # Soft bvtp = BitVector(w)
                # Output: bvtp
                w = children[0]
                bvt = self.universe.type.BitVectorType(w)
                bvtp = self.fresh_constant(self.universe.type, "BitVectorTypeHole")
                self.add_soft_constraint(bvt == bvtp, pos, "bad_type")
                return bvtp
            case t.ArrayType:
                # Input: index, value
                # Soft atp = Array(index, value)
                # Output: atp
                index = children[0]
                value = children[1]
                at = self.universe.type.ArrayType(index, value)
                atp = self.fresh_constant(self.universe.type, "ArrayTypeHole")
                self.add_soft_constraint(at == atp, pos, "bad_type")
                return atp
            case t.EnumeratedType:
                # Input: Enum(c_1, ..., c_n)
                # Soft ep = Enum(c_1, ..., c_n)
                # Hard: type(app_c_i) = ep
                # Output: ep
                ground_values = children[0]

                variant_set = z3.K(self.universe.symbol, False)
                for c in ground_values:
                    variant_set = z3.Store(variant_set, c, True)

                enu = self.universe.type.EnumeratedType(variant_set)

                for c in ground_values:
                    app_c_i = self.universe.expr.EnumValue(c)
                    cpos = self.z3_to_pos(app_c_i)
                    self.add_soft_constraint(
                        self.term_to_type(app_c_i) == enu, cpos, "bad_expr_1"
                    )

                ep = self.fresh_constant(self.universe.type, "EnumeratedTypeHole")
                self.add_soft_constraint(ep == enu, pos, "bad_type")
                return ep
            case t.RecordType:
                # Input: Record(f_1: t_1, ..., f_n: t_n)
                # Soft rp = Record(f_1: t_1, ..., f_n: t_n)
                # Hard: type(f_i) = t_i
                # Output: rp
                fields = children[0]
                field_names = []
                field_set = z3.K(self.universe.symbol, False)
                for f in fields:
                    field_names.append(f[0])
                    fpos = self.z3_to_pos(f[1])
                    self.add_soft_constraint(
                        self.field_to_type(f[0]) == f[1], fpos, "bad_type"
                    )
                    field_set = z3.Store(field_set, f[0], True)
                rec = self.universe.type.RecordType(field_set)
                rp = self.fresh_constant(self.universe.type, "RecordTypeHole")
                self.add_soft_constraint(rp == rec, pos, "bad_type")
                return rp
            case t.SynonymType:
                # Input: n
                # Soft: symbol_to_type(n) == t'
                # Output: t'
                sym = children[0]
                self.add_soft_constraint(self.symbol_is_type(sym), pos, "hard")
                tp = self.fresh_constant(self.universe.type, "SynonymTypeHole")
                self.add_soft_constraint(
                    self.symbol_to_type(sym) == tp, pos, "bad_type"
                )
                return tp
            case s.Block:
                arg = foldl(
                    lambda x, y: self.universe.stmt_list.cons(y, x),
                    self.universe.stmt_list.empty,
                    children[0],
                )
                return self.universe.stmt.Block(arg)
            case s.Assignment:
                # Input: x = y;
                # Hard: type(x) == type(y)
                # Output: x = y;
                x = children[0]
                y = children[1]
                ypos = self.z3_to_pos(y)
                weight = self.get_depth(y)
                self.add_soft_constraint(
                    self.term_to_type(x) == self.term_to_type(y),
                    ypos,
                    f"bad_expr_{weight}",
                )
                return self.universe.stmt.Assignment(x, y)
            case s.LocalDecl | s.OutputDecl | s.InputDecl | s.SharedDecl:
                # Input: var x: t;
                # Hard: type(x) == t
                # Output: var x: t;
                xsym = children[0]
                self.add_soft_constraint(
                    self.symbol_is_term(xsym), self.z3_to_pos(xsym), "hard"
                )
                xapp = self.universe.expr.FunctionApplication(
                    xsym, self.universe.expr_list.empty
                )
                tz3 = children[1]
                tpos = self.z3_to_pos(tz3)
                tweight = self.get_depth(tz3)
                self.add_soft_constraint(
                    self.term_to_type(xapp) == tz3, tpos, f"bad_expr_{tweight}"
                )
                return self.universe.stmt.LocalDecl(xsym, tz3)
            case s.TypeDecl:
                # Input: type x = y;
                # Hard: synonym(x) = y;
                # Output: type x = y;
                x = children[0]
                y = children[1]
                xtype = self.symbol_to_type(x)
                ypos = self.z3_to_pos(y)
                yweight = self.get_depth(y)
                self.add_soft_constraint(xtype == y, ypos, f"bad_expr_{yweight}")
                self.add_soft_constraint(
                    self.symbol_is_type(x), self.z3_to_pos(x), "hard"
                )
                return self.universe.stmt.TypeDecl(x, y)
            case s.InstanceDecl:
                # Input: instance target: mod(pairs);
                target = children[0]
                mod = children[1]
                pairs = children[2]

                def to_pair(pair):
                    id = pair[0]
                    expr = pair[1]
                    return self.universe.id_expr_pair.pair(id, expr)

                arg = foldl(
                    lambda acc, z: self.universe.id_expr_pair_list.cons(
                        to_pair(z), acc
                    ),
                    self.universe.id_expr_pair_list.empty,
                    pairs,
                )
                return self.universe.stmt.InstanceDecl(target, mod, arg)
            case s.If:
                # Input: if c then t else e
                # Hard: type(c') == bool
                # Soft: c == c'
                # Output: if c' then t else e
                cz3 = children[0]
                tc3 = children[1]
                ez3 = children[2]
                cpos = self.z3_to_pos(cz3)
                cweight = self.get_depth(cz3)
                self.add_soft_constraint(
                    self.term_to_type(cz3) == self.universe.type.BooleanType,
                    cpos,
                    f"bad_expr_{cweight}",
                )
                return self.universe.stmt.If(cz3, tc3, ez3)
            case s.Assert:
                # Input: assert c
                # Hard: type(c) == bool
                # Output: assert c
                cz3 = children[0]
                cpos = self.z3_to_pos(cz3)
                cweight = self.get_depth(cz3)
                self.add_soft_constraint(
                    self.term_to_type(cz3) == self.universe.type.BooleanType,
                    cpos,
                    f"bad_expr_{cweight}",
                )
                return self.universe.stmt.Assert(cz3)
            case s.Assume:
                # Input: assume c
                # Hard: type(c) == bool
                # Output: assume c
                cz3 = children[0]
                cpos = self.z3_to_pos(cz3)
                cweight = self.get_depth(cz3)
                self.add_soft_constraint(
                    self.term_to_type(cz3) == self.universe.type.BooleanType,
                    cpos,
                    f"bad_expr_{cweight}",
                )
                return self.universe.stmt.Assume(cz3)
            case s.Havoc:
                # Input: havoc x
                # Output: havoc x
                x = children[0]
                return self.universe.stmt.Havoc(x)
            case s.Next:
                # Input: next i
                # TODO: constraints on instances
                # Output: next i
                i = children[0]
                return self.universe.stmt.Next(i)
            case e.IntegerValue:
                # Input: z
                # Hard: type(IntValue(z)) == int
                # Soft: z == z'
                # Output: z'
                z = children[0]
                zz3 = self.universe.expr.IntegerValue(z)
                zp = self.fresh_constant(self.universe.expr, str(z))
                self.add_soft_constraint(
                    self.term_to_type(zz3) == self.universe.type.IntegerType,
                    pos,
                    "bad_constant",
                )
                self.add_soft_constraint(zz3 == zp, pos, "bad_constant")
                return zp
            case e.RealValue:
                # Input: r
                # Hard: type(RealValue(r)) == real
                # Soft: r == r'
                # Output: r'
                r = children[0]
                rz3 = self.universe.expr.RealValue(r)
                rp = self.fresh_constant(self.universe.expr, str(r))
                self.add_soft_constraint(
                    self.term_to_type(rz3) == self.universe.type.RealType,
                    pos,
                    "bad_constant",
                )
                self.add_soft_constraint(rz3 == rp, pos, "bad_constant")
                return rp
            case e.BooleanValue:
                # Input: b
                # Hard: type(BoolVal(b)) == bool
                # Soft: b == b'
                # Output: b'
                b = children[0]
                bz3 = self.universe.expr.BooleanValue(b)
                bp = self.fresh_constant(self.universe.expr, str(b))
                self.add_soft_constraint(
                    self.term_to_type(bz3) == self.universe.type.BooleanType,
                    pos,
                    "bad_constant",
                )
                self.add_soft_constraint(bz3 == bp, pos, "bad_constant")
                return bp
            case e.BitVectorValue:
                # Input: v, w
                # Hard: type(BitVectorValue(v, w)) == BitVector(w)
                # Soft: v == v'
                # Soft: w == w'
                # Soft bv' = BitVectorValue(v', w')
                # Output: bv'
                v = children[0]
                w = children[1]
                bv = self.universe.expr.BitVectorValue(v, w)
                vp = self.fresh_constant(z3.IntSort(), str(v))
                wp = self.fresh_constant(z3.IntSort(), str(w))
                bvp = self.fresh_constant(self.universe.expr, str(bv))
                self.add_soft_constraint(
                    self.term_to_type(bv) == self.universe.type.BitVectorType(w),
                    pos,
                    "bad_constant",
                )
                self.add_soft_constraint(bv == bvp, pos, "bad_constant")
                self.add_soft_constraint(v == vp, pos, "bad_constant")
                self.add_soft_constraint(w == wp, pos, "bad_constant")
                return bvp
            case e.Add:
                # Input: x + y
                # Hard: type(x) == type(y)
                # Hard: type(x + y) == type(x)
                # Hard: type(x) == int | real | BitVector(w)
                # Output: x + y
                x = children[0]
                y = children[1]
                x_plus_y = self.universe.expr.Add(x, y)
                weight = max(self.get_depth(x), self.get_depth(y)) + 1
                self.add_soft_constraint(
                    self.term_to_type(x) == self.term_to_type(y),
                    pos,
                    f"bad_expr_{weight}",
                )
                self.add_soft_constraint(
                    self.term_to_type(x_plus_y) == self.term_to_type(x),
                    pos,
                    f"bad_expr_{weight}",
                )
                type_x = self.term_to_type(x)
                self.add_soft_constraint(
                    z3.Or(
                        type_x == self.universe.type.IntegerType,
                        type_x == self.universe.type.RealType,
                        self.universe.type.is_BitVectorType(type_x),
                    ),
                    pos,
                    f"bad_expr_{weight}",
                )
                return x_plus_y
            case e.Subtract:
                # Input: x - y
                # Hard: type(x) == type(y)
                # Hard: type(x - y) == type(x)
                # Hard: type(x) == int | real | BitVector(w)
                # Output: x - y
                x = children[0]
                y = children[1]
                x_minus_y = self.universe.expr.Subtract(x, y)
                weight = max(self.get_depth(x), self.get_depth(y)) + 1
                self.add_soft_constraint(
                    self.term_to_type(x) == self.term_to_type(y),
                    pos,
                    f"bad_expr_{weight}",
                )
                self.add_soft_constraint(
                    self.term_to_type(x_minus_y) == self.term_to_type(x),
                    pos,
                    f"bad_expr_{weight}",
                )
                type_x = self.term_to_type(x)
                self.add_soft_constraint(
                    z3.Or(
                        type_x == self.universe.type.IntegerType,
                        type_x == self.universe.type.RealType,
                        self.universe.type.is_BitVectorType(type_x),
                    ),
                    pos,
                    f"bad_expr_{weight}",
                )
                return x_minus_y
            case e.Negate:
                # Input: -x
                # Hard: type(-x) == type(x)
                # Hard: type(x) == int | real | BitVector(w)
                # Output: -x
                x = children[0]
                neg_x = self.universe.expr.Negate(x)
                weight = self.get_depth(x)
                self.add_soft_constraint(
                    self.term_to_type(neg_x) == self.term_to_type(x),
                    pos,
                    f"bad_expr_{weight}",
                )
                type_x = self.term_to_type(x)
                self.add_soft_constraint(
                    z3.Or(
                        type_x == self.universe.type.IntegerType,
                        type_x == self.universe.type.RealType,
                        self.universe.type.is_BitVectorType(type_x),
                    ),
                    pos,
                    f"bad_expr_{weight}",
                )
                return neg_x
            case e.Multiply:
                # Input: x * y
                # Hard: type(x) == type(y)
                # Hard: type(x * y) == type(x)
                # Hard: type(x) == int | real | BitVector(w)
                # Output: x * y
                x = children[0]
                y = children[1]
                x_times_y = self.universe.expr.Multiply(x, y)
                weight = max(self.get_depth(x), self.get_depth(y)) + 1
                self.add_soft_constraint(
                    self.term_to_type(x) == self.term_to_type(y),
                    pos,
                    f"bad_expr_{weight}",
                )
                self.add_soft_constraint(
                    self.term_to_type(x_times_y) == self.term_to_type(x),
                    pos,
                    f"bad_expr_{weight}",
                )
                type_x = self.term_to_type(x)
                self.add_soft_constraint(
                    z3.Or(
                        type_x == self.universe.type.IntegerType,
                        type_x == self.universe.type.RealType,
                        self.universe.type.is_BitVectorType(type_x),
                    ),
                    pos,
                    f"bad_expr_{weight}",
                )
                return x_times_y
            case e.Divide:
                # Input: x / y
                # Hard: type(x) == type(y)
                # Hard: type(x / y) == type(x)
                # Hard: type(x) == int | real | BitVector(w)
                # Output: x / y
                x = children[0]
                y = children[1]
                x_div_y = self.universe.expr.Divide(x, y)
                weight = max(self.get_depth(x), self.get_depth(y)) + 1
                self.add_soft_constraint(
                    self.term_to_type(x) == self.term_to_type(y),
                    pos,
                    f"bad_expr_{weight}",
                )
                self.add_soft_constraint(
                    self.term_to_type(x_div_y) == self.term_to_type(x),
                    pos,
                    f"bad_expr_{weight}",
                )
                type_x = self.term_to_type(x)
                self.add_soft_constraint(
                    z3.Or(
                        type_x == self.universe.type.IntegerType,
                        type_x == self.universe.type.RealType,
                        self.universe.type.is_BitVectorType(type_x),
                    ),
                    pos,
                    f"bad_expr_{weight}",
                )
                return x_div_y
            case e.Modulo:
                # Input: x % y
                # Hard: type(x) == type(y)
                # Hard: type(x % y) == type(x)
                # Hard: type(x) == int | real | BitVector(w)
                # Output: x % y
                x = children[0]
                y = children[1]
                x_mod_y = self.universe.expr.Modulo(x, y)
                weight = max(self.get_depth(x), self.get_depth(y)) + 1
                self.add_soft_constraint(
                    self.term_to_type(x) == self.term_to_type(y),
                    pos,
                    f"bad_expr_{weight}",
                )
                self.add_soft_constraint(
                    self.term_to_type(x_mod_y) == self.term_to_type(x),
                    pos,
                    f"bad_expr_{weight}",
                )
                type_x = self.term_to_type(x)
                self.add_soft_constraint(
                    # mod only works on bitvectors
                    self.universe.type.is_BitVectorType(type_x),
                    pos,
                    f"bad_expr_{weight}",
                )
                return x_mod_y
            case e.Equal:
                # Input: x == y
                # Hard: type(x) == type(y)
                # Hard: type(x == y) == bool
                # Output: x == y
                x = children[0]
                y = children[1]
                x_eq_y = self.universe.expr.Equal(x, y)
                weight = max(self.get_depth(x), self.get_depth(y)) + 1
                self.add_soft_constraint(
                    self.term_to_type(x) == self.term_to_type(y),
                    pos,
                    f"bad_expr_{weight}",
                )
                self.add_soft_constraint(
                    self.term_to_type(x_eq_y) == self.universe.type.BooleanType,
                    pos,
                    f"bad_expr_{weight}",
                )
                return x_eq_y
            case e.NotEqual:
                # Input: x != y
                # Hard: type(x) == type(y)
                # Hard: type(x != y) == bool
                # Output: x != y
                x = children[0]
                y = children[1]
                x_neq_y = self.universe.expr.NotEqual(x, y)
                weight = max(self.get_depth(x), self.get_depth(y)) + 1
                self.add_soft_constraint(
                    self.term_to_type(x) == self.term_to_type(y),
                    pos,
                    f"bad_expr_{weight}",
                )
                self.add_soft_constraint(
                    self.term_to_type(x_neq_y) == self.universe.type.BooleanType,
                    pos,
                    f"bad_expr_{weight}",
                )
                return x_neq_y
            case e.GreaterThan:
                # Input: x > y
                # Hard: type(x) == type(y)
                # Hard: type(x > y) == bool
                # Hard: type(x) == int | real | BitVector(w)
                # Output: x > y
                x = children[0]
                y = children[1]
                x_gt_y = self.universe.expr.GreaterThan(x, y)
                weight = max(self.get_depth(x), self.get_depth(y)) + 1
                self.add_soft_constraint(
                    self.term_to_type(x) == self.term_to_type(y),
                    pos,
                    f"bad_expr_{weight}",
                )
                self.add_soft_constraint(
                    self.term_to_type(x_gt_y) == self.universe.type.BooleanType,
                    pos,
                    f"bad_expr_{weight}",
                )
                type_x = self.term_to_type(x)
                self.add_soft_constraint(
                    z3.Or(
                        type_x == self.universe.type.IntegerType,
                        type_x == self.universe.type.RealType,
                        self.universe.type.is_BitVectorType(type_x),
                    ),
                    pos,
                    f"bad_expr_{weight}",
                )
                return x_gt_y
            case e.GreaterThanOrEqual:
                # Input: x >= y
                # Hard: type(x) == type(y)
                # Hard: type(x >= y) == bool
                # Hard: type(x) == int | real | BitVector(w)
                # Output: x >= y
                x = children[0]
                y = children[1]
                x_ge_y = self.universe.expr.GreaterThanOrEqual(x, y)
                weight = max(self.get_depth(x), self.get_depth(y)) + 1
                self.add_soft_constraint(
                    self.term_to_type(x) == self.term_to_type(y),
                    pos,
                    f"bad_expr_{weight}",
                )
                self.add_soft_constraint(
                    self.term_to_type(x_ge_y) == self.universe.type.BooleanType,
                    pos,
                    f"bad_expr_{weight}",
                )
                type_x = self.term_to_type(x)
                self.add_soft_constraint(
                    z3.Or(
                        type_x == self.universe.type.IntegerType,
                        type_x == self.universe.type.RealType,
                        self.universe.type.is_BitVectorType(type_x),
                    ),
                    pos,
                    f"bad_expr_{weight}",
                )
                return x_ge_y
            case e.LessThan:
                # Input: x < y
                # Hard: type(x) == type(y)
                # Hard: type(x < y) == bool
                # Hard: type(x) == int | real | BitVector(w)
                # Output: x < y
                x = children[0]
                y = children[1]
                x_lt_y = self.universe.expr.LessThan(x, y)
                weight = max(self.get_depth(x), self.get_depth(y)) + 1
                self.add_soft_constraint(
                    self.term_to_type(x) == self.term_to_type(y),
                    pos,
                    f"bad_expr_{weight}",
                )
                self.add_soft_constraint(
                    self.term_to_type(x_lt_y) == self.universe.type.BooleanType,
                    pos,
                    f"bad_expr_{weight}",
                )
                type_x = self.term_to_type(x)
                self.add_soft_constraint(
                    z3.Or(
                        type_x == self.universe.type.IntegerType,
                        type_x == self.universe.type.RealType,
                        self.universe.type.is_BitVectorType(type_x),
                    ),
                    pos,
                    f"bad_expr_{weight}",
                )
                return x_lt_y
            case e.LessThanOrEqual:
                # Input: x <= y
                # Hard: type(x) == type(y)
                # Hard: type(x <= y) == bool
                # Hard: type(x) == int | real | BitVector(w)
                # Output: x <= y
                x = children[0]
                y = children[1]
                x_le_y = self.universe.expr.LessThanOrEqual(x, y)
                weight = max(self.get_depth(x), self.get_depth(y)) + 1
                self.add_soft_constraint(
                    self.term_to_type(x) == self.term_to_type(y),
                    pos,
                    f"bad_expr_{weight}",
                )
                self.add_soft_constraint(
                    self.term_to_type(x_le_y) == self.universe.type.BooleanType,
                    pos,
                    f"bad_expr_{weight}",
                )
                type_x = self.term_to_type(x)
                self.add_soft_constraint(
                    z3.Or(
                        type_x == self.universe.type.IntegerType,
                        type_x == self.universe.type.RealType,
                        self.universe.type.is_BitVectorType(type_x),
                    ),
                    pos,
                    f"bad_expr_{weight}",
                )
                return x_le_y
            case e.And:
                # Input: x and y
                # Hard: type(x) == type(y) == bool
                # Hard: type(x and y) == bool
                # Output: x and y
                x = children[0]
                y = children[1]
                x_and_y = self.universe.expr.And(x, y)
                xweight = self.get_depth(x)
                yweight = self.get_depth(y)
                weight = max(xweight, yweight) + 1
                self.add_soft_constraint(
                    self.term_to_type(x) == self.universe.type.BooleanType,
                    self.z3_to_pos(x),
                    f"bad_expr_{xweight}",
                )
                self.add_soft_constraint(
                    self.term_to_type(y) == self.universe.type.BooleanType,
                    self.z3_to_pos(y),
                    f"bad_expr_{yweight}",
                )
                self.add_soft_constraint(
                    self.term_to_type(x_and_y) == self.universe.type.BooleanType,
                    pos,
                    f"bad_expr_{weight}",
                )
                return x_and_y
            case e.Or:
                # Input: x or y
                # Hard: type(x) == type(y) == bool
                # Hard: type(x or y) == bool
                # Output: x or y
                x = children[0]
                y = children[1]
                x_or_y = self.universe.expr.Or(x, y)
                xweight = self.get_depth(x)
                yweight = self.get_depth(y)
                weight = max(xweight, yweight) + 1
                self.add_soft_constraint(
                    self.term_to_type(x) == self.universe.type.BooleanType,
                    self.z3_to_pos(x),
                    f"bad_expr_{xweight}",
                )
                self.add_soft_constraint(
                    self.term_to_type(y) == self.universe.type.BooleanType,
                    self.z3_to_pos(y),
                    f"bad_expr_{yweight}",
                )
                self.add_soft_constraint(
                    self.term_to_type(x_or_y) == self.universe.type.BooleanType,
                    pos,
                    f"bad_expr_{weight}",
                )
                return x_or_y
            case e.Xor:
                # Input: x xor y
                # Hard: type(x) == type(y) == bool
                # Hard: type(x xor y) == bool
                # Output: x xor y
                x = children[0]
                y = children[1]
                x_xor_y = self.universe.expr.Xor(x, y)
                xweight = self.get_depth(x)
                yweight = self.get_depth(y)
                weight = max(xweight, yweight) + 1
                self.add_soft_constraint(
                    self.term_to_type(x) == self.universe.type.BooleanType,
                    self.z3_to_pos(x),
                    f"bad_expr_{xweight}",
                )
                self.add_soft_constraint(
                    self.term_to_type(y) == self.universe.type.BooleanType,
                    self.z3_to_pos(y),
                    f"bad_expr_{yweight}",
                )
                self.add_soft_constraint(
                    self.term_to_type(x_xor_y) == self.universe.type.BooleanType,
                    pos,
                    f"bad_expr_{weight}",
                )
                return x_xor_y
            case e.Implies:
                # Input: x implies y
                # Hard: type(x) == type(y) == bool
                # Hard: type(x implies y) == bool
                # Output: x implies y
                x = children[0]
                y = children[1]
                x_implies_y = self.universe.expr.Implies(x, y)
                xweight = self.get_depth(x)
                yweight = self.get_depth(y)
                weight = max(xweight, yweight) + 1
                self.add_soft_constraint(
                    self.term_to_type(x) == self.universe.type.BooleanType,
                    self.z3_to_pos(x),
                    f"bad_expr_{xweight}",
                )
                self.add_soft_constraint(
                    self.term_to_type(y) == self.universe.type.BooleanType,
                    self.z3_to_pos(y),
                    f"bad_expr_{yweight}",
                )
                self.add_soft_constraint(
                    self.term_to_type(x_implies_y) == self.universe.type.BooleanType,
                    pos,
                    f"bad_expr_{weight}",
                )
                return x_implies_y
            case e.Not:
                # Input: not x
                # Hard: type(x) == bool
                # Hard: type(not x) == bool
                # Output: not x
                x = children[0]
                not_x = self.universe.expr.Not(x)
                xweight = self.get_depth(x)
                weight = xweight + 1
                self.add_soft_constraint(
                    self.term_to_type(x) == self.universe.type.BooleanType,
                    self.z3_to_pos(x),
                    f"bad_expr_{xweight}",
                )
                self.add_soft_constraint(
                    self.term_to_type(not_x) == self.universe.type.BooleanType,
                    pos,
                    f"bad_expr_{weight}",
                )
                return not_x
            case e.Ite:
                # Input: ite(c, t, e)
                # Hard: type(c) == bool
                # Hard: type(t) == type(e)
                # Hard: type(ite(c, t, e)) == type(t)
                # Output: ite(c, t, e)
                cond = children[0]
                then_ = children[1]
                else_ = children[2]
                ite = self.universe.expr.Ite(cond, then_, else_)
                cweight = self.get_depth(cond)
                tweight = self.get_depth(then_)
                eweight = self.get_depth(else_)
                weight = max(cweight, tweight, eweight) + 1
                self.add_soft_constraint(
                    self.term_to_type(cond) == self.universe.type.BooleanType,
                    self.z3_to_pos(cond),
                    f"bad_expr_{cweight}",
                )
                self.add_soft_constraint(
                    self.term_to_type(then_) == self.term_to_type(else_),
                    pos,
                    f"bad_expr_{weight}",
                )
                self.add_soft_constraint(
                    self.term_to_type(ite) == self.term_to_type(then_),
                    pos,
                    f"bad_expr_{weight}",
                )
                return ite
            case e.FunctionApplication:
                f = children[0]
                arg = foldl(
                    lambda x, y: self.universe.expr_list.cons(y, x),
                    self.universe.expr_list.empty,
                    children[1],
                )
                self.add_soft_constraint(
                    self.symbol_is_term(f), self.z3_to_pos(f), "hard"
                )
                return self.universe.expr.FunctionApplication(f, arg)
            case e.EnumValue:
                # Input: c
                # Hard: type(c) is EnumType
                # Hard: type(c)[c] == True
                # Soft: c == c'
                # Output: c'
                csym = self.str_to_symbol(self.prefix + children[0])
                cvar = self.universe.expr.EnumValue(csym)
                ctype = self.term_to_type(cvar)

                self.add_soft_constraint(
                    self.universe.type.is_EnumeratedType(ctype),
                    pos,
                    f"bad_expr_{self.get_depth(cvar)}",
                )
                variants = self.universe.type.values(ctype)
                self.add_soft_constraint(
                    variants[csym], pos, f"bad_expr_{self.get_depth(cvar)}"
                )

                # it's neither a type nor a term
                self.add_soft_constraint(z3.Not(self.symbol_is_term(csym)), pos, "hard")
                self.add_soft_constraint(z3.Not(self.symbol_is_type(csym)), pos, "hard")

                cp = self.fresh_constant(self.universe.expr, "EnumValueHole")
                self.add_soft_constraint(cvar == cp, pos, "bad_constant")
                return cp
            case e.Forall | e.Exists:
                # Input: forall x: t. c
                # Hard: type(c) == bool
                # Hard: type(forall x: t. c) == bool
                # Hard: type(x) = t
                # Output: forall x: t. c
                x = children[0]
                self.add_soft_constraint(
                    self.symbol_is_term(x), self.z3_to_pos(x), "hard"
                )
                xapp = self.universe.expr.FunctionApplication(
                    x, self.universe.expr_list.empty
                )
                xt = children[1]

                c = children[2]
                q = (
                    self.universe.expr.Forall(x, xt, c)
                    if cls == e.Forall
                    else self.universe.expr.Exists(x, xt, c)
                )
                self.add_soft_constraint(
                    self.term_to_type(c) == self.universe.type.BooleanType,
                    self.z3_to_pos(c),
                    f"bad_expr_{self.get_depth(c)}",
                )
                self.add_soft_constraint(
                    self.term_to_type(q) == self.universe.type.BooleanType,
                    pos,
                    f"bad_expr_{self.get_depth(q)}",
                )
                self.add_soft_constraint(
                    self.term_to_type(xapp) == xt,
                    self.z3_to_pos(xt),
                    f"bad_expr_{self.get_depth(xt)}",
                )
                return q
            case e.ArrayStore:
                # Input: a[x] = y
                # Hard: type(a) == Array(type(x), type(y))
                # Hard: type(a[x] = y) == Array(t1, t2)
                # Output: a[x] = y
                a = children[0]
                x = children[1]
                y = children[2]
                a_x_eq_y = self.universe.expr.ArrayStore(a, x, y)
                a_type = self.term_to_type(a)
                x_type = self.term_to_type(x)
                y_type = self.term_to_type(y)
                self.add_soft_constraint(
                    a_type == self.universe.type.ArrayType(x_type, y_type),
                    pos,
                    f"bad_expr_{self.get_depth(a)}",
                )
                self.add_soft_constraint(
                    self.term_to_type(a_x_eq_y) == a_type,
                    pos,
                    f"bad_expr_{self.get_depth(a_x_eq_y)}",
                )
                return a_x_eq_y
            case e.ArraySelect:
                # Input: a[x]
                # Hard: type(a) == Array(type(x), type(a).element)
                # Hard: type(a[x]) == type(a).element
                # Output: a[x]
                a = children[0]
                x = children[1]
                a_x = self.universe.expr.ArraySelect(a, x)
                a_type = self.term_to_type(a)
                x_type = self.term_to_type(x)
                a_element_type = self.universe.type.element(a_type)
                self.add_soft_constraint(
                    a_type == self.universe.type.ArrayType(x_type, a_element_type),
                    pos,
                    f"bad_expr_{self.get_depth(a)}",
                )
                self.add_soft_constraint(
                    self.term_to_type(a_x) == a_element_type,
                    pos,
                    f"bad_expr_{self.get_depth(a_x)}",
                )
                return a_x
            case e.RecordSelect:
                # Input: r.f
                # Soft: rp = r
                # Soft: fp = f
                # Soft: rp.fp == x
                # Hard: type(rp) is RecordType
                # Hard: type(rp).fields(fp) == True
                # Hard: type(x) == type(fp)
                # Output: x
                r = children[0]
                rp = self.fresh_constant(self.universe.expr, "RecordHole")
                f = children[1]

                # it's neither a type nor a term
                self.add_soft_constraint(z3.Not(self.symbol_is_term(f)), pos, "hard")
                self.add_soft_constraint(z3.Not(self.symbol_is_type(f)), pos, "hard")

                fp = self.fresh_constant(self.universe.symbol, "FieldHole")
                x = self.fresh_constant(self.universe.expr, "RecordSelectHole")
                self.add_soft_constraint(
                    r == rp, self.z3_to_pos(r), f"bad_expr_{self.get_depth(r)}"
                )
                self.add_soft_constraint(f == fp, self.z3_to_pos(f), "bad_constant")
                self.add_soft_constraint(
                    x == self.universe.expr.RecordSelect(rp, fp),
                    pos,
                    f"bad_expr_{self.get_depth(f)}",
                )
                self.add_soft_constraint(
                    self.universe.type.is_RecordType(self.term_to_type(rp)),
                    pos,
                    f"bad_expr_{self.get_depth(r)}",
                )
                self.add_soft_constraint(
                    self.universe.type.fields(self.term_to_type(rp))[fp],
                    pos,
                    f"bad_expr_{self.get_depth(f)}",
                )
                self.add_soft_constraint(
                    self.term_to_type(x) == self.field_to_type(fp),
                    pos,
                    f"bad_expr_{self.get_depth(f)}",
                )
                return x
            case e.InstanceSelect:
                # TODO
                return self.universe.expr.InstanceSelect(children[0], children[1])
            case p.Block:
                arg = foldl(
                    lambda x, y: self.universe.cmd_list.cons(y, x),
                    self.universe.cmd_list.empty,
                    children[0],
                )
                return self.universe.cmd.Block(arg)
            case p.Induction:
                # Input: induction(k)
                # Output: induction(k)
                k = children[0]
                return self.universe.cmd.Induction(k)
            case t.HoleType:
                # Input: ??
                # Soft: ?? == ??'
                # Output: ??'
                hole = self.universe.type.HoleType
                holep = self.fresh_constant(self.universe.type, "HoleType")
                self.add_soft_constraint(hole == holep, pos, "hole")
                return holep
            case e.HoleExpr:
                # Input: ??
                # Soft: ?? == ??'
                # Output: ??'
                hole = self.universe.expr.HoleExpr
                holep = self.fresh_constant(self.universe.expr, "HoleExpr")
                self.add_soft_constraint(hole == holep, pos, "hole")
                return holep
            case e.Globally:
                # bt = self.universe.type.BooleanType
                # btp = self.fresh_constant(self.universe.type, "BooleanTypeHole")
                # self.add_soft_constraint(bt == btp, pos, "bad_type")
                # return btp
                return self.universe.expr.Globally(children[0])
            case s.HoleStmt:
                # Input: ??
                # Soft: ?? == ??'
                # Output: ??'
                hole = self.universe.stmt.HoleStmt
                holep = self.fresh_constant(self.universe.stmt, "HoleStmt")
                self.add_soft_constraint(hole == holep, pos, "hole")
                return holep
            case p.HoleCmd:
                # Input: ??
                # Soft: ?? == ??'
                # Output: ??'
                hole = self.universe.cmd.HoleCmd
                holep = self.fresh_constant(self.universe.cmd, "HoleCmd")
                self.add_soft_constraint(hole == holep, pos, "hole")
                return holep
            case n.HoleId:
                # return a fresh symbol
                return self.fresh_constant(self.universe.symbol, "HoleId")
            case _:
                raise NotImplementedError(f"Unsupported class {cls}")

    def z3_to_pos(self, z3expr):
        for pos, expr in self.pos_to_z3expr.items():
            if z3expr.eq(expr):
                return pos
        return None

    def z3_to_ast(self, z3expr, node, position) -> Node:
        def is_bool(x):
            return self.model.eval(
                self.universe.type.is_BooleanType(x), model_completion=True
            )

        def is_int(x):
            return self.model.eval(
                self.universe.type.is_IntegerType(x), model_completion=True
            )

        def is_real(x):
            return self.model.eval(
                self.universe.type.is_RealType(x), model_completion=True
            )

        def is_bv(x):
            return self.model.eval(
                self.universe.type.is_BitVectorType(x), model_completion=True
            )

        def is_enum(x):
            return self.model.eval(
                self.universe.type.is_EnumeratedType(x), model_completion=True
            )

        def is_record(x):
            return self.model.eval(
                self.universe.type.is_RecordType(x), model_completion=True
            )

        def is_array(x):
            return self.model.eval(
                self.universe.type.is_ArrayType(x), model_completion=True
            )

        # REPAIR RULES LIVE HERE
        match z3expr.sort():
            case self.universe.type:
                if is_bool(z3expr):
                    return t.BooleanType(position)
                if is_int(z3expr):
                    return t.IntegerType(position)
                if is_real(z3expr):
                    return t.RealType(position)
                elif is_bv(z3expr):
                    w = self.model.eval(self.universe.type.width(z3expr))
                    return t.BitVectorType(position, w)
                elif is_enum(z3expr):
                    # get all the variants that are assigned this type
                    variants = []
                    for name, value in self.symbol_map.items():
                        if self.model.eval(
                            z3.And(
                                self.universe.type.values(z3expr)[value],
                                z3.Not(self.symbol_is_term(value)),
                                z3.Not(self.symbol_is_type(value)),
                            )
                        ):
                            variants.append(
                                n.Identifier(position, name[len(self.prefix) :])
                            )
                    if len(variants) == 0:
                        variants = [n.HoleId(position)]
                    return t.EnumeratedType(position, set(variants))
                elif is_record(z3expr):
                    fields = []
                    for name, selector in self.symbol_map.items():
                        if self.model.eval(
                            z3.And(
                                self.universe.type.fields(z3expr)[selector],
                                z3.Not(self.symbol_is_term(selector)),
                                z3.Not(self.symbol_is_type(selector)),
                            )
                        ):
                            field_id = n.Identifier(position, name[len(self.prefix) :])
                            field_type = t.HoleType(position)
                            fields.append((field_id, field_type))
                    if len(fields) == 0:
                        fields = [(n.HoleId(position), t.HoleType(position))]
                    return t.RecordType(position, set(fields))
                elif is_array(z3expr):
                    element_type = t.HoleType(position)
                    index_type = t.HoleType(position)
                    return t.ArrayType(position, index_type, element_type)

            case self.universe.expr:
                new_type = self.term_to_type(z3expr)
                match node:
                    case e.BooleanValue(_, v) if is_int(new_type):
                        return e.IntegerValue(position, 1 if v else 0)
                    case e.BooleanValue(_, _) if is_bool(new_type):
                        return node
                    case e.IntegerValue(_, v) if is_bool(new_type):
                        return e.BooleanValue(position, False if v == 0 else True)
                    case e.IntegerValue(_, _) if is_int(new_type):
                        return node
                    case e.IntegerValue(_, v) if is_real(new_type):
                        return e.RealValue(position, str(v) + ".0")
                    case e.IntegerValue(_, v) if is_bv(new_type):
                        w = self.model.eval(self.universe.type.width(new_type))
                        return e.BitVectorValue(position, v, w)
                    case e.RealValue(_, v) if is_int(new_type):
                        return e.IntegerValue(position, int(v))

        return None

    def repair(self, cls, pos, children) -> Node:
        if pos in self.to_repair:
            z3expr = self.pos_to_z3expr[pos]
            node = self.pos_to_node[pos]
            new_node = self.z3_to_ast(z3expr, node, pos)
            if new_node is not None:
                self.to_repair[pos] = new_node

        return cls(pos, *children)

    def check(self, modules: List[m.Module]) -> List[Dict[Position, Node]]:
        self.universe = Universe()

        # to get the type of terms
        self.term_to_type = self.declare_function(
            "term_to_type", self.universe.expr, self.universe.type
        )

        # for type synonyms only
        self.symbol_to_type = self.declare_function(
            "symbol_to_type", self.universe.symbol, self.universe.type
        )

        # for record fields only
        self.field_to_type = self.declare_function(
            "field_to_type", self.universe.symbol, self.universe.type
        )

        self.symbol_is_term = self.declare_function(
            "symbol_is_term", self.universe.symbol, z3.BoolSort()
        )

        self.symbol_is_type = self.declare_function(
            "symbol_is_type", self.universe.symbol, z3.BoolSort()
        )

        self.symbol_map = {}

        self.pos_to_z3expr = {}
        self.pos_to_node = {}

        for module in modules:
            self.prefix = module.name.name + "_"

            def visit_and_save(cls, pos, children):
                node = cls(pos, *children)
                self.pos_to_node[pos] = node
                return node

            def encode_and_save(cls, pos, children):
                node = self.encode(cls, pos, children)
                self.pos_to_z3expr[pos] = node
                return node

            module.visit(visit_and_save)
            module.visit(encode_and_save)

        # make sure that all the symbols are unique
        symbols = [sym for sym in self.symbol_map.values()]
        if len(symbols) > 1:
            self.add_soft_constraint(
                z3.Distinct(symbols), modules[0].name.position, "hard"
            )

        # make sure that no symbol is both a term and a type
        for sym in self.symbol_map.values():
            self.add_soft_constraint(
                z3.Not(z3.And(self.symbol_is_term(sym), self.symbol_is_type(sym))),
                self.z3_to_pos(sym),
                "hard",
            )

        positions, self.model = self.solve()

        # print(f"Model: {self.model}")
        # print(f"Edits: {[self.pos_to_node[pos] for pos in positions]}")

        self.to_repair = {position: n.HoleId(position) for position in positions}

        for module in modules:
            self.prefix = module.name.name + "_"
            module.visit(self.repair)

        return [self.to_repair]
