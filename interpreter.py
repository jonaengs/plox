from abc import abstractmethod
import time
import typing

from environment import Environment
import lox
from stmt_ast import BlockStmt, BreakStmt, ClassStmt, ExpressionStmt, FunctionStmt, IfStmt, PrintStmt, ReturnStmt, Stmt, VarStmt, WhileStmt
import token_type as TokenType
from error import LoxRuntimeError

from expr_ast import AssignExpr, CallExpr, Expr, GetExpr, GroupingExpr, LiteralExpr, LogicalExpr, SetExpr, UnaryExpr, BinaryExpr, VariableExpr
from lox_token import Token

class Lox_Callable(typing.Protocol):
    @abstractmethod
    def arity(self): ...
    @abstractmethod
    def call(self, interpreter: "Interpreter", arguments: list[object]) -> object: ...

class Lox_Function(typing.NamedTuple):
    declaration: FunctionStmt
    closure: Environment

    def call(self, interpreter: "Interpreter", arguments: list[object]) -> object:
        environment = Environment(self.closure)
        for param, arg in zip(self.declaration.params, arguments):
            environment.define(param.lexeme, arg)

        try:
            interpreter._execute_block(self.declaration.body, environment)
        except Return as r:
            return r.ret_val
        return None

    def arity(self) -> int:
        return len(self.declaration.params)
    
    def __str__(self) -> str:
        return f"<fn '{self.declaration.token.lexeme}'>"

class Lox_Class(typing.NamedTuple):
    name: str
    methods: dict[str, Lox_Function]

    def call(self, interpreter: "Interpreter", arguments: list[object]) -> "Lox_Instance":
        instance = Lox_Instance(self)
        return instance
    
    def find_method(self, identifier: str) -> Lox_Function:
        if identifier in self.methods:
            return self.methods[identifier]
    
    def arity(self) -> int:
        return 0

    def __str__(self) -> str:
        return self.name
    
class Lox_Instance:
    def __init__(self, klass: Lox_Class):
        self.klass = klass
        self.fields: dict[str, object] = {}

    def get(self, token: Token):
        if token.lexeme in self.fields:
            return self.fields[token.lexeme]
        if (method := self.klass.find_method(token.lexeme)):
            return method
            
        raise LoxRuntimeError(token, f"Undefined property '{token.lexeme}' of {self}.")
    
    def set(self, token: Token, value: object):
        self.fields[token.lexeme] = value

    def __str__(self):
        return str(self.klass) + " instance"
    
class Return(Exception):
    def __init__(self, ret_val):
        super().__init__()
        self.ret_val = ret_val

class Break(Exception):
    ...

class Interpreter:
    def __init__(self) -> None:
        self.globals = Environment()
        self.environment = self.globals
        self.locals: dict[Expr, int] = {}

        def get_clock_fun() -> Lox_Callable:
            class _:
                def arity(self) -> int: 
                    return 0
                
                def call(self, interpreter: Interpreter, arguments: list[object]) -> float:
                    return time.time()
                
                def __str__(self) -> str:
                    return "<native fn 'clock'>"
                
            return _()
        
        self.globals.define("clock", get_clock_fun())

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
            case IfStmt(cond, b_then, b_else):
                if is_truthy(self._evaluate(cond)):
                    self._execute(b_then)
                elif b_else is not None:
                    self._execute(b_else)
            case WhileStmt(cond, body):
                try:
                    while is_truthy(self._evaluate(cond)):
                        self._execute(body)
                except Break:
                    pass
            case BreakStmt(_token):
                raise Break()
            case FunctionStmt(token, _params, _body):
                function: Lox_Callable = Lox_Function(statement, self.environment)
                self.environment.define(token.lexeme, function)
            case ReturnStmt(token, expr):
                raise Return(expr and self._evaluate(expr))
            case ClassStmt(token, methods_stmts):
                self.environment.define(token.lexeme, None)
                methods = {
                    method.token.lexeme: Lox_Function(method, self.environment)
                    for method in methods_stmts
                }
                
                lox_class = Lox_Class(token.lexeme, methods)
                self.environment.assign(token, lox_class)

    
    def _execute_block(self, statements: list[Stmt], environment: Environment):
        prev_env = self.environment
        try:
            self.environment = Environment(environment)
            for statement in statements:
                self._execute(statement)
        finally:
            self.environment = prev_env

    def _evaluate(self, expr: Expr) -> object:
        match expr:
            case LiteralExpr(value):
                return value
            case GroupingExpr(expr):
                return self._evaluate(expr)
            case UnaryExpr(op, expr):
                right = self._evaluate(expr)
                match op.type:
                    case TokenType.MINUS:
                        return -to_float(right, op)
                    case TokenType.BANG:
                        return not is_truthy(right)
            case LogicalExpr(l_expr, op, r_expr):
                # Logical expr returns the value of one of its operands
                # not a boolean (except when operands are booleans).
                # The truthiness will be the same as if, though.
                left = self._evaluate(l_expr)
                if op.type == TokenType.OR and is_truthy(left):
                    return left
                elif not is_truthy(left):
                    return left
                return self._evaluate(r_expr)
            case BinaryExpr(l_expr, op, r_expr):
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
            case VariableExpr(token):
                return self.lookup_variable(token, expr)
            case AssignExpr(token, expr):
                # Make assignment an expression
                expr_val = self._evaluate(expr)
                distance = self.locals.get(expr)
                if distance:
                    self.environment.assign_at(distance, token.lexeme, expr_val)
                else: 
                    self.globals.assign(token, expr_val)
                return expr_val
            case CallExpr(callee_expr, r_paren, args_exprs):
                callee = self._evaluate(callee_expr)
                args = list(map(self._evaluate, args_exprs))

                fun = typing.cast(Lox_Callable, callee)
                try:
                    if len(args) == fun.arity():
                        return fun.call(self, args)
                    raise LoxRuntimeError(r_paren, f"Expected {fun.arity()} arguments but got {len(args)}.")
                except AttributeError:
                    raise LoxRuntimeError(r_paren, "Can only call functions or classes")
            case GetExpr(instance_expr, token):
                instance = self._evaluate(instance_expr)
                if type(instance) == Lox_Instance:
                    return instance.get(token)
                raise LoxRuntimeError(token, "Only instances have properties.")
            case SetExpr(instance_expr, token, value_expr):
                instance = self._evaluate(instance_expr)

                if type(instance) != Lox_Instance:
                    raise LoxRuntimeError(token, "Only instances have fields.")
                
                value = self._evaluate(value_expr)
                instance.set(token, value)
                return value

        raise Exception("Interpreter missing match case")
    
    
    def resolve(self, expr: Expr, depth: int):
        self.locals[expr] = depth

    def lookup_variable(self, token: Token, expr: Expr):
        distance = self.locals.get(expr)
        if distance:
            return self.environment.get_at(distance, token.lexeme)
        else:
            return self.globals.get(token)
    
def stringify(val: object) -> str:
    simple_conversions = {
        True: "true",
        False: "false",
        None: "nil"
    }
    
    if isinstance(val, float) and str(val).endswith(".0"):
        return str(val)[:-2]
    
    # Do after float check because 1 == True, meaning otherwise
    # all 1's will print as 'true'
    if val in list(simple_conversions.keys()):  # TODO: Figure out why looking up Lox_Function objects directly in the dict causes a crash
        return simple_conversions[val]  # type: ignore[index] 

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
