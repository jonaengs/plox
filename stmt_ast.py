from typing import NamedTuple, Union

from expr_ast import Expr
from lox_token import Token


Stmt = Union["ExpressionStmt", "PrintStmt", "VarStmt", "BlockStmt", "IfStmt", "WhileStmt", "BreakStmt"]

class VarStmt(NamedTuple):
    name: Token
    initializer: Expr | None

class ExpressionStmt(NamedTuple):
    expression: Expr

class PrintStmt(NamedTuple):
    expression: Expr

class BlockStmt(NamedTuple):
    statements: list[Stmt]

class IfStmt(NamedTuple):
    condition: Expr
    then_branch: Stmt
    else_branch: Stmt | None

class WhileStmt(NamedTuple):
    condition: Expr
    body: Stmt

class BreakStmt(NamedTuple):
    token: Token