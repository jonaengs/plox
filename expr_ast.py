from typing import NamedTuple, Union

from lox_token import Token, Lox_Literal
import token_type as TokenType

# TODO: Figure out if we can keep abc metaclass somehow
# class Expr(NamedTuple, metaclass=ABCMeta): 

Expr = Union["BinaryExpr", "GroupingExpr", "LiteralExpr", "UnaryExpr", "VariableExpr", "AssignExpr", "LogicalExpr", "CallExpr", "GetExpr", "SetExpr", "ThisExpr", "SuperExpr"]

class BinaryExpr(NamedTuple):
    left: Expr
    operator: Token
    right: Expr

class GroupingExpr(NamedTuple):
    expression: Expr

class LiteralExpr(NamedTuple):
    value: Lox_Literal

class UnaryExpr(NamedTuple):
    operator: Token
    right: Expr

class VariableExpr(NamedTuple):
    token: Token

class AssignExpr(NamedTuple):
    token: Token
    value: Expr

class LogicalExpr(NamedTuple):
    left: Expr
    operator: Token
    right: Expr

class CallExpr(NamedTuple):
    callee: Expr
    r_paren: Token  # For reporting errors
    arguments: tuple[Expr]

class GetExpr(NamedTuple): # Property access expression
    instance: Expr
    token: Token

class SetExpr(NamedTuple):
    instance: Expr
    token: Token
    value: Expr

class ThisExpr(NamedTuple):
    token: Token

class SuperExpr(NamedTuple):
    token: Token
    method: Token


def print_expr(expr: Expr):
    # TODO: Add remaining classes or remove completely
    def parenthesize(name: str, *exprs: Expr):
        return f"({name} {' '.join(map(print_expr, exprs))})"
     
    match expr:
        case BinaryExpr(left, operator, right):
            return parenthesize(operator.lexeme, left, right)
        case GroupingExpr(expression):
            return parenthesize("group", expression)
        case LiteralExpr(value):
            return "nil" if value is None else str(value)
        case UnaryExpr(operator, right):
            return parenthesize(operator.lexeme, right)
        

if __name__ == '__main__':
    expr = BinaryExpr(
        UnaryExpr(
            Token(TokenType.MINUS, "-", None, 1),
            LiteralExpr(123)
        ),
        Token(TokenType.STAR, "*", None, 1),
        GroupingExpr(LiteralExpr(45.67))
    )
    print(print_expr(expr))

    unary = UnaryExpr(
        Token(TokenType.MINUS, "-", None, 1),
        LiteralExpr(123)
    )