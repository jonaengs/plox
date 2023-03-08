from typing import NamedTuple

from token_type import TokenType

class Token(NamedTuple):
    token_type: TokenType
    lexeme: str
    literal: object
    line: int

    def __str__(self) -> str:
        return f"{self.token_type} {self.lexeme} {self.literal}"