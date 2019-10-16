import mypl_token as token
import mypl_error as error
class Lexer(object):
    def __init__(self, input_stream):
        self.line = 1
        self.column = 1
        self.input_stream = input_stream

    def __peek(self):
        pos = self.input_stream.tell()
        symbol = self.input_stream.read(1)
        self.input_stream.seek(pos)
        return symbol

    def __read(self):
        return self.input_stream.read(1)

    def next_token(self):
        input = ""
        oldLine = self.line
        oldColumn = self.column
        temp = ""
        inputType = ""
        intFloatOrString = 0 #1 if input is a number, 2 if float, 3 if string, 0 otherwise
        checker = True
        keepLooping = True
        noSpaceSymbols = ['.', '<=', '>=', '==', '!=', '*',':', '/', '!', '+', '-', ';', '=', ')', '(', '<', '>', ',', '%'] #list of symbols that dont need whitesaces
        comparisonsOp = ['<=', '>=', '==', '!=', '<', '>'] #list of comparisons

        #take care of whitespace
        while self.__peek().isspace(): # == " " or self.__peek() == '\n' or self.__peek == '\t':
            temp = self.__read()
            self.column += 1
            oldColumn = self.column
        while self.__peek() == '\n':
            temp = self.__read()
            self.column += 1
            oldColumn = self.column

        
        while self.__peek() !=  " " and self.__peek() != "" and self.__peek() != '\n' and not self.__peek().isspace() and keepLooping:
            #token is a string
            if self.__peek() == '"' or self.__peek() == "'": 
                isSingle = True;
                if self.__peek() == '"':
                    isSingle = False
                temp = self.__read()
                self.column += 1
                while (self.__peek() != "'" and self.__peek() != '"') or ((self.__peek() != "'" or not isSingle) and (self.__peek() != '"' or isSingle)):
                    input += self.__read()
                    if self.__peek() == '\n':
                        raise error.MyPLError("uh oh, you had a new line in a string ", self.line, self.column)
                    self.column += 1
                temp = self.__read()
                self.column += 1
                intFloatOrString = 3
                keepLooping = False
            #token is not a string               
            #print(self.column)
            #reads the next character   
            if keepLooping:
                input += self.__read()
                #what to do for comments
                if input == '#':
                    while self.__peek() != '\n':
                        input = self.__read()
                    input = ""
                    temp == self.__read()
                    while self.__peek() == " " or self.__peek().isspace():
                        temp = self.__read()
                    while self.__peek() == '\n':
                        temp = self.__read()
                    self.line += 1
                    self.column = 1
                    oldLine = self.line
                    oldColumn = self.column
                #bad number checking for number preceded by 0
                if input == '0' and self.__peek().isdigit():
                    m = 'unexpected symbol "%s" at: ' %self.__peek()
                    raise error.MyPLError(m, self.line, self.column)
                #bad number checking for digit followed by alphabetical letter
                if input.isdigit() and self.__peek().isalpha():   
                    temp = self.__read()
                    m = 'unexpected symbol "%s" at:' % temp
                    raise error.MyPLError(m, self.line, self.column)
                     
                checker = True
                if self.__peek() == '.' and input.isdigit():
                    checker = False
                #checking for operators 
                if checker == True:
                    if (input in noSpaceSymbols or self.__peek() in noSpaceSymbols) and input != "":
                        if input == '!' and self.__peek() != '=':
                            raise error.MyPLError("extra exclamation mark at ", self.line, self.column)
                        temp = input + self.__peek()
                        if len(input) == 1:
                            if temp != '!=' and temp != '==':
                                if input in comparisonsOp:
                                    if self.__peek() in comparisonsOp == False:
                                        keepLooping = False
                                else:
                                    keepLooping = False
                        else:
                            keepLooping = False
                 
                    
                #increment column count
                self.column += 1
        if intFloatOrString != 3:
            #checks to see if the input is an int
            if(input.isdigit()):   
                intFloatOrString = 1
            #checks to see if it is a double
            else:
                soFarSoGood = True   #bool that checks to see if there are any alphabetical characters
                numberOfDots = 0   #keeps track of the dots
                if len(input) > 1:
                    for i, x in enumerate(input):
                        if x == '.':
                            numberOfDots += 1
                            #float error where there is nothing after the 
                            if i + 1 == len(input):     
                                m = input + "missing digit in float value at "
                                raise error.MyPLError(m, self.line, self.column)
                            #float error where there is an invalid number after the dot
                                #pre dot invalid number checking is taken care of up above
                            elif input[i+1].isdigit() == False and soFarSoGood:   
                                m = 'unexpected character "%s" at ' % (self.__peek())
                                raise error.MyPLError(m, self.line, self.column)
                        elif x.isdigit() == False:
                            soFarSoGood = False
                if soFarSoGood and numberOfDots == 1:
                    intFloatOrString = 2
        #end of the line
        if self.__peek() == '\n':
            self.line += 1
            self.column = 1;
            temp = self.__read()
        #input was a int float or string
        if intFloatOrString != 0:
            if intFloatOrString == 1:
                inputType = token.INTVAL
            elif intFloatOrString == 2:
                inputType = token.FLOATVAL
            else:
                inputType = token.STRINGVAL
        #input was not a value except for maybe a bool
        else:
            if input == '=':
                inputType = token.ASSIGN
            elif input == ',':
                inputType = token.COMMA
            elif input == ':':
                inputType = token.COLON
            elif input == '/':
                inputType = token.DIVIDE
            elif input == '.':
                inputType = token.DOT
            elif input == '==':
                inputType = token.EQUAL
            elif input == '':
                oldColumn -= 1
                inputType = token.EOS
            elif input == '>':
                inputType = token.GREATER_THAN
            elif input == '>=':
                inputType = token.GREATER_THAN_EQUAL
            elif input == '<':
                inputType = token.LESS_THAN
            elif input == '<=':
                inputType = token.LESS_THAN_EQUAL
            elif input == '!=':
                inputType = token.NOT_EQUAL
            elif input == '(':
                inputType = token.LPAREN
            elif input == ')':
                inputType = token.RPAREN
            elif input == '-':
                inputType = token.MINUS
            elif input == '%':
                inputType = token.MODULO
            elif input == '*':
                inputType = token.MULTIPLY
            elif input == '+':
                inputType = token.PLUS
            elif input == ';':
                inputType = token.SEMICOLON
            elif input == 'bool':
                inputType = token.BOOLTYPE
            elif input == 'int':
                inputType = token.INTTYPE
            elif input == 'float':
                inputType = token.FLOATTYPE
            elif input == 'string':
                inputType = token.STRINGTYPE
            elif input == 'struct':
                inputType = token.STRUCTTYPE
            elif input == 'and':
                inputType = token.AND
            elif input == 'or':
                inputType = token.OR
            elif input == 'not':
                inputType = token.NOT
            elif input == 'while':
                inputType = token.WHILE
            elif input == 'do':
                inputType = token.DO
            elif input == 'if':
                inputType = token.IF
            elif input == 'then':
                inputType = token.THEN
            elif input == 'else':
                inputType = token.ELSE
            elif input == 'elif':
                inputType = token.ELIF
            elif input == 'end':
                inputType = token.END
            elif input == 'fun':
                inputType = token.FUN
            elif input == 'var':
                inputType = token.VAR
            elif input == 'set':
                inputType = token.SET
            elif input == 'return':
                inputType = token.RETURN
            elif input == 'new':
                inputType = token.NEW
            elif input == 'false' or input == 'true':
                inputType = token.BOOLVAL
            elif input == 'nil':
                inputType = token.NIL
            else:
                inputType = token.ID
        newToken = token.Token(inputType, input, oldLine, oldColumn)
        return newToken
