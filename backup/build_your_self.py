import sys
import re
import PyInstaller.__main__

keywords = ['IF' , 'WHILE' , 'ELSE' , 'PRINTF']
def lexer(code):
    token_specification = [
        ('NUMBER',   r'\d+(\.\d*)?'),       
        ('IDENT',    r'[A-Za-z_]\w*'),      
        ('ASSIGN',   r'='),                 
        ('END',      r';'),                 
        ('ADD',      r'\+'),               
        ('SUB',      r'-'),                 
        ('MUL',      r'\*'),              
        ('DIV',      r'/'),                
        ('LPAREN',   r'\('),             
        ('RPAREN',   r'\)'),              
        ('LBRACE',   r'\{'),              
        ('RBRACE',   r'\}'),                               
        ('GT',       r'>'),                
        ('LT',       r'<'),                
        ('SKIP',     r'[ \t\n]+|"%d" ,'),         
        ('MISMATCH', r'.'),                
    ]
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    tokens = []
    line_num = 1
    line_start = 0
    for mo in re.finditer(tok_regex, code):
        kind = mo.lastgroup
        value = mo.group()
        column = mo.start() - line_start
        if kind == 'NUMBER':
            value = float(value) if '.' in value else int(value)
            tokens.append((kind, value, line_num, column))
        elif kind == 'IDENT':
            for keyword in keywords:
                if keyword == value:
                    value = keyword
            if value != 'int': 
                tokens.append((kind, value, line_num, column))
        elif kind == 'SKIP':
            if '\n' in value:
                line_start = mo.end()
                line_num += value.count('\n')
            continue
        elif kind == 'MISMATCH':
            raise RuntimeError(f'{value!r} unexpected on line {line_num}')
        else:
            tokens.append((kind, value, line_num, column))
    return tokens
class Parser:
    def __init__(self,token):
        self.tokens = token
        self.pos = 0
        
    def parse(self):
        statements = []
        while self.current_token():
            statements.append(self.statement())
        return statements

    def statement(self):
        if self.current_token() == 'IF':
            return self.if_statement()
        elif self.current_token() == 'WHILE':
            return self.while_statement()
        elif self.current_token() == 'PRINTF':
            return self.printf_statement()
        elif self.current_token() == 'IDENT' and self.peek_token() == 'ASSIGN':
            return self.assignment()
        else:
            raise RuntimeError(f'Unexpected token: {self.current_token()}')

    def assignment(self):
        var_name = self.match('IDENT')[1]
        self.match('ASSIGN')
        expr = self.expression()
        self.match('END')
        return ('ASSIGN', var_name, expr)

    def if_statement(self):
        self.match('IF')
        self.match('LPAREN')
        condition = self.expression()
        self.match('RPAREN')
        self.match('LBRACE')
        then_branch = []
        while self.current_token() != 'RBRACE':
            then_branch.append(self.statement())
        self.match('RBRACE')
        return ('IF', condition, then_branch)
    
    def while_statement(self):
        self.match('WHILE')
        self.match('LPAREN')
        condition = self.expression()
        self.match('RPAREN')
        self.match('LBRACE')
        body = []
        while self.current_token() != 'RBRACE':
            body.append(self.statement())
        self.match('RBRACE')
        return ('WHILE', condition, body)
    
    def printf_statement(self):
        self.match('PRINTF')
        self.match('LPAREN')
        var_name = self.match('IDENT')[1]
        self.match('RPAREN')
        self.match('END')
        return ('PRINTF', var_name)
    
    def expression(self):
        node = self.term()
        while self.current_token() in ('ADD', 'SUB', 'GT', 'LT'):
            token = self.current_token()
            self.next_token()
            if token == 'ADD':
                node = ('ADD', node, self.term())
            elif token == 'SUB':
                node = ('SUB', node, self.term())
            elif token == 'GT':
                node = ('GT', node, self.term())
            elif token == 'LT':
                node = ('LT', node, self.term())
        return node

    def term(self):
        node = self.factor()
        while self.current_token() in ('MUL', 'DIV'):
            token = self.current_token()
            self.next_token()
            if token == 'MUL':
                node = ('MUL', node, self.factor())
            elif token == 'DIV':
                node = ('DIV', node, self.factor())
        return node

    def factor(self):
        token = self.current_token()
        if token == 'NUMBER':
            self.next_token()
            return ('NUMBER', self.tokens[self.pos - 1][1])
        elif token == 'IDENT':
            self.next_token()
            return ('IDENT', self.tokens[self.pos - 1][1])
        elif token == 'LPAREN':
            self.next_token()
            node = self.expression()
            self.match('RPAREN')
            return node

    def current_token(self):
        if self.pos < len(self.tokens):
            if self.tokens[self.pos][1] == 'if':
                return 'IF'
            elif self.tokens[self.pos][1] == 'while':
                return 'WHILE'
            elif self.tokens[self.pos][1] == 'printf':
                return 'PRINTF'
            else:
                return self.tokens[self.pos][0]
        return None

    def peek_token(self):
        if self.pos + 1 < len(self.tokens):
            if self.tokens[self.pos+1][1] == 'if':
                return 'IF'
            elif self.tokens[self.pos+1][1] == 'while':
                return 'WHILE'
            elif self.tokens[self.pos+1][1] == 'printf':
                return 'PRINTF'
            return self.tokens[self.pos + 1][0]
        return None

    def next_token(self):
        self.pos += 1

    def match(self, token_type):
        if self.current_token() != token_type:
            raise RuntimeError(f'Expected {token_type} but got {self.current_token()}')
        if self.tokens[self.pos][1] == 'if':
            token = 'IF'
        elif self.tokens[self.pos][1] == 'while':
            token = 'WHILE'
        elif self.tokens[self.pos][1] == 'printf':
            token = 'PRINTF'
        else:
            token = self.tokens[self.pos]
        self.next_token()
        return token
    
