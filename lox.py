import sys
from expr_ast import print_expr
from lox_token import Token
import token_type as TokenType

import scanner as scanner_module
import lox_parser as parser_module

class Lox:
    @classmethod
    def __new__(_cls, _name):
        raise ValueError("Class should not be instantiated")
    
    had_error = False

    @staticmethod
    def scan_error(line: int, message: str):
        Lox.report(line, "", message)
    
    @staticmethod
    def parse_error(token: Token, message: str):
        if token.type == TokenType.EOF:
            Lox.report(token.line, " at end", message)
        else:
            Lox.report(token.line, " at '" + token.lexeme + "'", message)

    @staticmethod
    def report(line: int, where: str, message: str):
        Lox.had_error = True
        
        print(f"[line {line}] Error{where}: {message}", file=sys.stderr)

    @staticmethod
    def run_file(file_name: str):
        with open(file_name, mode="r", encoding="utf-8") as f:
            source = f.read()
        
        Lox.run(source)
        if Lox.had_error:
            sys.exit(65)

    @staticmethod
    def run_prompt():
        while True:
            try:
                line = input("> ")
            except EOFError:
                break

            Lox.run(line)
            Lox.had_error = False
            

    @staticmethod
    def run(source: str):
        scanner = scanner_module.Scanner(source)
        tokens = scanner.scan_tokens()

        parser = parser_module.Parser(tokens)
        expression = parser.parse()

        print(print_expr(expression))

if __name__ == '__main__':
    args = sys.argv
    if len(args) > 2:
        print("Usage: plox [script]")
        sys.exit(64)
    elif len(args) == 2:
        Lox.run_file(args[1])
    else:
        Lox.run_prompt()
