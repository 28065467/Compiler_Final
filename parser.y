%{
    #include <iostream>
%}

%token IDENTIFIER CONSTANT
%token IF WHILE 
%token LPAREN RPAREN LBPAREN RBPAREN
%token ASSIGN EQUAL SMALLER LARGER ESMALLER ELARGER
%token PLUS MINUS DIV MUL 
%token DOT COMMA

%start PROGRAM

%%
    PROGRAM
        : declaration statement
        ;
    declaration
        : IDENTIFIER CONSTANT
        | IDENTIFIER CONSTANT declaration
        ;
    statement
        : statement_list statement
        ;
    statement_list
        :if_statement | while_statement | assign_statement | declaration 
        | 
        ;
    if_statement
        : IF '(' condition ')' '{' statement '}'
        ;
    assign_statement
        : IDENTIFIER ASSIGN factor
    while_statement
        : WHILE '(' condition ')' '{' statement '}'
        ;
    condition
        :  expression conditional_operator expression
        ;
    conditional_operator
        : EQUAL|SMALLER|LARGER|ESMALLER|ELARGER
        ;
    expression
        : term
        | expression PLUS term
        | expression MINUS term 
        ;
    term
        : factor  
        | factor MUL factor
        | factor DIV factor
        ;
    factor
        : IDENTIFIER | CONSTANT
        ;
%%