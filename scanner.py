
import lox
from lox_token import Token
from token_type import *

simple_lexemes = {
    '(': LEFT_PAREN,
    ')': RIGHT_PAREN,
    '{': LEFT_BRACE,
    '}': RIGHT_BRACE,
    ',': COMMA,
    '.': DOT,
    '-': MINUS,
    '+': PLUS,
    ';': SEMICOLON,
    '*': STAR
}

two_char_lexemes = {
    "!": ("=", (BANG_EQUAL, BANG)),
    "=": ("=", (EQUAL_EQUAL, EQUAL)),
    "<": ("=", (LESS_EQUAL, LESS)),
    ">": ("=", (GREATER_EQUAL, GREATER))
}

class Scanner:
    def __init__(self, source):
        self.source = source
        self.tokens = []

        self.start = 0
        self.current = 0
        self.line = 1

    def is_at_end(self):
        return self.current >= len(self.source)

    def scan_tokens(self) -> list[Token]:
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()

        self.tokens.append(Token(EOF, "", None, self.line))

        return self.tokens
    
    def advance(self):
        self.current += 1
        return self.source[self.current - 1]
    
    def add_token(self, ttype: TokenType, literal: object=None):
        text = self.source[self.start:self.current]
        self.tokens.append(Token(ttype, text, literal, self.line))

    def match(self, expected: str):
        if self.is_at_end(): 
            return False
        if self.source[self.current] != expected:
            return False
    
        self.current += 1
        return True
    
    def peek(self):
        if self.is_at_end():
            return '\0'
        return self.source[self.current]
    
    def scan_token(self):
        c = self.advance()
        if c in simple_lexemes:
            self.add_token(simple_lexemes[c])
        elif c in two_char_lexemes:
            expect_char, ttypes = two_char_lexemes[c]
            ttype = ttypes[0] if self.match(expect_char) else ttypes[1]
            self.add_token(ttype)
        elif c == "/":
            if self.match("/"):  # Double slash => comment
                while self.peek() != "\n" and not self.is_at_end():
                    self.advance()
            else:
                self.add_token(SLASH)
        elif c in (' ', '\t', '\r', '\n'):
            # Ignore whitespace, except newlines where we increment line no.
            self.line += c == '\n'
        else:
            lox.Lox.error(self.line, "Unexpected character")

        
        



