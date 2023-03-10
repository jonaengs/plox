from expr_ast import Binary, Expr, Grouping, Literal, Unary
from lox_token import Token
from token_type import *
import lox

class ParseError(Exception):
    ...


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self):
        try:
            return self.expression()
        except ParseError:
            return None

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
                except ParseError: ...

                raise self.error(self.previous(), "Expected expression left of binary operator")

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
            elif self.match(LEFT_PAREN):
                expr = self.expression()
                self.consume(RIGHT_PAREN, "Expcted ')' after expression.")
                return Grouping(expr)
            
            raise self.error(self.peek(), "Expected expression.")

        
        return equality()
    
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
        return ParseError()
        
    def consume(self, ttype: TokenType, message: str):
        if self.is_at_end() or self.peek().type == ttype:
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
