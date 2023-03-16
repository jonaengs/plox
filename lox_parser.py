from expr_ast import Assign, Binary, Expr, Grouping, Literal, Unary, Variable
from lox_token import Token
from stmt_ast import BlockStmt, ExpressionStmt, PrintStmt, Stmt, VarStmt
from token_type import *
import lox
from error import LoxParseError

class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> list[Stmt]:
        statements = []
        while not self.is_at_end():
            # TODO: How to handle potential None here? Skip?
            if (decl := self.declaration()):
                statements.append(decl)
        return statements
    
    def declaration(self) -> Stmt | None:
        def var_declaration():
            name = self.consume(IDENTIFIER, "Expect variable name.")
            initializer = self.expression() if self.match(EQUAL) else None
            self.consume(SEMICOLON, "Expect ';' after variable declaration.")
            return VarStmt(name, initializer)
        
        try:
            if self.match(VAR):
                return var_declaration()
            return self.statement()
        except LoxParseError:
            self.synchronize()
            return None
        
    def statement(self) -> Stmt:
        def print_statement() -> PrintStmt:
            value = self.expression()
            self.consume(SEMICOLON, "Expect ';' after value.")
            return PrintStmt(value)

        def expression_statement() -> ExpressionStmt:
            expr = self.expression()
            self.consume(SEMICOLON, "Expect ';' after expression.")
            return ExpressionStmt(expr)
        
        def block() -> list[Stmt]:
            # Return statement list instead of block for re-use
            def get_statements():
                while not self.check(RIGHT_BRACE):
                    yield self.declaration()

            statements = list(get_statements())
            self.consume(RIGHT_BRACE, "Expect '}' after block.")
            return statements

        if self.match(PRINT):
            return print_statement()
        
        if self.match(LEFT_BRACE):
            return BlockStmt(block())
        
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
            expr = equality()

            if self.match(EQUAL):  # Won't match on '==' due to above equality() call
                value = assignment()  # Recursively evaluate to the right. Allows chaining assignment
                if type(expr) == Variable:
                    return Assign(expr.token, value)
                
                # Report error. No need to raise and synchronize because the parser is not confused
                self.error(self.previous(), "Invalid assignment target.")

            return expr

        def equality() -> Expr:
            detect_illegal_binary_operator()
            expr = comparison()

            while self.match(BANG_EQUAL, EQUAL_EQUAL):
                operator = self.previous()
                right = comparison()
                expr = Binary(expr, operator, right)

            return expr
        
        def comparison() -> Expr:
            expr = term()
            while self.match(LESS, LESS_EQUAL, GREATER, GREATER_EQUAL):
                operator = self.previous()
                right = term()
                expr = Binary(expr, operator, right)

            return expr
        
        def term() -> Expr:
            expr = factor()
            while self.match(MINUS, PLUS):
                operator = self.previous()
                right = factor()
                expr = Binary(expr, operator, right)

            return expr

        def factor() -> Expr:
            expr = unary()
            while self.match(SLASH, STAR):
                operator = self.previous()
                right = unary()
                expr = Binary(expr, operator, right)

            return expr

        def unary() -> Expr:
            if self.match(BANG, MINUS):
                operator = self.previous()
                right = unary()
                return Unary(operator, right)

            return primary()
        
        def primary() -> Expr:
            if self.match(NUMBER, STRING, TRUE, FALSE, NIL):
                token = self.previous()
                value = {FALSE: False, TRUE: True, NIL: None}.get(token, token.literal)  # type: ignore[call-overload]
                return Literal(value)
            elif self.match(IDENTIFIER):
                return Variable(self.previous())
            elif self.match(LEFT_PAREN):
                expr = self.expression()
                self.consume(RIGHT_PAREN, "Expcted ')' after expression.")
                return Grouping(expr)
            
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
