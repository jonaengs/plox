from environment import Environment
import lox
from stmt_ast import BlockStmt, ExpressionStmt, PrintStmt, Stmt, VarStmt
import token_type as TokenType
from error import LoxRuntimeError

from expr_ast import Assign, Expr, Grouping, Literal, Unary, Binary, Variable
from lox_token import Token

class Interpreter:
    def __init__(self) -> None:
        self.environment = Environment()

    def interpret(self, statements: list[Stmt]):
        try:
            for statement in statements:
                self._execute(statement)
        except LoxRuntimeError as error:
            lox.Lox.runtime_error(error)

    def _execute(self, statement: Stmt):
        match statement:
            case PrintStmt(expr):
                value = self._evaluate(expr)
                print(stringify(value))
            case ExpressionStmt(expr):
                self._evaluate(expr)
            case VarStmt(token, initial):
                # Allow declaring vars without initial value
                # All values without initial are set to nil/None
                value = initial and self._evaluate(initial)
                self.environment.define(token.lexeme, value)
            case BlockStmt(stmts):
                self._execute_block(stmts, Environment(self.environment))
    
    def _execute_block(self, statements: list[Stmt], environment: Environment):
        prev_env = self.environment
        try:
            self.environment  = environment
            for statement in statements:
                self._execute(statement)
        finally:
            self.environment = prev_env

    def _evaluate(self, expr: Expr) -> object:
        match expr:
            case Literal(value):
                return value
            case Grouping(expr):
                return self._evaluate(expr)
            case Unary(op, expr):
                right = self._evaluate(expr)
                match op.type:
                    case TokenType.MINUS:
                        return -to_float(right, op)
                    case TokenType.BANG:
                        return not is_truthy(right) 
            case Binary(l_expr, op, r_expr):
                left = self._evaluate(l_expr)
                right = self._evaluate(r_expr)
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
                        print(type(left), type(right))
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
            case Variable(token):
                return self.environment.get(token)
            case Assign(token, expr):
                # Make assignment an expression
                expr_val = self._evaluate(expr)
                self.environment.assign(token, expr_val)
                return expr_val

        raise Exception("Interpreter missing match case")

    
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