def generate_code(statements):
    code = []
    for stmt in statements:
        if stmt[0] == 'ASSIGN':
            code.append(f"{stmt[1]} = {generate_expr(stmt[2])}")
        elif stmt[0] == 'IF':
            code.append(f"if {generate_expr(stmt[1])}:")
            for sub_stmt in stmt[2]:
                code.append(f"    {generate_code([sub_stmt])}")
        elif stmt[0] == 'WHILE':
            code.append(f"while {generate_expr(stmt[1])}:")
            for sub_stmt in stmt[2]:
                code.append(f"    {generate_code([sub_stmt])}")
        elif stmt[0] == 'PRINTF':
            code.append(f"print({stmt[1]})")
    return '\n'.join(code)

def generate_expr(node):
    if node[0] == 'NUMBER':
        return str(node[1])
    elif node[0] == 'IDENT':
        return node[1]
    elif node[0] == 'ADD':
        return f"({generate_expr(node[1])} + {generate_expr(node[2])})"
    elif node[0] == 'SUB':
        return f"({generate_expr(node[1])} - {generate_expr(node[2])})"
    elif node[0] == 'MUL':
        return f"({generate_expr(node[1])} * {generate_expr(node[2])})"
    elif node[0] == 'DIV':
        return f"({generate_expr(node[1])} / {generate_expr(node[2])})"
    elif node[0] == 'GT':
        return f"({generate_expr(node[1])} > {generate_expr(node[2])})"
    elif node[0] == 'LT':
        return f"({generate_expr(node[1])} < {generate_expr(node[2])})"


def compile_code(code):
    tokens = lexer(code)
    #print(tokens)
    parser = Parser(tokens)
    statements = parser.parse()
    return generate_code(statements)

input_file = sys.argv[1]
with open(input_file, 'r') as file:
    code = file.read()
#file = open('test.c' , 'r')
#code = file.read()
#print(code)
file.close()
compiled = compile_code(code)
with open('output.py' , 'w') as file:
    file.write(compiled)
#print(compiled)
# PyInstaller.__main__.run([
#     'output.py',
#     '--onefile',     
#     '--clean',       
#     '--noconfirm'    
# ])
file.close()
exec(compiled)