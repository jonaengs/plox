
import lox
from lox_token import Token
from token_type import *

simple_one_char_lexemes = {
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

simple_two_char_lexemes = {
    "!": ("=", (BANG_EQUAL, BANG)),
    "=": ("=", (EQUAL_EQUAL, EQUAL)),
    "<": ("=", (LESS_EQUAL, LESS)),
    ">": ("=", (GREATER_EQUAL, GREATER))
}

keyword_lexemes = {
    "and": AND,
    "class": CLASS,
    "else": ELSE,
    "false": FALSE,
    "for": FOR,
    "fun": FUN,
    "if": IF,
    "nil": NIL,
    "or": OR,
    "print": PRINT,
    "return": RETURN,
    "super": SUPER,
    "this": THIS,
    "true": TRUE,
    "var": VAR,
    "while": WHILE,
}

class Scanner:
    def __init__(self, source):
        self.source = source
        self.tokens = []

        self.start = 0
        self.current = 0
        self.line = 1

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def scan_tokens(self) -> list[Token]:
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()

        self.tokens.append(Token(EOF, "", None, self.line))

        return self.tokens
    
    def advance(self) -> str:
        self.current += 1
        return self.source[self.current - 1]
    
    def add_token(self, ttype: TokenType, literal: object=None):
        text = self.source[self.start:self.current]
        self.tokens.append(Token(ttype, text, literal, self.line))

    def match(self, expected: str) -> bool:
        if self.is_at_end(): 
            return False
        if self.source[self.current] != expected:
            return False
    
        self.current += 1
        return True
    
    @staticmethod
    def is_digit(c: str) -> bool:
        return '0' <= c <= '9'
    
    @staticmethod
    def is_alpha(c: str) -> bool:
        return 'a' <= c <= 'z' or 'A' <= c <= 'Z' or c == '_'
    
    def is_alphanum(self, c: str) -> bool:
        return self.is_alpha(c) or self.is_digit(c)
    
    def peek(self) -> str:
        if self.is_at_end():
            return '\0'
        return self.source[self.current]
    
    def peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]
    
    def scan_token(self):
        c = self.advance()
        if c in simple_one_char_lexemes:
            self.add_token(simple_one_char_lexemes[c])
        elif c in simple_two_char_lexemes:
            expect_char, ttypes = simple_two_char_lexemes[c]
            ttype = ttypes[0] if self.match(expect_char) else ttypes[1]
            self.add_token(ttype)
        elif c == "/":
            if self.match("/"):  # Double slash => comment
                while self.peek() != "\n" and not self.is_at_end():
                    self.advance()
            elif self.match("*"):  # /* => Start of block comment
                prev = self.peek()
                while not (prev == "*" and self.peek() == "/"):
                    if self.is_at_end():
                        lox.Lox.scan_error(self.line, "Unterminated block comment")
                        break
                    
                    prev = self.advance()

                if not self.is_at_end():
                    self.advance()
            else:
                self.add_token(SLASH)
        elif c in (' ', '\t', '\r', '\n'):
            # Ignore whitespace, except newlines where we increment line no.
            self.line += c == '\n'
        elif c == '"':
            self.string()
        elif self.is_digit(c):
            self.number()
        elif self.is_alpha(c):
            self.identifier()
        else:
            lox.Lox.scan_error(self.line, "Unexpected character")

    def identifier(self):
        while self.is_alphanum(self.peek()):
            self.advance()

        text = self.source[self.start:self.current]
        ttype = keyword_lexemes.get(text, IDENTIFIER)

        self.add_token(ttype)

    def number(self):
        while self.is_digit(self.peek()):
            self.advance()

        if self.peek() == '.' and self.is_digit(self.peek_next()):
            self.advance()  # consume the dot
            while self.is_digit(self.peek()):
                self.advance()

        text = self.source[self.start:self.current]
        self.add_token(NUMBER, float(text))
        
    def string(self):
        # Note: the implementation diverges from the book here:
        # We don't support multi-line strings
        while self.peek() not in ('"', '\n') and not self.is_at_end():
            self.advance()

        if self.is_at_end() or self.peek() == '\n':
            lox.Lox.scan_error(self.line, "Unterminated string.")
            return
        
        # Move over the closing '"'
        self.advance()

        string_value = self.source[self.start+1 : self.current-1]  # exclude quotes
        self.add_token(STRING, string_value)

            



