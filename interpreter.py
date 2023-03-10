import lox
import token_type as TokenType

from expr_ast import Expr, Grouping, Literal, Unary, Binary
from lox_token import Token

class LoxRuntimeError(Exception):
    def __init__(self, token: Token, message: str):
        super().__init__()
        self.token = token
        self.message = message


class Interpreter:
    def interpret(self, expression: Expr):
        try:
            val = self.evaluate(expression)
            print(stringify(val))
        except LoxRuntimeError as error:
            lox.Lox.runtime_error(error)

    def evaluate(self, expr: Expr) -> object:
        match expr:
            case Literal(value):
                return value
            case Grouping(expr):
                return self.evaluate(expr)
            case Unary(op, expr):
                right = self.evaluate(expr)
                match op.type:
                    case TokenType.MINUS:
                        return -to_float(right, op)
                    case TokenType.BANG:
                        return not is_truthy(right) 
            case Binary(l_expr, op, r_expr):
                left = self.evaluate(l_expr)
                right = self.evaluate(r_expr)
                match op.type:
                    case TokenType.MINUS:
                        return to_float(left, op) - to_float(right, op)
                    case TokenType.SLASH:
                        try:
                            return to_float(left, op) / to_float(right, op)
                        except ZeroDivisionError:
                            # According to IEEE 754 0/0 should result in a NaN
                            # We follow Python's implementation and always raise an error when dividing by zero
                            raise LoxRuntimeError(op, "float division by zero")
                    case TokenType.STAR:
                        return to_float(left, op) * to_float(right, op)
                    case TokenType.PLUS:
                        if type(left) == type(right) and type(left) in (str, float):
                            return left + right  # type: ignore[operator]
                        raise LoxRuntimeError(op, "Operands must be numbers or strings")

                    case TokenType.GREATER:
                        return to_float(left, op) > to_float(right, op)
                    case TokenType.GREATER_EQUAL:
                        return to_float(left, op) >= to_float(right, op)
                    case TokenType.LESS:
                        return to_float(left, op) < to_float(right, op)
                    case TokenType.LESS_EQUAL:
                        return to_float(left, op) <= to_float(right, op)
                    
                    case TokenType.EQUAL_EQUAL:
                        return left == right
                    case TokenType.BANG_EQUAL:
                        return left != right

                    
                    
        # Should be unreachable
        return None
    
def stringify(val: object) -> str:
    simple_conversions = {
        True: "true",
        False: "false",
        None: "nil"
    }
    if val in simple_conversions:
        return simple_conversions[val]  # type: ignore[index] 
    
    if isinstance(val, float) and str(val).endswith(".0"):
        return str(val)[:-2]

    return str(val)

def is_truthy(val: object) -> bool:
    # In Plox: Only nil and false are falsey
    # Other values, including 0, "" and [] are truthy
    falsy_values = (None, False)
    return val not in falsy_values

def to_float(obj: object, op: Token) -> float:
    if isinstance(obj, float):
        return obj
    raise LoxRuntimeError(op, "Operand must be a number")
