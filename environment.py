from __future__ import annotations

import traceback

from error import LoxRuntimeError
from lox_token import Token


class Environment:
    def __init__(self, enclosing: Environment | None = None) -> None:
        self.values: dict[str, object] = {}
        self.enclosing = enclosing

    def define(self, name: str, value: object) -> None:
        self.values[name] = value

    def assign(self, token: Token, value: object) -> None:
        if token.lexeme in self.values:
            self.values[token.lexeme] = value
        elif self.enclosing is not None:
            self.enclosing.assign(token, value)
        else:
            raise LoxRuntimeError(token, f"Undefined variable '{token.lexeme}'.")

    def get(self, token: Token) -> object:
        if token.lexeme in self.values:
            return self.values[token.lexeme]
        if self.enclosing is not None:
            return self.enclosing.get(token)
        raise LoxRuntimeError(token, f"Undefined variable '{token.lexeme}'.")
    
    def get_at(self, distance: int, name: str) -> object:
        return self._ancestor(distance).values[name]
    
    def assign_at(self, distance: int, name: str, value: object):
        self._ancestor(distance).values[name] = value
    
    def _ancestor(self, distance: int) -> Environment:
        if distance == 0: return self
        return self.enclosing._ancestor(distance - 1)  # type: ignore[union-attr]
    
    def print_stack(self):
        print("-------------")
        print(self.values)
        if self.enclosing:
            self.enclosing.print_stack()