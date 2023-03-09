from typing import NamedTuple

from token_type import TokenType

class Token(NamedTuple):
    type: TokenType
    lexeme: str
    literal: object
    line: int

    def __str__(self) -> str:
        return f"{self.type} {self.lexeme} {self.literal}"