from typing import NamedTuple

from token_type import TokenType

Lox_Literal = float | str | bool | None

class Token(NamedTuple):
    type: TokenType
    lexeme: str
    literal: Lox_Literal
    line: int

    def __str__(self) -> str:
        return f"{self.type} {self.lexeme} {self.literal}"