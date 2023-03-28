

from enum import Enum, auto
from typing import Literal
import lox
import interpreter as intepreter_module
from expr_ast import Expr, GetExpr, SetExpr, ThisExpr
from lox_token import Token

from stmt_ast import BlockStmt, BreakStmt, ClassStmt, ExpressionStmt, FunctionStmt, IfStmt, PrintStmt, ReturnStmt, Stmt, VarStmt, WhileStmt
from expr_ast import AssignExpr, CallExpr, Expr, GroupingExpr, LiteralExpr, LogicalExpr, UnaryExpr, BinaryExpr, VariableExpr

class FunctionType(Enum):
    NONE = auto()
    FUNCTION = auto()
    METHOD = auto()
    INITIALIZER = auto()

class ClassType(Enum):
    NONE = auto()
    CLASS = auto()

class Resolver:
    def __init__(self, interpreter: intepreter_module.Interpreter):
        self.interpreter = interpreter
        self.scopes: list[dict[str, bool]] = []
        self.current_function = FunctionType.NONE
        self.current_class = ClassType.NONE

    def resolve(self, statements: list[Stmt]):
        for stmt in statements:
            self._resolve(stmt)

    def _resolve(self, unit: Expr | Stmt):
        # This is a combination of the visit and resolve
        # methods from the book. Implementing them as 
        # separate functions seemed wasteful, as I'm
        # not following the visitor pattern.

        """
        Note the difference between declaring and defining a variable.
        When we declare a variable, we mark it as encountered and 
        shadowing the outer scopes, but not yet ready to use. 
        A variable is defined when its initializer has been executed
        and it has been assigned a value -- it is ready to be used.
        """

        match unit:
            # STATEMENTS
            case BlockStmt(statements):
                with self.enter_scope():
                    for statement in statements:
                        self._resolve(statement)
            case VarStmt(token, initializer):
                self._declare(token)
                if initializer:
                    self._resolve(initializer)
                self._define(token)
            case FunctionStmt(token, _, _):
                self._declare(token)
                self._define(token)
                self._resolve_function(unit, FunctionType.FUNCTION)
            case ExpressionStmt(expr):
                self._resolve(expr)
            case IfStmt(condition, then_branch, else_branch):
                self._resolve(condition)
                self._resolve(then_branch)
                if else_branch: self._resolve(else_branch)
            case PrintStmt(expr):
                self._resolve(expr)
            case ReturnStmt(token, expr):
                if self.current_function == FunctionType.NONE:
                    lox.Lox.parse_error(token, "Can't return from top-level code.")
                if expr:
                    if self.current_function == FunctionType.INITIALIZER:
                        lox.Lox.parse_error(token, "Can't return a value from an initializer.")
                    self._resolve(expr)
            case WhileStmt(condition, body):
                self._resolve(condition)
                self._resolve(body)
            case BreakStmt():
                pass
            case ClassStmt(token, methods):
                enclosing_class = self.current_class
                self.current_class = ClassType.CLASS
                
                self._declare(token)
                self._define(token)
                with self.enter_scope() as scope:
                    scope["this"] = True
                    for method in methods:
                        func_type = FunctionType.INITIALIZER \
                            if token.lexeme == "init" else FunctionType.METHOD
                        self._resolve_function(method, func_type)
                
                self.current_class = enclosing_class


            # EXPRESSIONS
            case VariableExpr(token):
                scope = self.scopes and self.scopes[-1]
                if scope and scope.get(token.lexeme) == False:
                    lox.Lox.parse_error(token, "Can't read local variable in its own initializer.")  # TODO: in book, the method is called "error"
                self._resolve_local(unit, token)
            case AssignExpr(token, value):
                self._resolve(value)
                self._resolve_local(unit, token)
            case BinaryExpr(left, _operator, right):
                self._resolve(left)
                self._resolve(right)
            case CallExpr(callee, _paren, args):
                self._resolve(callee)
                for arg in args:
                    self._resolve(arg)
            case GroupingExpr(expr):
                self._resolve(expr)
            case LiteralExpr():
                pass
            case LogicalExpr(left, _operator, right):
                self._resolve(left)
                self._resolve(right)
            case UnaryExpr(_operator, expr):
                self._resolve(expr)
            case GetExpr(instance, _token):
                self._resolve(instance)
            case SetExpr(instance, token, value):
                self._resolve(value)
                self._resolve(instance)
            case ThisExpr(token):
                if self.current_class == ClassType.NONE:
                    lox.Lox.parse_error("Can't use 'this' outside a class.")
                else:
                    self._resolve_local(unit, token)
            
    def _resolve_function(self, function: FunctionStmt, ftype: FunctionType):
        enclosing_function = self.current_function
        self.current_function = ftype

        with self.enter_scope():
            for param in function.params:
                self._declare(param)
                self._define(param)

            # This scope is not in the book. However, we do keep the parameters
            # and the body in separate environments in the interpreter,
            # so this has to be here?
            with self.enter_scope():
                for statement in function.body:
                    self._resolve(statement)

        self.current_function = enclosing_function

    def _resolve_local(self, expr: Expr, token: Token):
        for i, scope in enumerate(reversed(self.scopes)):
            if token.lexeme in scope:
                self.interpreter.resolve(expr, i)
                return
            
    def _declare(self, token: Token):
        if not self.scopes: return

        # Prevent successive var statements for the same name below the global scope
        if token.lexeme in self.scopes[-1]:
            lox.Lox.parse_error(token, "A variable with that name already exists in this scope")

        self.scopes[-1][token.lexeme] = False

    def _define(self, token):
        if self.scopes:
            self.scopes[-1][token.lexeme] = True

    def enter_scope(self):
        class ScopeEnter:
            def __enter__(*_):
                new_scope = {}
                self.scopes.append(new_scope)
                return new_scope
            
            def __exit__(*_):
                self.scopes.pop()

        return ScopeEnter()
        