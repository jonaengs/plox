from typing import NamedTuple, Union

from expr_ast import Expr
from lox_token import Token


Stmt = Union["ExpressionStmt", "PrintStmt", "VarStmt", "BlockStmt"]

class VarStmt(NamedTuple):
    name: Token
    initializer: Expr | None

class ExpressionStmt(NamedTuple):
    expression: Expr

class PrintStmt(NamedTuple):
    expression: Expr

class BlockStmt(NamedTuple):
    statements: list[Stmt]