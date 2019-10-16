import mypl_error as error
import mypl_lexer as lexer
import mypl_token as token
import mypl_ast as ast 

class Parser(object):

    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = None

    def parse(self):
        """succeeds if program is syntactically well-formed"""
        stmt_list_node = ast.StmtList()
        self.__advance()
        self.__stmts(stmt_list_node)
        self.__eat(token.EOS, 'expecting end of file')
        return stmt_list_node

    def __advance(self):
        self.current_token = self.lexer.next_token()

    def __eat(self, tokentype, error_msg):
        if self.current_token.tokentype == tokentype:
            self.__advance()
        else:
            self.__error(error_msg)

    def __error(self, error_msg):
        error_msg = error_msg + ', found "' + self.current_token.lexeme + '" in parser'
        l = self.current_token.line
        c = self.current_token.column
        raise error.MyPLError(error_msg, l, c)

    # Beginning of recursive descent functions
    def __stmts(self, stmt_list_node):
        """<stmts> ::= <stmt> <stmts> | e"""
        if self.current_token.tokentype != token.EOS:
            self.__stmt(stmt_list_node)
            self.__stmts(stmt_list_node)

    def __stmt(self, stmt_list_node):
        """<stmt> ::= <sdecl> | <fdecl> | <bstmt>"""
        newNode = ast.Stmt() 
        if self.current_token.tokentype == token.STRUCTTYPE:
            newNode = self.__sdecl()
        elif self.current_token.tokentype == token.FUN:
            newNode = self.__fdecl()
        else:
            newNode = self.__bstmt()
        stmt_list_node.stmts.append(newNode)
        

    def __sdecl(self):
        """<sdecl> ::= STRUCT ID <vdecls> END """
        structNode = ast.StructDeclStmt()
        self.__eat(token.STRUCTTYPE, "expecting struct");
        structNode.struct_id = self.current_token
        self.__eat(token.ID, "expecting an id");
        self.__vdecls(structNode)
        self.__eat(token.END, "expecting an end");
        return structNode

    def __vdecls(self, nodeFromAbove):
        """<vdecls> ::= <vdecl><vdecls>| E"""
        if self.current_token.tokentype == token.VAR:
            varStmt = ast.VarDeclStmt()
            varStmt = self.__vdecl()
            nodeFromAbove.var_decls.append(varStmt)
            self.__vdecls(nodeFromAbove)

    def __vdecl(self):
        """<vdecl> ::= VAR ID <tdecl> ASSIGN <expr> SEMICOLON"""
        varStmt = ast.VarDeclStmt()
        self.__eat(token.VAR, "expecting var")
        varStmt.var_id = self.current_token
        self.__eat(token.ID, "Expecting an ID")
        varStmt.var_type = self.__tdecl()
        self.__eat(token.ASSIGN, "expecting an =")
        varStmt.var_expr = self.__expr()
        self.__eat(token.SEMICOLON, "expecting a ;")
        return varStmt

    def __tdecl(self):
        """<tdecl> ::= COLON <type>| E"""
        if self.current_token.tokentype == token.COLON:
            self.__advance()
            typeDec = self.__type()
            return typeDec
        return None
        
    def __type(self):
        """<type> ::= ID | INTTYPE | FLOATTYPE | BOOLTYPE | STRINGTYPE """
        temp = self.current_token.tokentype
        temp2 = self.current_token
        if temp == token.ID:
            self.__advance()
        elif temp == token.INTTYPE:
            self.__advance()
        elif temp == token.FLOATTYPE:
            self.__advance()
        elif temp == token.BOOLTYPE:
            self.__advance()
        elif temp == token.STRINGTYPE:
            self.__advance()
        else:
            self.__error("expecting an id, int, float, bool, or string")
        return temp2

    def __expr(self):
        """<expr> ::= ( <rvalue>| LPAREN <expr> RPAREN ) ( <mathrel><expr>| E )"""
        exprNode = ast.SimpleExpr()
        temp = 1
        if self.current_token.tokentype == token.LPAREN:
            self.__advance()
            exprNode = self.__expr()
            temp = exprNode.first_operand
            self.__eat(token.RPAREN, 'expecting ")"')
        else:
            exprNode.term = self.__rvalue()
            temp = exprNode.term
        mathrels = [token.PLUS, token.MINUS, token.DIVIDE, token.MULTIPLY, token.MODULO]
        if self.current_token.tokentype in mathrels:
            exprNode = ast.ComplexExpr()
            exprNode.first_operand = temp
            exprNode.math_rel = self.current_token
            self.__advance()
            exprNode.rest = self.__expr()
        return exprNode
        
    def __rvalue(self):
        """<rvalue> ::= STRINGVAL | INTVAL | BOOLVAL | FLOATVAL | NIL | NEW ID |<idrval>"""
        temp = self.current_token.tokentype
        rStmt = ast.SimpleRValue()
        rStmt.val = self.current_token
        if temp == token.STRINGVAL:
            self.__advance()
        elif temp == token.INTVAL:
            self.__advance()
        elif temp == token.BOOLVAL:
            self.__advance()
        elif temp == token.FLOATVAL:
            self.__advance()
        elif temp == token.NIL:
            self.__advance()
        elif temp == token.NEW:
            self.__advance()
            rStmt = ast.NewRValue()
            rStmt.struct_type = self.current_token
            self.__eat(token.ID, "expecting an id")
        else:
            rStmt = self.__idrval()
            #rStmt = ast.CallRValue()
            #rStmt.fun = self.current_token
            #self.__idrval(rStmt)
        return rStmt

    def __idrval(self):
        """<idrval> ::= ID ( DOT ID )* | ID LPAREN <exprlist> RPAREN"""
        rStmt = ast.SimpleRValue()
        rStmt.val = self.current_token 
        self.__eat(token.ID, "expecting ID")
        if self.current_token.tokentype == token.LPAREN:
            temp = rStmt.val
            rStmt = ast.CallRValue()
            rStmt.fun = temp
            self.__advance()
            self.__exprlist(rStmt)
            self.__eat(token.RPAREN, "expecting a ')'")
            return rStmt
        else:
            if self.current_token.tokentype == token.DOT:
                temp = rStmt.val
                rStmt = ast.IDRvalue()
                rStmt.path.append(temp)
                while self.current_token.tokentype == token.DOT:
                    self.__advance()     
                    temp = self.current_token
                    rStmt.path.append(temp)
                    self.__eat(token.ID, "expecting an ID")
        return rStmt


    def __exprlist(self, nodeFromAbove):
        # tokens that can start an expression ...
        types = [token.STRINGVAL, token.INTVAL, token.BOOLVAL, token.FLOATVAL, token.NIL, token.NEW, token.ID, token.LPAREN]
        if self.current_token.tokentype in types:
            nodeFromAbove.args.append(self.__expr())
            while self.current_token.tokentype == token.COMMA:
                self.__advance()
                nodeFromAbove.args.append(self.__expr())

    def __fdecl(self):
        """<fdecl> ::= FUN ( <type>| NIL ) ID LPAREN <params> RPAREN <bstmts> END"""
        funStmt = ast.FunDeclStmt()
        self.__eat(token.FUN, "expecting an fun")
        if self.current_token.tokentype == token.NIL:
            funStmt.return_type = self.current_token
            self.__advance()
        else:
            funStmt.return_type = self.__type()
        funStmt.fun_name = self.current_token
        self.__eat(token.ID, "expecting an id")
        self.__eat(token.LPAREN, "expecting an '('")
        self.__params(funStmt)
        self.__eat(token.RPAREN, "expecting an ')'")
        self.__bstmts(funStmt.stmt_list)
        self.__eat(token.END, "expecting an end")
        return funStmt

    def __params(self, nodeFromHeaven):
        """<params> ::= ID COLON <type> ( COMMA ID COLON <type> )* | E"""
        paramStmt = ast.FunParam()
        #print("ptest")
        if self.current_token.tokentype == token.ID:
            paramStmt.param_name = self.current_token
            self.__eat(token.ID, "expecting an ID")
            self.__eat(token.COLON, "expecting a ':'")
            paramStmt.param_type = self.__type()
            nodeFromHeaven.params.append(paramStmt)
            #print(paramStmt.param_name.lexeme, " " , nodeFromHeaven.params[0].param_name.lexeme)
            while self.current_token.tokentype == token.COMMA:
                paramStmt = ast.FunParam()
                self.__advance()
                paramStmt.param_name = self.current_token
                self.__eat(token.ID, "expecting an ID")
                self.__eat(token.COLON, "expecting a ':'")
                paramStmt.param_type = self.__type()
                nodeFromHeaven.params.append(paramStmt)
                #print(paramStmt.param_name.lexeme, " " , nodeFromHeaven.params[1].param_name.lexeme)
        #for x in nodeFromHeaven.params:
        #    print(x.param_name.lexeme)
        #print("ptest")

    def __bstmts(self, nodeFromAbove):
        """<bstmts> ::= <bstmt><bstmts>| E"""
        stuffThatStartsBstmt = [token.VAR, token.SET, token.IF, token.WHILE, token.RETURN, token.LPAREN, token.STRINGVAL, token.INTVAL, token.BOOLVAL, token.FLOATVAL, token.NIL, token.NEW, token.ID, token.PLUS, token.MINUS, token.DIVIDE, token.MULTIPLY, token.MODULO ] 
        if self.current_token.tokentype in stuffThatStartsBstmt:
            bstmtStmt = ast.Stmt()
            bstmtStmt = self.__bstmt()
            nodeFromAbove.stmts.append(bstmtStmt)
            self.__bstmts(nodeFromAbove)

    def __bstmt(self):
        """<bstmt> ::= <vdecl>|<assign>|<cond>|<while>|<expr> SEMICOLON |<exit>"""
        temp = self.current_token.tokentype
        bstmtStmt = ast.Stmt()
        exprStarts = [token.LPAREN, token.STRINGVAL, token.INTVAL, token.BOOLVAL, token.FLOATVAL, token.NIL, token.NEW, token.ID]
        if temp == token.VAR:
            bstmtStmt = self.__vdecl()
        elif temp == token.SET:
            bstmtStmt = self.__assign()
        elif temp == token.IF:
            bstmtStmt = self.__cond()
        elif temp == token.WHILE:
            bstmtStmt = self.__while()
        elif self.current_token.tokentype in exprStarts:
            bstmtStmt = ast.ExprStmt()
            bstmtStmt.expr = self.__expr()
            self.__eat(token.SEMICOLON, "expecting a ';'")
        else:
            bstmtStmt = self.__exit()
        return bstmtStmt

    def __assign(self):
        """<assign> ::= SET <lvalue> ASSIGN <expr> SEMICOLON"""
        assignStmt = ast.AssignStmt()
        self.__eat(token.SET, "expecting set")
        assignStmt.lhs = self.__lvalue()
        self.__eat(token.ASSIGN, "expecting '='")
        assignStmt.rhs = self.__expr()
        self.__eat(token.SEMICOLON, "expecting ';'")
        return assignStmt

    def __lvalue(self):
        """<lvalue> ::= ID ( DOT ID )∗"""
        lvalueStmt = ast.LValue()
        lvalueStmt.path.append(self.current_token)
        self.__eat(token.ID, "expecting ID")
        while self.current_token.tokentype == token.DOT:
            self.__advance()
            lvalueStmt.path.append(self.current_token)
            self.__eat(token.ID, "expecting ID")
        return lvalueStmt

    def __cond(self):
        """<cond> ::= IF <bexpr> THEN <bstmts><condt> END"""
        condStmt = ast.IfStmt()
        self.__eat(token.IF, "expecting an if")
        condStmt.if_part.bool_expr = self.__bexpr()
        self.__eat(token.THEN, "expecting then")
        self.__bstmts(condStmt.if_part.stmt_list)
        self.__condt(condStmt)
        self.__eat(token.END, "expecting an end")
        return condStmt

    def __bexpr(self):
        boolStmt = ast.BoolExpr()
        """<bexpr> ::= <expr><bexprt>| NOT <bexpr><bexprt> | LPAREN <bexpr> RPAREN <bconnct>"""
        temp = self.current_token.tokentype
        if temp == token.NOT:
            self.__advance()
            boolStmt = self.__bexpr()
            boolStmt.negated = True
            self.__bexprt(boolStmt)
        elif temp == token.LPAREN:
            self.__advance()
            boolStmt = self.__bexpr()
            self.__eat(token.RPAREN, "expecting a ')'")
            self.__bconnct(boolStmt)
        else:
            boolStmt.first_expr = self.__expr()
            self.__bexprt(boolStmt)
        return boolStmt

    def __bexprt(self, nodeFromAbove):
        """<bexprt> ::= <boolrel><expr><bconnct>|<bconnct>"""
        boolrelStuff = [ token.EQUAL, token.LESS_THAN, token.GREATER_THAN, token.LESS_THAN_EQUAL, token.GREATER_THAN_EQUAL, token.NOT_EQUAL]

        if self.current_token.tokentype in boolrelStuff:
            nodeFromAbove.bool_rel = self.__boolrel()
            nodeFromAbove.second_expr = self.__expr()
            self.__bconnct(nodeFromAbove)       
        else:
             self.__bconnct(nodeFromAbove)

    def __bconnct(self, nodeFromAbove):
        """<bconnct> ::= AND <bexpr>| OR <bexpr>| E"""
        if self.current_token.tokentype == token.AND:
            nodeFromAbove.bool_connector = self.current_token
            self.current_token = self.lexer.next_token()
            nodeFromAbove.rest = self.__bexpr()
        if self.current_token.tokentype == token.OR:
            nodeFromAbove.bool_connector = self.current_token
            self.current_token = self.lexer.next_token()
            nodeFromAbove.rest = self.__bexpr()

    def __boolrel(self):
        """<boolrel> ::= EQUAL | LESS_THAN | GREATER_THAN | LESS_THAN_EQUAL | GREATER_THAN_EQUAL | NOT_EQUAL"""
        temp = self.current_token.tokentype
        temp2 = self.current_token
        if temp == token.EQUAL:
            self.__advance()
            return temp2
        elif temp == token.LESS_THAN:
            self.__advance()
            return temp2
        elif temp == token.GREATER_THAN:
            self.__advance()
            return temp2
        elif temp == token.LESS_THAN_EQUAL:
            self.__advance()
            return temp2
        elif temp == token.GREATER_THAN_EQUAL:
            self.__advance()
            return temp2
        elif temp == token.NOT_EQUAL:
            self.__advance()
            return temp2
        return None

    def __condt(self, nodeFromAbove):
        """<condt> ::= ELIF <bexpr> THEN <bstmts><condt>| ELSE <bstmts>| * """
        condtStmt = ast.BasicIf()
        thingsThatStartBSTMTS = [token.VAR, token.SET, token.IF, token.WHILE, token.RETURN, token.LPAREN, token.STRINGVAL, token.INTVAL, token.BOOLVAL, token.FLOATVAL, token.NIL, token.NEW, token.ID]
        temp = self.current_token.tokentype
        if temp == token.ELIF:
            self.__advance()
            condtStmt.bool_expr = self.__bexpr()
            self.__eat(token.THEN, "expecting a then")
            self.__bstmts(condtStmt.stmt_list)
            nodeFromAbove.elseifs.append(condtStmt)
            self.__condt(nodeFromAbove)
        if temp == token.ELSE:
            self.__advance()
            nodeFromAbove.has_else = True
            if self.current_token.tokentype in thingsThatStartBSTMTS:
                self.__bstmts(nodeFromAbove.else_stmts)

    def __while(self):
        """<while> ::= WHILE <bexpr> DO <bstmts> END"""
        whileStmt = ast.WhileStmt()
        self.__eat(token.WHILE, "expecting a 'while'")
        whileStmt.bool_expr = self.__bexpr()
        self.__eat(token.DO, "expecting a 'do'")
        self.__bstmts(whileStmt.stmt_list)
        self.__eat(token.END, "expecting an 'end'")
        return whileStmt

    def __exit(self):
        """<exit> ::= RETURN ( <expr>| E ) SEMICOLON"""
        exitStmt = ast.ReturnStmt()
        exitStmt.return_token = self.current_token
        self.__eat(token.RETURN, "expecting 'return'")
        if self.current_token.tokentype != token.SEMICOLON:
            exitStmt.return_expr = self.__expr()
        self.__eat(token.SEMICOLON, "expecting a ';'")
        return exitStmt
