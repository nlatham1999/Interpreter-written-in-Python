import mypl_token as token 
import mypl_ast as ast 
import mypl_error as error 
import mypl_symbol_table as sym_tbl

class ReturnException(Exception): pass

class Interpreter(ast.Visitor): 
    """A MyPL interpret visitor implementation"""
    
    def __init__(self): 
        # initialize the symbol table (for ids -> values) 
        self.sym_table = sym_tbl.SymbolTable() 
        # holds the type of last expression type 
        self.current_value = None
        self.current_token = None #keeps the curren token for error reporting
        self.expressionIsTrue = True #checks for conditional statements and loopss
        self.structDict = {} #holds values of varDecls of the struct
        self.inStruct = False #checks to see if enviroment is inside of a struct
        self.varId = "x" #holds the current var id
        # the heap {oid:struct_obj} 
        self.structId = 1
        self.heap = {}

    def __error(self, msg, the_token): 
        raise error.MyPLError(msg, the_token.line, the_token.column)
        
    def run(self, stmt_list): 
        try: 
            stmt_list.accept(self) 
        except ReturnException: 
            pass
        
    def visit_stmt_list(self, stmt_list): 
        #print("visit_stmt_list")
        self.sym_table.push_environment() 
        for stmt in stmt_list.stmts: 
            stmt.accept(self) 
        self.sym_table.pop_environment()

    def visit_expr_stmt(self, expr_stmt):
        #print("visit_expr_stmt")
        expr_stmt.expr.accept(self) 
    
    def visit_simple_expr(self, exprStmt):
        #print("visit_simple_expr")
        exprStmt.term.accept(self)
    
    def visit_complex_expr(self, compExpr):
        compExpr.first_operand.accept(self)
        temp = self.current_value
        compExpr.rest.accept(self)
        temp2 = self.current_value
        temp3 = compExpr.math_rel.lexeme
        if temp3 == '+':
            self.current_value = temp + temp2
        elif temp3 == '-':
            self.current_value = temp - temp2
        elif temp3 == '*':
            self.current_value = temp * temp2
        elif temp3 == '/':
            self.current_value = temp / temp2
        elif temp3 == '%':
            self.current_value = temp % temp2
        
    def visit_simple_rvalue(self, simple_rvalue): 
        #print("visit_simple_rvalue")
        if simple_rvalue.val.tokentype == token.INTVAL: 
            self.current_value = int(simple_rvalue.val.lexeme) 
        elif simple_rvalue.val.tokentype == token.FLOATVAL: 
            self.current_value = float(simple_rvalue.val.lexeme) 
        elif simple_rvalue.val.tokentype == token.BOOLVAL: 
            self.current_value = True 
            if simple_rvalue.val.lexeme == 'false': 
                self.current_value = False 
        elif simple_rvalue.val.tokentype == token.STRINGVAL: 
            self.current_value = simple_rvalue.val.lexeme 
        elif simple_rvalue.val.tokentype == token.NIL: 
            self.current_value = None
        elif simple_rvalue.val.tokentype == token.ID:
            self.current_value = self.sym_table.get_info(simple_rvalue.val.lexeme)
        self.current_token = simple_rvalue.val
            
    def visit_id_rvalue(self, id_rvalue): 
        #print("visit_id_rvalue")
        if len(id_rvalue.path) == 1:
            var_name = id_rvalue.path[0].lexeme 
            var_val = self.sym_table.get_info(var_name) 
        else:
            var_name = id_rvalue.path[0].lexeme
            var_val = self.sym_table.get_info(var_name)
            dict = 0
            for i, path_id in enumerate(id_rvalue.path):
                if i < len(id_rvalue.path) - 1:
                    dict = self.heap[var_val]
                    nextName = id_rvalue.path[i+1].lexeme
                    var_val = dict[nextName]
        self.current_value = var_val

    def visit_lvalue(self, lval):
        #print("visit_lvalue") 
        identifier = lval.path[0].lexeme 
        if len(lval.path) == 1: 
            self.sym_table.set_info(identifier, self.current_value) 
        else: 
            var_val = self.sym_table.get_info(identifier)
            dict = 0
            for i, x in enumerate(lval.path):
                if i < len(lval.path) - 1:
                    dict = self.heap[var_val]
                    identifier = lval.path[i + 1].lexeme
                    var_val = dict[identifier]
                else:
                    dict[x.lexeme] = self.current_value

    def visit_var_decl_stmt(self, var_decl): 
        var_decl.var_expr.accept(self) 
        exp_value = self.current_value 
        var_name = var_decl.var_id.lexeme 
        self.varId = var_name
        self.sym_table.add_id(var_decl.var_id.lexeme) 
        self.sym_table.set_info(var_decl.var_id.lexeme, exp_value)
        if self.inStruct:
            self.structDict[var_decl.var_id.lexeme] =  exp_value


    def visit_call_rvalue(self, call_rvalue): 
        #print("visit_call_rvalue")
        # handle built in functions first 
        built_ins = ['print', 'length', 'get', 'readi', 'reads', 'readf', 'itof', 'itos', 'ftos', 'stoi', 'stof'] 
        if call_rvalue.fun.lexeme in built_ins: 
            self.__built_in_fun_helper(call_rvalue) 
        else: 
            fun_info = self.sym_table.get_info(call_rvalue.fun.lexeme)
            curr_env = self.sym_table.get_env_id()
            fun_stmt = fun_info[1]
            #gets the value of the parameters
            params = []
            for x in call_rvalue.args:     
                x.accept(self)
                params.append(self.current_value)
            self.sym_table.set_env_id(fun_info[0])
            self.sym_table.push_environment()
            for i, x in enumerate(fun_stmt.params):
                self.sym_table.add_id(x.param_name.lexeme)
                self.sym_table.set_info(x.param_name.lexeme, params[i])
            #goes into the body of the function
            self.run(fun_stmt.stmt_list)        
            self.sym_table.pop_environment()
            self.sym_table.set_env_id(curr_env)
            
                
    def __built_in_fun_helper(self, call_rvalue): 
        #print("test 1.0")
        fun_name = call_rvalue.fun.lexeme 
        arg_vals = [] 
        for x in call_rvalue.args:
            x.accept(self)
            arg_vals.append(self.current_value)
        # check for nil values 
        for i, arg in enumerate(arg_vals): 
            if arg is None: 
                i = 0#... report a nil value error ...
        # perform each function 
        if fun_name == 'print': 
            arg_vals[0] = arg_vals[0].replace(r'\n','\n') 
            print(arg_vals[0], end='') 
        elif fun_name == 'length': 
            self.current_value = len(arg_vals[0]) 
        elif fun_name == 'get': 
            if 0 <= arg_vals[0] < len(arg_vals[1]): 
                self.current_value = arg_vals[1][arg_vals[0]] 
            else: 
                self.__error("get out of bounds", self.current_token) 
        elif fun_name == 'reads': 
            self.current_value = input() 
        elif fun_name == 'readi': 
            try: 
                self.current_value = int(input()) 
            except ValueError: 
                self.__error('bad int value', call_rvalue.fun) 
        elif fun_name == 'ftos':
            self.current_value = str(arg_vals[0])
        elif fun_name == 'stof':
            self.current_value = float(arg_vals[0])
        elif fun_name == 'itof':
            temp = arg_vals[0]
            self.check_for_nil(temp)
            self.current_value = float(arg_vals[0])
        elif fun_name == 'itos':
            temp = arg_vals[0]
            self.check_for_nil(temp)
            self.current_value = str(arg_vals[0])
        elif fun_name == 'stoi':
            self.current_value = int(arg_vals[0])
        elif fun_name == 'reads':
            self.current_value = input()
        elif fun_name == 'readf':
            temp = input()
            self.current_value = float(temp)
        #... etc ...

    def check_for_nil(self, val):
        if val == 'nil' or val == None:
            self.__error("can't do that with a nil", self.current_token)
            
    def visit_while_stmt(self, whileStmt):
        self.expressionIsTrue = True
        whileStmt.bool_expr.accept(self)
        while self.expressionIsTrue:
            self.sym_table.push_environment()
            for x in whileStmt.stmt_list.stmts:
                x.accept(self)
            self.sym_table.pop_environment()
            whileStmt.bool_expr.accept(self)
            
    def visit_bool_expr(self, boolStmt):
        self.expressionIsTrue = False
        boolStmt.first_expr.accept(self)
        lhs = self.current_value
        if boolStmt.bool_rel != None:
            cond = boolStmt.bool_rel.lexeme
            boolStmt.second_expr.accept(self)
            rhs = self.current_value
            #if rhs == None or lhs == None:
            #    print(rhs, " + ", lhs, " ", cond)
            #    self.__error("can't do comparisons with nil values", self.current_token)
            if cond == '<' and lhs < rhs:
                self.expressionIsTrue = True
            elif cond == '<=' and lhs <= rhs:
                self.expressionIsTrue = True
            elif cond == '>' and lhs > rhs:
                self.expressionIsTrue = True
            elif cond == '>=' and lhs >= rhs:
                self.expressionIsTrue = True
            elif cond == '==' and lhs == rhs:
                self.expressionIsTrue = True
            elif cond == '!=' and lhs != rhs:
                self.expressionIsTrue = True
        elif lhs == True:
            self.expressionIsTrue = True
        if boolStmt.negated == True:
            self.expressionIsTrue = not self.expressionIsTrue
        if boolStmt.bool_connector != None:
            temp = self.expressionIsTrue
            boolStmt.rest.accept(self)
            if boolStmt.bool_connector.lexeme == 'and':
                self.expressionIsTrue = temp and self.expressionIsTrue
            elif boolStmt.bool_connector.lexeme == 'or':
                self.expressionIsTrue = temp or self.expressionIsTrue
    
    def visit_assign_stmt(self, assignStmt):
        assignStmt.rhs.accept(self)
        assignStmt.lhs.accept(self)
    
    def visit_if_stmt(self, ifStmt):
        ifStmt.if_part.bool_expr.accept(self)
        if self.expressionIsTrue:
            self.sym_table.push_environment()
            for x in ifStmt.if_part.stmt_list.stmts:
                x.accept(self)
            self.sym_table.pop_environment()
        else:
            stillFalse = True
            for x in ifStmt.elseifs:
                if stillFalse:
                    x.bool_expr.accept(self)
                    if self.expressionIsTrue:
                        stillFalse = False
                        self.sym_table.push_environment()
                        for y in x.stmt_list.stmts:
                            y.accept(self)
                        self.sym_table.pop_environment()
            if stillFalse and ifStmt.has_else:
                self.sym_table.push_environment()
                for x in ifStmt.else_stmts.stmts:
                    x.accept(self)
                self.sym_table.pop_environment()
    
    def visit_struct_decl_stmt(self, structStmt):
        curr_env = self.sym_table.get_env_id()
        self.sym_table.add_id(structStmt.struct_id.lexeme)
        structValue = [curr_env, structStmt.var_decls]
        self.sym_table.set_info(structStmt.struct_id.lexeme, structValue)
        
    def visit_new_rvalue(self, newStmt):
        struct_info = self.sym_table.get_info(newStmt.struct_type.lexeme)
        curr_env = self.sym_table.get_env_id() 
        self.sym_table.set_env_id(struct_info[0])
        struct_obj = {}
        
        self.structDict = {}
        self.inStruct = True
    
        self.sym_table.push_environment()
        for x in struct_info[1]:
            temp = x.var_id.lexeme
            x.var_expr.accept(self)
            struct_obj[temp] = self.current_value
        self.sym_table.pop_environment()
    
        self.inStruct = False
        #struct_obj = dict(self.structDict)
        self.structDict = {}
        
        self.sym_table.set_env_id(curr_env)
        oid = id(struct_obj)
        self.heap[oid] = struct_obj
        self.current_value = oid 
        self.structId += 1

    def visit_fun_decl_stmt(self, funStmt):
        curr_env = self.sym_table.get_env_id()
        self.sym_table.add_id(funStmt.fun_name.lexeme)
        fun_val = [curr_env, funStmt]
        self.sym_table.set_info(funStmt.fun_name.lexeme, fun_val)
      
        
    def visit_return_stmt(self, returnStmt):
        if returnStmt.return_expr != None:
            returnStmt.return_expr.accept(self)
        raise ReturnException()
