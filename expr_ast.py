from typing import NamedTuple, Union

from lox_token import Token, Lox_Literal
import token_type as TokenType

# TODO: Figure out if we can keep abc metaclass somehow
# class Expr(NamedTuple, metaclass=ABCMeta): 

Expr = Union["Binary", "Grouping", "Literal", "Unary", "Variable", "Assign", "Logical", "Call"]

class Binary(NamedTuple):
    left: Expr
    operator: Token
    right: Expr

class Grouping(NamedTuple):
    expression: Expr

class Literal(NamedTuple):
    value: Lox_Literal

class Unary(NamedTuple):
    operator: Token
    right: Expr

class Variable(NamedTuple):
    token: Token

class Assign(NamedTuple):
    token: Token
    value: Expr

class Logical(NamedTuple):
    left: Expr
    operator: Token
    right: Expr

class Call(NamedTuple):
    callee: Expr
    r_paren: Token  # For reporting errors
    arguments: list[Expr]



def print_expr(expr: Expr):
    # TODO: Add remaining classes or remove completely
    def parenthesize(name: str, *exprs: Expr):
        return f"({name} {' '.join(map(print_expr, exprs))})"
     
    match expr:
        case Binary(left, operator, right):
            return parenthesize(operator.lexeme, left, right)
        case Grouping(expression):
            return parenthesize("group", expression)
        case Literal(value):
            return "nil" if value is None else str(value)
        case Unary(operator, right):
            return parenthesize(operator.lexeme, right)
        

if __name__ == '__main__':
    expr = Binary(
        Unary(
            Token(TokenType.MINUS, "-", None, 1),
            Literal(123)
        ),
        Token(TokenType.STAR, "*", None, 1),
        Grouping(Literal(45.67))
    )
    print(print_expr(expr))

    unary = Unary(
        Token(TokenType.MINUS, "-", None, 1),
        Literal(123)
    )