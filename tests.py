import subprocess
from subprocess import PIPE

import unittest

def process_stdout(data: bytearray):
    s = data.decode('utf-8')
    s = s.strip().replace("\r\n", "\n")
    return s

def process_expected(s: str):
    return "\n".join(
        line.strip() for line in s.splitlines()
    ).strip()

def process_stderr(data: bytearray):
    return data.decode("utf-8")

def exec_program(program, timeout=1):
    proc = subprocess.Popen(
        ["python", "lox.py", "--"], 
        stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate(program.encode("utf-8"), timeout=timeout)
    return process_stdout(stdout), process_stderr(stderr)

class Tests(unittest.TestCase):
    def test_print_literals(self):
        program = """
            print 1;
            print -1;
            print 1.25;
            print -1.25;
            print true;
            print false;
            print nil;
            print "hello";
        """

        expected = process_expected("""
            1
            -1
            1.25
            -1.25
            true
            false
            nil
            hello
        """)

        stdout, stderr = exec_program(program)
        self.assertEqual(expected, stdout)
        self.assertEqual("", stderr)

    def test_assignment(self):
        program = """
        var a = 1;
        var b = 2;
        var c;
        c = a + b;
        print c;
        """
        expected = process_expected("3")
        
        stdout, stderr = exec_program(program)
        self.assertEqual(expected, stdout)
        self.assertEqual("", stderr)

    def test_assignment_expr(self):
        program = """
        var a; var b; var c;
        a = b = c = 2;
        print a == b and b == c;
        """
        expected = process_expected("true")
        
        stdout, stderr = exec_program(program)
        self.assertEqual(expected, stdout)
        self.assertEqual("", stderr)

    def test_if(self):
        ...

    def test_while(self):
        program_1 = """
        while (false) print 1;
        """
        expected_1 = ""

        stdout_1, stderr_1 = exec_program(program_1)
        self.assertEqual(expected_1, stdout_1)
        self.assertEqual("", stderr_1)

        program_2 = """
        var a = 1;
        while (a) { print a; a = 0; }
        """
        expected_2 = "1"
        stdout_2, stderr_2 = exec_program(program_2)
        self.assertEqual(expected_2, stdout_2)
        self.assertEqual("", stderr_2)

        # Fibonacci numbers below 20
        program_3 = """
        var temp;
        var a = 1;
        var b = 1;
        while (a < 20) { 
            print a;
            temp = a;
            a = b;
            b = temp + b;
        }
        """
        expected_3 = process_expected("\n".join(map(str, [1,1,2,3,5,8,13])))
        stdout_3, stderr_3 = exec_program(program_3)
        self.assertEqual(expected_3, stdout_3)
        self.assertEqual("", stderr_3)

    def test_while_nested(self):
        program = """
        var a = 1;
        while (a < 5) {
            var b = a;
            while (b < 5) {
                var c = b;
                while (c < 10) {
                    c = c + 1;
                }
                b = c;
            }
            a = b;
            while (a < 5) {
                a = 1000;
            }
        }
        print a;
        """
        expected = "10"

        stdout, stderr = exec_program(program)
        self.assertEqual(expected, stdout)
        self.assertEqual("", stderr)

    def test_break(self):
        ...
    
    def test_break_nested(self):
        ...

    def test_break_errors(self):
        prog_1 = "break;"
        stdout_1, stderr_1 = exec_program(prog_1)
        self.assertEqual("", stdout_1)
        self.assertEqual(
            stderr_1.strip(), 
            "[line 1] Error at 'break': Expect 'break' to appear inside a loop."
        )

        prog_2 = """
           while (false) break;
           break; 
        """
        stdout_2, stderr_2 = exec_program(prog_2)
        self.assertEqual("", stdout_2)
        self.assertEqual(
            stderr_2.strip(), 
            "[line 1] Error at 'break': Expect 'break' to appear inside a loop."
        )

        prog_3 = """
           break; 
           while (false) break;
        """
        stdout_3, stderr_3 = exec_program(prog_3)
        self.assertEqual("", stdout_3)
        self.assertEqual(
            stderr_3.strip(), 
            "[line 1] Error at 'break': Expect 'break' to appear inside a loop."
        )
            
        



    



# TODO: Test the following
# * expressions: all mathematical operators, string concat, logical operators (==, <, >, !), unary ops
# * and, or
# * Bracketing
# * Expression precedence
# * Statements: If, For, While
# * Blocks: shadowing, nesting, 
# * Error handling: scanning, parsing and runtime errors
#   * Var declaration after if/while/for without block

    


    
