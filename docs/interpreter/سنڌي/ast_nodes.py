# -*- coding: utf-8 -*-
"""
سنڌي (SindhiScript) — Abstract Syntax Tree (AST) Nodes
"""
import json
from typing import List, Optional, Union, Any


class ASTNode:
    def __init__(self, line: int = 1, col: int = 1):
        self.line = line
        self.col = col

    def to_dict(self) -> dict:
        """Convert AST node to a dictionary for easy inspection/serialization."""
        d = {"_type": self.__class__.__name__, "line": self.line, "col": self.col}
        for k, v in self.__dict__.items():
            if k in ("line", "col"):
                continue
            if isinstance(v, ASTNode):
                d[k] = v.to_dict()
            elif isinstance(v, list):
                d[k] = [item.to_dict() if isinstance(item, ASTNode) else item for item in v]
            else:
                d[k] = v
        return d
        
    def __str__(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


# ─── Base Categories ────────────────────────────────────────────────────────

class Expression(ASTNode):
    pass


class Statement(ASTNode):
    pass


class Program(ASTNode):
    def __init__(self, statements: List[Statement], line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.statements = statements


# ─── Expressions ────────────────────────────────────────────────────────────

class Identifier(Expression):
    def __init__(self, value: str, line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.value = value


class NumberLiteral(Expression):
    def __init__(self, value: Union[int, float], line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.value = value


class StringLiteral(Expression):
    def __init__(self, value: str, is_fstring: bool = False, line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.value = value
        self.is_fstring = is_fstring


class BooleanLiteral(Expression):
    def __init__(self, value: bool, line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.value = value


class NullLiteral(Expression):
    def __init__(self, line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.value = None


class BinaryOp(Expression):
    def __init__(self, left: Expression, op: str, right: Expression, line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.left = left
        self.op = op
        self.right = right


class UnaryOp(Expression):
    def __init__(self, op: str, right: Expression, line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.op = op
        self.right = right


class Assignment(Expression):
    def __init__(self, target: Expression, value: Expression, line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.target = target
        self.value = value


class Call(Expression):
    def __init__(self, callee: Expression, arguments: List[Expression], line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.callee = callee
        self.arguments = arguments


class ListLiteral(Expression):
    def __init__(self, elements: List[Expression], line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.elements = elements


class DictLiteral(Expression):
    def __init__(self, keys: List[Expression], values: List[Expression], line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.keys = keys
        self.values = values


class MemberAccess(Expression):
    def __init__(self, obj: Expression, property_name: str, line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.obj = obj
        self.property = property_name


class IndexAccess(Expression):
    def __init__(self, obj: Expression, index: Expression, line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.obj = obj
        self.index = index


# ─── Statements ─────────────────────────────────────────────────────────────

class ExpressionStatement(Statement):
    def __init__(self, expression: Expression, line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.expression = expression


class VarDecl(Statement):
    """
    متغير or ثابت declarations.
    is_const is True for 'ثابت', False for 'متغير'.
    """
    def __init__(self, name: str, value: Expression, is_const: bool, line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.name = name
        self.value = value
        self.is_const = is_const


class Block(Statement):
    def __init__(self, statements: List[Statement], line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.statements = statements


class IfStmt(Statement):
    def __init__(self, condition: Expression, then_branch: Block, 
                 elif_branches: List[tuple], else_branch: Optional[Block], 
                 line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.condition = condition
        self.then_branch = then_branch
        self.elif_branches = elif_branches  # list of (condition, block) tuples
        self.else_branch = else_branch


class WhileStmt(Statement):
    def __init__(self, condition: Expression, body: Block, line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.condition = condition
        self.body = body


class ForStmt(Statement):
    # هر identifier ۾ iterable: block
    def __init__(self, item_name: str, iterable: Expression, body: Block, line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.item_name = item_name
        self.iterable = iterable
        self.body = body


class FunctionDecl(Statement):
    def __init__(self, name: str, params: List[str], body: Block, is_extern: bool = False, line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.name = name
        self.params = params
        self.body = body
        self.is_extern = is_extern


class ClassDecl(Statement):
    def __init__(self, name: str, superclass: Optional[str], methods: List[FunctionDecl], line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.name = name
        self.superclass = superclass
        self.methods = methods


class ReturnStmt(Statement):
    def __init__(self, value: Optional[Expression], line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.value = value


class BreakStmt(Statement):
    def __init__(self, line: int = 1, col: int = 1):
        super().__init__(line, col)


class ContinueStmt(Statement):
    def __init__(self, line: int = 1, col: int = 1):
        super().__init__(line, col)


class ExternBlockNode(Statement):
    """
    Generated purely for ٻاهري ڪم ... bodies.
    Stores the raw string captured by the lexer.
    """
    def __init__(self, code: str, line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.code = code


class TryStmt(Statement):
    def __init__(self, try_block: Block, catch_name: Optional[str], catch_block: Optional[Block], finally_block: Optional[Block], line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.try_block = try_block
        self.catch_name = catch_name
        self.catch_block = catch_block
        self.finally_block = finally_block

class ImportStmt(Statement):
    def __init__(self, module_name: str, line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.module_name = module_name

class FromImportStmt(Statement):
    def __init__(self, module_name: str, names: List[str], line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.module_name = module_name
        self.names = names

class ExportStmt(Statement):
    def __init__(self, names: List[str], line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.names = names
