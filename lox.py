import sys
from lox_token import Token
from stmt_ast import ExpressionStmt, PrintStmt
import token_type as TokenType


import scanner as scanner_module
import lox_parser as parser_module
import interpreter as interpreter_module
import resolver as resolver_module
from error import LoxRuntimeError

class Lox:
    @classmethod
    def __new__(_cls, _name):
        raise ValueError("Class should not be instantiated")
    
    had_error = False
    had_runtime_error = False

    interpreter = interpreter_module.Interpreter()

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
    def runtime_error(error: LoxRuntimeError):
        print(f"[line {error.token.line}] Error: {error.message}", file=sys.stderr)
        Lox.had_runtime_error = True

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
        elif Lox.had_runtime_error:
            sys.exit(70)

    @staticmethod
    def run_prompt():
        while True:
            try:
                line = input("> ")
            except EOFError:
                break

            Lox.repl_run(line)
            Lox.had_error = False
            # TODO Lox.had_runtime_error = False ??

    @staticmethod
    def repl_run(line: str):
        scanner = scanner_module.Scanner(line)
        tokens = scanner.scan_tokens()

        parser = parser_module.Parser(tokens)
        statements = parser.parse()
        
        # Turn expressions into print statements so they get printed
        statements = [
            PrintStmt(statement.expression) if type(statement) == ExpressionStmt
            else statement
            for statement in statements
        ]

        resolver = resolver_module.Resolver(Lox.interpreter)
        resolver.resolve(statements)
        
        if Lox.had_error:
            Lox.interpreter.interpret(statements)

    @staticmethod
    def run(source: str):
        scanner = scanner_module.Scanner(source)
        tokens = scanner.scan_tokens()

        parser = parser_module.Parser(tokens)
        statements = parser.parse()
        
        if Lox.had_error:  # TODO: Figure out why had_error is not True after errors
            return
            
        resolver = resolver_module.Resolver(Lox.interpreter)
        resolver.resolve(statements)

        if Lox.had_error:
            Lox.interpreter.interpret(statements)

    @staticmethod
    def stdin_run():
        source = ""
        while True:
            try:
                source += input()
            except EOFError:
                Lox.run(source)
                return


if __name__ == '__main__':
    args = sys.argv
    if len(args) > 2:
        print("Usage: plox [script]")
        sys.exit(64)
    elif len(args) == 2:
        if args[1] == "--":
            Lox.stdin_run()
        else:
            Lox.run_file(args[1])
    else:
        Lox.run_prompt()
