import mypl_token as token 
import mypl_ast as ast 
import mypl_error as error 
import mypl_symbol_table as symbol_table
import copy

class TypeChecker(ast.Visitor): 
    """A MyPL type checker visitor implementation 
    where struct types take the form: type_id -> {v1:t1, ..., vn:tn} 
    and function types take the form: fun_id -> [[t1, t2, ..., tn,], return_type] """
    
    def __init__(self): 
        # initialize the symbol table (for ids -> types) 
        self.sym_table = symbol_table.SymbolTable() 
        # current_type holds the type of the last expression type 
        self.current_type = None 
        #checks to see if we are inside a struct
        self.inStruct = False
        #dictionary for holding values for the dictionary
        self.dict = {}
        # global env (for return) 
        self.sym_table.push_environment() 
        # set global return type to int 
        self.sym_table.add_id('return') 
        self.sym_table.set_info('return', token.INTTYPE) 
        # load in built-in function types 
        self.sym_table.add_id('print') 
        self.sym_table.set_info('print', [[token.STRINGVAL], token.NIL]) 
        self.sym_table.add_id('pass')
        self.sym_table.set_info('pass', token.INTTYPE)
        self.sym_table.add_id('reads')
        self.sym_table.set_info('reads', [[],token.STRINGVAL])
        self.sym_table.add_id('length')
        self.sym_table.set_info('length', [[token.STRINGVAL], token.INTVAL])
        self.sym_table.add_id('get')
        self.sym_table.set_info('get', [[token.INTVAL, token.STRINGVAL], token.STRINGVAL])
        self.sym_table.add_id('stof')
        self.sym_table.set_info('stof', [[token.STRINGVAL], token.FLOATVAL])
        self.sym_table.add_id('ftos')
        self.sym_table.set_info('ftos', [[token.FLOATVAL], token.STRINGVAL])
        self.sym_table.add_id('itof')
        self.sym_table.set_info('itof', [[token.INTVAL], token.FLOATVAL])
        self.sym_table.add_id('itos')
        self.sym_table.set_info('itos', [[token.INTVAL], token.STRINGVAL])
        self.sym_table.add_id('stoi')
        self.sym_table.set_info('stoi', [[token.STRINGVAL], token.INTVAL])
        self.sym_table.add_id('reads')
        self.sym_table.set_info('reads', [[], token.STRINGVAL])
        self.sym_table.add_id('readf')
        self.sym_table.set_info('readf', [[], token.FLOATVAL])
        
        
    def visit_stmt_list(self, stmt_list): 
        # add new block (scope) 
        self.sym_table.push_environment() 
        for stmt in stmt_list.stmts:
            self.current_type = None;
            stmt.accept(self) 
        # remove new block 
        self.sym_table.pop_environment()
        
    def visit_expr_stmt(self, expr_stmt): 
        expr_stmt.expr.accept(self)
        
    def visit_var_decl_stmt(self, var_decl):
        var_decl.var_expr.accept(self) 
        exp_type = self.current_type.lexeme 
        var_id = var_decl.var_id 
        curr_env = self.sym_table.get_env_id()
        # check that variable isn't already defined 
        if self.sym_table.id_exists_in_env(var_id.lexeme, curr_env): 
            msg = 'variable already defined in current environment' 
            self.__error(msg, var_id)   
    
        lhs = var_decl.var_type
        #if not self.sym_table.id_exists(var_decl.var_id.lexeme):
        self.sym_table.add_id(var_decl.var_id.lexeme)
        var_decl.var_expr.accept(self)
        rhs = self.current_type
        
        if var_decl.var_type != None:
            check = False
            if lhs.tokentype == token.INTTYPE:
                lhs = token.INTVAL
            elif lhs.tokentype == token.STRINGTYPE:
                lhs = token.STRINGVAL
            elif lhs.tokentype == token.FLOATTYPE:
                lhs = token.FLOATVAL
            elif lhs.tokentype == token.BOOLTYPE:
                lhs = token.BOOLVAL
            elif lhs.tokentype == token.ID:
                if not self.sym_table.id_exists(lhs.lexeme):
                    message = lhs.lexeme + " does not exist"
                    raise error.MyPLError(message, lhs.column, lhs.line)
                lhs = lhs.lexeme
            self.sym_table.set_info(var_decl.var_id.lexeme, lhs)    
            if lhs != rhs.tokentype and rhs.tokentype != token.NIL:
                message = "cant assign a " + rhs.tokentype + " to a " + lhs
                raise error.MyPLError(message, rhs.line, rhs.column)
            if self.inStruct:
                self.dict[var_decl.var_id.lexeme] = lhs
        else:
            self.sym_table.set_info(var_decl.var_id.lexeme, rhs.tokentype)
            if rhs.tokentype == token.NIL:
                raise error.MyPLError("can only assign a nil to an explicitly defined variable", rhs.line, rhs.column)
            if self.inStruct:
                self.dict[var_decl.var_id.lexeme] = rhs.tokentype
        
    def visit_assign_stmt(self, assign_stmt):
        assign_stmt.lhs.accept(self) 
        lhs_type = self.current_type 
        assign_stmt.rhs.accept(self) 
        rhs_type = self.current_type.tokentype
        temp = self.current_type
        if rhs_type != token.NIL and rhs_type != lhs_type: 
            msg = 'mismatch type in assignment ' + lhs_type + " " + rhs_type 
            raise error.MyPLError(msg, temp.line, temp.column)
    
    def visit_simple_expr(self, simpleExpr):
        simpleExpr.term.accept(self)
        
    def visit_simple_rvalue(self, rvalue):
        self.current_type = rvalue.val
        if rvalue.val.tokentype == token.ID:
            if not self.sym_table.id_exists(rvalue.val.lexeme):
                message = rvalue.val.lexeme + " does not exist"
                raise error.MyPLError(message, rvalue.val.column, rvalue.val.line)
            temp = self.sym_table.get_info(rvalue.val.lexeme)
            self.current_type = copy.deepcopy(rvalue.val)
            self.current_type.tokentype = temp
    
    def visit_new_rvalue(self, newStmt):
        if not self.sym_table.id_exists(newStmt.struct_type.lexeme):
            message = newStmt.struct_type.lexeme + " does not exist"
            raise error.MyPLError(message, newStmt.struct_type.column, newStmt.struct_type.line)
        self.current_type = newStmt.struct_type
        self.current_type.tokentype = newStmt.struct_type.lexeme
    
    def visit_id_rvalue(self, idrVal):
        if len(idrVal.path) == 1:
            if not self.sym_table.id_exists(idrVal.path[0].lexeme):
                message = idrVal.path[0].lexeme + " does not exist"
                raise error.MyPLError(message, idrVal.path[0].column, idrVal.path[0].line)
            temp = self.sym_table.get_info(idrVal.path[0].lexeme)
            self.current_type = idrVal.path[0]
            self.current_type.tokentype = temp
        else:
            temp = idrVal.path[0].lexeme
            if not self.sym_table.id_exists(temp):
                message = temp + "- does not exist"
                raise error.MyPLError(message, idrVal.path[i].line, idrVal.path[i].column)
            temp2 = self.sym_table.get_info(temp)
            i = 1;
            j = len(idrVal.path)
            while i < j - 1:
                if not self.sym_table.id_exists(temp2):
                    message = temp + " - does not exist"
                    raise error.MyPLError(message, idrVal.path[i].line, idrVal.path[i].column)
                temp = self.sym_table.get_info(temp2)
                type = temp[idrVal.path[i].lexeme]
                temp2 = type
                i += 1
            
            temp = self.sym_table.get_info(temp2)
            temp2 = temp[idrVal.path[-1].lexeme]
            
            if temp2 == token.INTTYPE:
                temp2 = token.INTVAL
            elif temp2 == token.FLOATTYPE:
                temp2 = token.FLOATVAL
            elif temp2 == token.BOOLTYPE:
                temp2 = token.BOOLVAL
            elif temp2 == token.STRINGTYPE:
                temp2 = token.STRINGVAL     
            self.current_type = idrVal.path[-1]
            self.current_type.tokentype = temp2
                

    def visit_call_rvalue(self, callStmt):
        if not self.sym_table.id_exists(callStmt.fun.lexeme):
            message = "function " + callStmt.fun.lexeme + " not recognized"
            raise error.MyPLError(message, callStmt.fun.line, callStmt.fun.column)
        temp = self.sym_table.get_info(callStmt.fun.lexeme)
        if len(temp[0]) != len(callStmt.args):
            raise error.MyPLError("wrong number of parameters " + callStmt.fun.lexeme, callStmt.fun.line, callStmt.fun.column)
        for i, x in enumerate(callStmt.args):
            x.accept(self)
            if(temp[0][i] != self.current_type.tokentype and self.current_type.tokentype != token.NIL):# and self.current_type.tokentype != token.ID):
                message = "parameter " + str(i) + " is the wrong type" + temp[0][i] + self.current_type.lexeme
                raise error.MyPLError(message, self.current_type.line, self.current_type.column)
        self.current_type = callStmt.fun
        self.current_type.tokentype = temp[1]
        temp2 = self.current_type.tokentype
        if temp2 == token.INTTYPE:
            temp2 = token.INTVAL
        elif temp2 == token.FLOATTYPE:
            temp2 = token.FLOATVAL
        elif temp2 == token.BOOLTYPE:
            temp2 = token.BOOLVAL
        elif temp2 == token.STRINGTYPE:
            temp2 = token.STRINGVAL     
        self.current_type.tokentype = temp2
    
    def visit_complex_expr(self, complExpr):
        complExpr.first_operand.accept(self)
        lhs = self.current_type
        complExpr.rest.accept(self)
        rhs = self.current_type
        if lhs.tokentype != rhs.tokentype or lhs.tokentype == token.BOOLVAL or lhs.tokentype == token.NIL:
            message = "cant combine a " + lhs.tokentype + " to a " + rhs.tokentype
            raise error.MyPLError(message, rhs.line, lhs.column)
        if  complExpr.math_rel.lexeme != '+' and lhs.tokentype == token.STRINGVAL:
            message = "can only add a " + lhs.tokentype + " to a " + rhs.tokentype
            raise error.MyPLError(message, rhs.line, lhs.column)
        self.current_type = lhs
        
    def visit_lvalue(self, lvalueStmt):
        if len(lvalueStmt.path) == 1:
            temp = lvalueStmt.path[-1].lexeme
            if not self.sym_table.id_exists(temp):
                message = temp + " is not initialized"
                raise error.MyPLError(message, lvalueStmt.path[-1].line, lvalueStmt.path[-1].column)
            self.current_type = self.sym_table.get_info(temp)
        else:
            temp = lvalueStmt.path[0].lexeme
            if not self.sym_table.id_exists(temp):
                message = temp + "- does not exist"
                raise error.MyPLError(message, lvalueStmt.path[i].line, lvalueStmt.path[i].column)
            temp2 = self.sym_table.get_info(temp)
            i = 1;
            j = len(lvalueStmt.path)
            while i < j - 1:
                if not self.sym_table.id_exists(temp2):
                    message = temp + "- does not exist"
                    raise error.MyPLError(message, lvalueStmt.path[i].line, lvalueStmt.path[i].column)
                temp = self.sym_table.get_info(temp2)
                type = temp[lvalueStmt.path[i].lexeme]
                temp2 = type
                i += 1
                
            #added this section in hw7 to get proper type
            temp = self.sym_table.get_info(temp2)
            temp2 = temp[lvalueStmt.path[-1].lexeme]
            
            if temp2 == token.INTTYPE:
                temp2 = token.INTVAL
            elif temp2 == token.FLOATTYPE:
                temp2 = token.FLOATVAL
            elif temp2 == token.BOOLTYPE:
                temp2 = token.BOOLVAL
            elif temp2 == token.STRINGTYPE:
                temp2 = token.STRINGVAL     
            #self.current_type = lvalueStmt.path[-1]
            self.current_type = temp2
        
    def visit_if_stmt(self, ifStmt):
        #if part
        ifStmt.if_part.bool_expr.accept(self)
        self.sym_table.push_environment()
        for x in ifStmt.if_part.stmt_list.stmts:
            self.current_type = None;
            x.accept(self) 
        self.sym_table.pop_environment()
        #elif part
        for x in ifStmt.elseifs:
            x.bool_expr.accept(self)
            self.sym_table.push_environment()
            for x in x.stmt_list.stmts:
                self.current_type = None;
                x.accept(self)
            self.sym_table.push_environment()
        #else
        if ifStmt.has_else:
            self.sym_table.push_environment()
            for x in ifStmt.else_stmts.stmts:
                self.current_type = None
                x.accept(self)
            self.sym_table.pop_environment()
    
    def visit_bool_expr(self, boolStmt):
        boolStmt.first_expr.accept(self)
        lhs = self.current_type
        if boolStmt.bool_rel != None:
            boolStmt.second_expr.accept(self)
            rhs = self.current_type
            if lhs.tokentype != rhs.tokentype and rhs.tokentype != token.NIL:
                message = "cant compare a " + lhs.tokentype + " with a " + rhs.tokentype
                raise error.MyPLError(message, rhs.column, rhs.line)
            if boolStmt.bool_rel.lexeme != "!=" and boolStmt.bool_rel.lexeme != "==" and rhs.tokentype == token.NIL:
                raise error.MyPLError("can only check if == or != with nil", rhs.line, rhs.column)
        if boolStmt.bool_connector != None:
            boolStmt.rest.accept(self)            

    def visit_while_stmt(self, whileStmt):
        whileStmt.bool_expr.accept(self)
        self.sym_table.push_environment()
        for x in whileStmt.stmt_list.stmts:
            self.current_type = None
            x.accept(self)
        self.sym_table.pop_environment()
    
    def visit_struct_decl_stmt(self, structStmt):
        self.sym_table.add_id(structStmt.struct_id.lexeme)
        self.inStruct = True
        #self.sym_table.set_info(structStmt.struct_id.lexeme, structStmt.struct_id.lexeme)
        self.sym_table.push_environment()
        for x in structStmt.var_decls:
            x.accept(self)
        self.sym_table.pop_environment()
        self.sym_table.set_info(structStmt.struct_id.lexeme, self.dict)
        self.inStruct = False
        self.dict = {}
    
    def visit_fun_decl_stmt(self, funStmt):
        self.sym_table.add_id(funStmt.fun_name.lexeme)
        param = []
        paramNames = []
        type = []       
        self.sym_table.push_environment()
        for x in funStmt.params:
            x.accept(self)
            if self.current_type.lexeme in paramNames:
                message = "cant have parameters with the same name" + self.current_type.lexeme
                raise error.MyPLError(message, self.current_type.column, self.current_type.line)
            param.append(self.current_type.tokentype)
            paramNames.append(self.current_type.lexeme)
        type.append(param)
        temp2 = funStmt.return_type.tokentype
        if temp2 == token.INTTYPE:
            temp2 = token.INTVAL
        elif temp2 == token.FLOATTYPE:
            temp2 = token.FLOATVAL
        elif temp2 == token.BOOLTYPE:
            temp2 = token.BOOLVAL
        elif temp2 == token.STRINGTYPE:
            temp2 = token.STRINGVAL     
        if funStmt.return_type.tokentype != token.ID:
            type.append(funStmt.return_type.tokentype)
        else:
            type.append(funStmt.return_type.lexeme)
        self.sym_table.set_info(funStmt.fun_name.lexeme, type)
        
        temp = self.sym_table.get_info("return")      
        self.sym_table.set_info("return", funStmt.return_type.tokentype)
        for x in funStmt.stmt_list.stmts:
            self.current_type = None
            x.accept(self)
        self.sym_table.pop_environment()
        self.sym_table.set_info("return", temp)
        
    def visit_fun_param(self, paramStmt):
        self.current_type = token.Token("temp", "temp", 0, 0)
        self.current_type.lexeme = paramStmt.param_name.lexeme
        self.sym_table.add_id(paramStmt.param_name.lexeme)
        temp = ""
        if paramStmt.param_type.tokentype == token.INTTYPE:
            temp = token.INTVAL
        elif paramStmt.param_type.tokentype == token.STRINGTYPE:
            temp = token.STRINGVAL
        elif paramStmt.param_type.tokentype == token.BOOLTYPE:
            temp = token.BOOLVAL
        elif paramStmt.param_type.tokentype == token.FLOATTYPE:
            temp = token.FLOATVAL
        elif paramStmt.param_type.tokentype == token.ID:
            temp = paramStmt.param_type.lexeme
        self.sym_table.set_info(paramStmt.param_name.lexeme, temp)
        self.current_type.tokentype = temp
        
    def visit_return_stmt(self, returnStmt):
        temp = self.sym_table.get_info("return")
        if temp != 'NIL':
            returnStmt.return_expr.accept(self)
        if temp == token.INTTYPE:
            temp = token.INTVAL
        elif temp == token.STRINGTYPE:
            temp = token.STRINGVAL
        elif temp == token.BOOLTYPE:
            temp = token.BOOLVAL
        elif temp == token.FLOATTYPE:
            temp = token.FLOATVAL
#        if temp != self.current_type.tokentype and self.current_type.tokentype != token.NIL and temp != token.NIL:
#            message = "mismatch in return type with function type" + self.current_type.tokentype + " " + temp
#            raise error.MyPLError(message, returnStmt.return_token.column, returnStmt.return_token.line)

        
            
    
            
                
                
                
                
                
                
                
                