from collections.abc import Iterator
import typing

from expr_ast import AssignExpr, BinaryExpr, CallExpr, Expr, GetExpr, GroupingExpr, LiteralExpr, LogicalExpr, SetExpr, SuperExpr, ThisExpr, UnaryExpr, VariableExpr
from lox_token import Lox_Literal, Token
from stmt_ast import BlockStmt, BreakStmt, ClassStmt, ExpressionStmt, FunctionStmt, IfStmt, PrintStmt, ReturnStmt, Stmt, VarStmt, WhileStmt
from token_type import *
import lox
from error import LoxParseError


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0
        self.loop_depth = 0  # Tracks whether we're currently inside a loop or not

    def parse(self) -> list[Stmt]:
        statements = []
        while not self.is_at_end():
            # TODO: How to handle potential None here? Skip?
            if (decl := self.declaration()):
                statements.append(decl)
        return statements
    
    def var_declaration(self):
        name = self.consume(IDENTIFIER, "Expect variable name.")
        initializer = self.expression() if self.match(EQUAL) else None
        self.consume(SEMICOLON, "Expect ';' after variable declaration.")
        return VarStmt(name, initializer)
    
    def declaration(self) -> Stmt | None:
        try:
            if self.match(VAR):
                return self.var_declaration()
            if self.match(FUN):
                return self.function("function")
            if self.match(CLASS):
                return self.class_declaration()
            return self.statement()
        except LoxParseError:
            self.synchronize()
            return None
        
    def class_declaration(self):
        def get_methods() -> Iterator[FunctionStmt]:
            while not (self.check(RIGHT_BRACE) or self.is_at_end()):
                yield self.function("method")

        token = self.consume(IDENTIFIER, "Expect class name.")
        superclass = None
        if self.match(LESS):
            self.consume(IDENTIFIER, "Expect superclass name")
            superclass = VariableExpr(self.previous())
        self.consume(LEFT_BRACE, "Expect '{' before class body.")

        methods = list(get_methods())

        self.consume(RIGHT_BRACE, "Expect '}' after class body")

        return ClassStmt(token, superclass, methods)
        
    def function(self, kind: typing.Literal["function", "method"]) -> FunctionStmt:
        def get_params() -> Iterator[Token]:
            yield self.consume(IDENTIFIER, "Expect parameter name.")
            while self.match(COMMA):
                yield self.consume(IDENTIFIER, "Expect parameter name.")
        
        token = self.consume(IDENTIFIER, f"Expect {kind} name.")
        self.consume(LEFT_PAREN, f"Expect '(' after {kind} name.")
        params = list(get_params()) if not self.check(RIGHT_PAREN) else []
        self.consume(RIGHT_PAREN, "Expect ')' after parameter list.")
        
        if len(params) >= 255:
            self.error(self.peek(), "Can't have more than 255 parameters.")

        self.consume(LEFT_BRACE, f"Expect {{ before {kind} body.")
        body = self.block()

        return FunctionStmt(token, params, body)
        
    def block(self) -> list[Stmt]:
        # Return statement list instead of block for re-use
        def get_statements():
            while not self.check(RIGHT_BRACE):
                yield self.declaration()

        statements = list(get_statements())
        self.consume(RIGHT_BRACE, "Expect '}' after block.")
        return statements

    def statement(self) -> Stmt:
        def print_statement() -> PrintStmt:
            value = self.expression()
            self.consume(SEMICOLON, "Expect ';' after value.")
            return PrintStmt(value)

        def expression_statement() -> ExpressionStmt:
            expr = self.expression()
            self.consume(SEMICOLON, "Expect ';' after expression.")
            return ExpressionStmt(expr)
        
        def if_statement() -> IfStmt:
            self.consume(LEFT_PAREN, "Expect '(' after 'if'.")
            condition = self.expression()
            self.consume(RIGHT_PAREN, "Expect ')' after 'if' condition.")

            then_branch = self.statement()  # TODO: match block instead? or block | if
            else_branch = self.statement() if self.match(ELSE) else None
            return IfStmt(condition, then_branch, else_branch)
        
        def while_statement() -> WhileStmt:
            self.consume(LEFT_PAREN, "Expect '(' after 'while'.")
            condition = self.expression()
            self.consume(RIGHT_PAREN, "Expect ')' after 'while' condition.")

            self.loop_depth += 1
            body = self.statement()
            self.loop_depth -= 1

            return WhileStmt(condition, body)
        
        def break_statement() -> Stmt:
            if not self.loop_depth:
                raise self.error(self.previous(), "Expect 'break' to appear inside a loop.")
            
            stmt = BreakStmt(self.previous())
            self.consume(SEMICOLON, "Expect ';' after break.")
            return stmt 
        
        def for_statement() -> Stmt:
            """
            For-statements are syntactic sugar in Lox. 
            They get 'de-sugared' into while-loops, so:

            'for (var i = 0; i < 10; i = i + 1)'
            
            is turned into:
            
            {
                var i = 0;
                while (i < 10) {
                    print i;
                    i = i + 1;
                }
            }
            """

            # Gather all the parts
            self.consume(LEFT_PAREN, "Expect '(' after 'for'.")
            if self.match(SEMICOLON):
                initializer = None
            elif self.match(VAR):
                initializer = self.var_declaration()
            else:
                initializer = expression_statement()

            condition = None if self.check(SEMICOLON) else self.expression()
            self.consume(SEMICOLON, "Expect ';' after loop condition.")

            increment = None if self.check(RIGHT_PAREN) else self.expression()
            self.consume(RIGHT_PAREN, "Expect ')' after for clause")

            self.loop_depth += 1
            body = self.statement()
            self.loop_depth -= 1

            # Put all the parts together into a two-level block while-statement
            while_body = BlockStmt(
                [body] + ([ExpressionStmt(increment)] if increment else [])
            )
            while_cond = condition or LiteralExpr(True)
            while_stmt = WhileStmt(while_cond, while_body)

            if initializer:
                return BlockStmt([initializer, while_stmt])
            
            return while_stmt
        
        def return_statement():
            keyword = self.previous()
            value = self.expression() if not self.check(SEMICOLON) else None

            self.consume(SEMICOLON, "Expect ';' after return statement")

            return ReturnStmt(keyword, value)

        
        if self.match(FOR):
            return for_statement()
        
        if self.match(IF):
            return if_statement()

        if self.match(PRINT):
            return print_statement()
        
        if self.match(WHILE):
            return while_statement()
        
        if self.match(LEFT_BRACE):
            return BlockStmt(self.block())
        
        if self.match(BREAK):
            return break_statement()
        
        if self.match(RETURN):
            return return_statement()
        
        return expression_statement()

    def expression(self) -> Expr:
        def detect_illegal_binary_operator():
            # Leave out minus as it is a valid unary op
            binary_ops = (BANG_EQUAL, EQUAL_EQUAL,
                LESS, LESS_EQUAL, GREATER, GREATER_EQUAL,
                PLUS, SLASH, STAR
            )
            if self.match(*binary_ops):
                # Discard right-hand expression
                try: self.expression()
                except LoxParseError: ...

                raise self.error(self.previous(), "Expected expression left of binary operator")
            
        def assignment() -> Expr:
            expr = or_expr()

            if self.match(EQUAL):  # Won't match on '==' due to above equality() call (inside or_expr)
                value = assignment()  # Recursively evaluate to the right. Allows chaining assignment
                if type(expr) == VariableExpr:
                    return AssignExpr(expr.token, value)
                if type(expr) == GetExpr:
                    return SetExpr(expr.instance, expr.token, value)
                
                # Report error. No need to raise and synchronize because the parser is not confused
                self.error(self.previous(), "Invalid assignment target.")

            return expr
        
        def or_expr() -> Expr:
            expr = and_expr()
            while self.match(AND):
                operator = self.previous()
                right = and_expr()
                expr = LogicalExpr(expr, operator, right)
 
            return expr

        def and_expr() -> Expr:
            expr = equality()
            while self.match(AND):
                operator = self.previous()
                right = equality()
                expr = LogicalExpr(expr, operator, right)

            return expr

        def equality() -> Expr:
            detect_illegal_binary_operator()
            expr = comparison()

            while self.match(BANG_EQUAL, EQUAL_EQUAL):
                operator = self.previous()
                right = comparison()
                expr = BinaryExpr(expr, operator, right)

            return expr
        
        def comparison() -> Expr:
            expr = term()
            while self.match(LESS, LESS_EQUAL, GREATER, GREATER_EQUAL):
                operator = self.previous()
                right = term()
                expr = BinaryExpr(expr, operator, right)

            return expr
        
        def term() -> Expr:
            expr = factor()
            while self.match(MINUS, PLUS):
                operator = self.previous()
                right = factor()
                expr = BinaryExpr(expr, operator, right)

            return expr

        def factor() -> Expr:
            expr = unary()
            while self.match(SLASH, STAR):
                operator = self.previous()
                right = unary()
                expr = BinaryExpr(expr, operator, right)

            return expr

        def unary() -> Expr:
            if self.match(BANG, MINUS):
                operator = self.previous()
                right = unary()
                return UnaryExpr(operator, right)

            return call()
        
        def call() -> Expr:
            def finish_call(callee: Expr) -> Expr:
                def get_args() -> Iterator[Expr]:
                    yield self.expression()
                    while self.match(COMMA):
                        yield self.expression()
                
                args = list(get_args()) if not self.check(RIGHT_PAREN) else []
                r_paren = self.consume(RIGHT_PAREN, "Expect ') after function arguments.")
                
                if len(args) >= 255: 
                    self.error(self.peek(), "Can't have more than 255 arguments")

                return CallExpr(callee, r_paren, tuple(args))                   
                
            expr = primary()

            while True:
                if self.match(LEFT_PAREN):
                    expr = finish_call(expr)
                elif self.match(DOT):
                    token = self.consume(IDENTIFIER, "Expect property name after '.'.")
                    expr = GetExpr(expr, token)
                else:
                    break
            
            return expr
        
        def primary() -> Expr:
            if self.match(NUMBER, STRING, TRUE, FALSE, NIL):
                conversion_dict: dict[TokenType, Lox_Literal] = {
                    FALSE: False, TRUE: True, NIL: None
                }
                token = self.previous()
                value = conversion_dict.get(token.type, token.literal)  # type: ignore[call-overload]
                return LiteralExpr(value)
            elif self.match(THIS):
                return ThisExpr(self.previous())
            elif self.match(SUPER):
                keyword = self.previous()
                self.consume(DOT, "Expect '.' after 'super'")
                method = self.consume(IDENTIFIER, "Expect superclass method name.")
                return SuperExpr(keyword, method)
            elif self.match(IDENTIFIER):
                return VariableExpr(self.previous())
            elif self.match(LEFT_PAREN):
                expr = self.expression()
                self.consume(RIGHT_PAREN, "Expcted ')' after expression.")
                return GroupingExpr(expr)
            
            raise self.error(self.peek(), "Expected expression.")

        
        return assignment()
    
    def synchronize(self):
        self.advance()
        # consume tokens until we hit the a statement boundary (end of one or start of another)
        while not self.is_at_end():
            if self.previous().type == SEMICOLON: 
                return
            
            if self.peek().type in (CLASS, FUN, VAR, FOR, IF, WHILE, PRINT, RETURN):
                return
            
            self.advance()

    def error(self, token: Token, message: str):
        lox.Lox.parse_error(token, message)
        return LoxParseError()
    
    def check(self, ttype:TokenType):
        return not self.is_at_end() and self.peek().type == ttype
        
    def consume(self, ttype: TokenType, message: str):
        if self.check(ttype):
            return self.advance()
        
        raise self.error(self.peek(), message)

    def is_at_end(self) -> bool:
        return self.peek().type == EOF

    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1
        return self.previous()
    
    def match(self, *tokens) -> bool:
        if self.is_at_end() or self.tokens[self.current].type not in tokens:
            return False 
        
        self.advance()
        return True
    
    def peek(self) -> Token:
        return self.tokens[self.current]
    
    def previous(self) -> Token:
        return self.tokens[self.current - 1]
