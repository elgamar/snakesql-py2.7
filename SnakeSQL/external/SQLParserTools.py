"SQLParserTools provides classes for parsing and building SQL strings"

# Check Bools are defined
try:
    True
except NameError:
    True = 1
    False = 0

# Imports
from error import *
from external.StringParsers import *
import string

# Definitions
allowedCharacters = string.letters+'_-0123456789'
sqlReservedWords = [
    'AND',
    'AS',
    'ASC',
    'BY',
    'CREATE',
    'DELETE',
    'DESC',
    'DROP',
    'FROM',
    'INSERT',
    'INTO',
    'KEY',
    'LIKE',
    'NOT',
    'NULL',
    'ORDER',
    'OR',
    'PRIMARY',
    'REQUIRED',
    'SHOW',
    'SELECT',
    'SET',
    'TABLE',
    'TABLES',
    'UNIQUE',
    'UPDATE',
    'VALUES',
    'WHERE',
]
types = [
    'UNKNOWN',
    'BINARY',
    'BOOL',
    'DATE',
    'DATETIME',
    'FLOAT',
    'INTEGER',
    'LONG',
    'TEXT',
    'TIME',
    'STRING',
]
soonToBe = [
    'SUM',
    'MAX',
    'FOREIGN',
    'MIN',
    'MOD',
    'DISTINCT',
    'COUNT',
    'COLUMN',
    'DATABASE',
]

# Ensure list items are all uppercase if set extrenally
def setTypes(list):
    for i in range(len(list)):
        list[i] = str(list[i]).upper()
    types = list

# SQLParser
class Parser:
    """Class for parsing SQL Code into more useful forms.

    Notes
     - Error checking is done at this stage. For example, checking that no duplicate column names are specified in an INSERT or CREATE.
     - Values returned from this parser are fully quoted SQL eg NULL, 'NULL', ?, '?', 56, '56', 'James', 'James''s'
    
    Restrictions
     - No newline characters should be used in the SQL except in quoted values.
    """
    def parse(self, sql):
        "Parse an SQL statement"
        stripped = stripBoth(sql.split(' '))
        function = str(stripped[0]).lower()
        if function == 'select':
            result = self.parseSelect(sql)
        elif function == 'delete':
            result = self.parseDelete(sql)
        elif function == 'insert':
            result = self.parseInsert(sql)
        elif function == 'update':
            result = self.parseUpdate(sql) 
        elif function == 'create':
            result = self.parseCreate(sql)
        elif function == 'drop':
            result = self.parseDrop(sql)
        elif function == 'show':
            if str(stripped[1]).lower() == 'tables':
                result = {'item':'tables',}
            else:
                raise SQLSyntaxError("Expected 'TABLES' after SHOW.")
        else:
            raise SQLError("%s is not a supported keyword."%function.upper())
        result['function'] = function
        return result

    def parseDrop(self, sql):
        "Parse a DROP statement"
        keyword = 'DROP'
        tableIdentifier = 'TABLE'
        table = ''
        sql = str(stripBoth(sql))
        if sql[:len(keyword)+1].lower() <> str(keyword).lower()+' ':
            raise SQLSyntaxError('%s term not found at start of the %s statement.'%(keyword.upper(), keyword.upper()))
        else:
            sql = stripStart(sql[len(keyword)+1:])
        if sql[:len(tableIdentifier)+1].lower() <> str(tableIdentifier).lower()+' ':
            raise SQLSyntaxError('%s term not found after %s keyword.'%(tableIdentifier.upper(), keyword.upper()))
        else:
            sql = stripStart(sql[len(tableIdentifier)+1:])
            
            pos = 0
            for char in sql:
                if char in allowedCharacters+', ': 
                    table += char
                else:
                    raise SQLSyntaxError("Table name contains the invalid character '%s' after '%s'."%(char, table))
                pos += 1
        t = []
        tables = table.split(',')
        for table in tables:
            t.append(table.strip(' '))
        return {
            'tables':t,
        }
        
    def parseCreate(self, sql, types=types):
        "Parse a CREATE statement"
        sql, table = self._parseTable(sql, 'CREATE', 'TABLE')
        if sql[0] <> "(":
            raise SQLSyntaxError("Expected a '(' after the table name.")
        if sql[-1:] <>  ")":
            raise SQLSyntaxError("Expected a ')' at the end of the CREATE statement.")
        sql = sql[1:]
        if (len(sql.split("'"))-1)%2:
            raise SQLSyntaxError('Uneven number of "\'" characters perhaps due to incorrect quoting in one of the default values of the columns')
        pos = 0
        columns = []
        column = {'name':None,'type':None,'unique':False,'required':False,'primaryKey':False,'foreignKey':None,'default': None,}
        term = ''
        part = 'name'
        position = 'one'
        while 1:
            if part in ['name', 'type']:
                if position=='one' and sql[pos] == ' ':
                    pos+=1
                elif position=='one' and sql[pos] in allowedCharacters: # start the name
                    position = 'middle'
                    term += sql[pos]
                    pos+=1
                elif position=='middle' and sql[pos] in allowedCharacters: # middle of name
                    position = 'middle'
                    term += sql[pos]
                    pos+=1
                elif position=='middle' and sql[pos] == ' ': # end of the name
                    column[part] = term
                    if part == 'name':
                        for c in columns:
                            if c['name'] == term:
                                raise SQLError('Duplicate name %s for columns in CREATE statement'%(repr(term)))
                        if term.upper() in sqlReservedWords:
                            raise SQLError('%s is an SQL reserved word and cannot be used as a column name'%(repr(term)))
                        if term.upper() in types:
                            raise SQLError('%s is an SQL data type and cannot be used as a column name'%(repr(term)))
                        part='type'
                    elif part == 'type':
                        #if term.upper() in sqlReservedWords:
                        #    raise SQLError('%s is an SQL reserved word and cannot be used as a column name'%(repr(term)))
                        if term.upper() not in types:
                            raise SQLError('%s is not a recognised SQL data type'%(repr(term)))
                        part='options'
                    else:
                        raise Bug('Unknown part of column definition in CREATE statement')
                    position='one'
                    term = ''
                    pos+=1
                elif position=='middle' and sql[pos] in [',',')']:
                    if part == 'name':
                        raise SQLSyntaxError("No column type specified for column %s."%(len(columns)+1))
                    else:
                        column[part] = term
                        columns.append(column)
                        column = {
                            'name':None,'type':None,'unique':False,'required':False,'primaryKey':False,
                            'foreignKey':None, 'default': None,
                        }
                        pos+=1
                        part='name'
                        position='one'
                        term = ''
                elif part == 'name':
                    raise SQLSyntaxError("Extra ',' or ')' found in create statement.")
                else:
                    raise SQLSyntaxError("Column type not specified for %s."%(column['name']))
            elif part == 'options':
                if sql[pos:pos+6].lower() == 'unique':
                    pos += 6
                    column['unique'] = True
                elif sql[pos:pos+8].lower() == 'required':
                    pos += 8
                    column['required'] = True
                elif sql[pos:pos+11].lower() == 'primary key':
                    pos += 11
                    column['primaryKey'] = True
                elif sql[pos] == ' ': #Whitespace
                    pos += 1
                elif sql[pos] in [',',')']:
                    columns.append(column)
                    column = {
                        'name':None,'type':None,'unique':False,'required':False,'primaryKey':False,
                        'foreignKey':None, 'default': None,
                    }
                    pos+=1
                    part='name'
                    position='one'
                    term = ''
                else: # We must be looking at the default value or foreign Key
                    
                    if sql[pos:pos+7].lower() == 'default':
                        pos+=7
                        while sql[pos] == ' ':
                            pos+=1
                        if sql[pos] == '=':
                            part='default'
                            pos += 1
                            position = 'one'                            
                        else:
                            raise SQLSyntaxError("Expected '=' after DEFAULT in column %s in CREATE statement."%(len(columns)+1))
                    elif sql[pos:pos+11].lower() == 'foreign key':
                        pos+=11
                        while sql[pos] == ' ':
                            pos+=1
                        if sql[pos] == '=':
                            part='foreignKey'
                            pos += 1
                            position = 'one'                            
                        else:
                            raise SQLSyntaxError("Expected '=' after FOREIGN KEY in column %s in CREATE statement."%(len(columns)+1))
                    else:
                        raise SQLSyntaxError("Expected DEFAULT or FOREIGN KEY or the end of the statement not %s for column %s in CREATE statement."%(repr(sql[pos:pos+11]), len(columns)+1))
            elif part=='default':  # one
                if column['primaryKey']:  #     default 'henry' , ) 
                    raise SQLError("PRIMARY KEY column '%s' cannot also have a DEFAULT value."%column['name'])
                if column['foreignKey']:
                    raise SQLError("FOREIGN KEY column '%s' cannot also have a DEFAULT value."%column['name'])
                if position == 'one':
                    if sql[pos] == ' ': #Whitespace
                        pos+=1
                    elif sql[pos] == "'":
                        position='defaultString'
                        column['default'] = "'"
                        pos+=1
                    else:
                        position='defaultNonString'
                        if column['default'] == None:
                            column['default'] = sql[pos]
                        else:
                            column['default'] += sql[pos]
                        pos+=1
                elif position=='defaultNonString':
                    if sql[pos] == ' ':
                        position='defaultNonStringEnded'
                        pos+=1
                    elif sql[pos] in [',',"'"]:
                        if sql[pos] == ",":
                            position='defaultNonStringEnded'
                        else:
                            raise SQLSyntaxError("'%s' character found in the unquoted default value of column %s"%(sql[pos], len(columns)+1))
                    elif sql[pos] == ')':
                        position='defaultNonStringEnded'
                    else:
                        column['default']+=sql[pos]
                        pos+=1
                elif position=='defaultNonStringEnded':
                    if sql[pos] == ' ':
                        pos+=1
                    elif sql[pos] in [',',')']:
                        if column['default'] == 'NULL':
                            if column['required']:
                                raise SQLError("REQUIRED column '%s' cannot also have a DEFAULT value of NULL"%column['name'])
                            column['default'] = 'NULL'
                        columns.append(column)
                        column = {
                            'name':None,'type':None,'unique':False,'required':False,'primaryKey':False,
                            'foreignKey':None, 'default': None,
                        }
                        pos+=1
                        part='name'
                        position='one'
                        term = ''
                    else:
                        raise SQLSyntaxError("Non-whitespace character '%s' found after default value of column %s"%(sql[pos], len(columns)+1))
                elif position=='defaultString':
                    #~ if len(sql)+1 > pos and sql[pos:pos+3] == "''":
                        #~ column['default']+="''"
                        #~ pos+=2
                    if sql[pos:pos+2] == "''":
                        if column['default'] == None:
                            column['default']="''"
                            pos += 2
                            columns.append(column)
                            column = {
                                'name':None,'type':None,'unique':False,'required':False,'primaryKey':False,
                                'foreignKey':None, 'default': None,
                            }
                            part='name'
                            position='one'
                            term = ''
                        else:
                            column['default']+="''"
                            pos += 2
                    elif sql[pos] == "'":
                        position='defaultEnded'
                        column['default'] += "'"
                        pos+=1
                    else:
                        if column['default'] == None:
                            column['default']=sql[pos]
                        else:
                            column['default']+=sql[pos]
                        pos+=1
                elif position=='defaultEnded':
                    if sql[pos] == ' ':
                        pos+=1
                    elif sql[pos] in [',',')']:
                        columns.append(column)
                        column = {
                            'name':None,'type':None,'unique':False,'required':False,'primaryKey':False,
                            'foreignKey':None,'default': None,
                        }
                        pos+=1
                        part='name'
                        position='one'
                        term = ''
                    else:
                        raise SQLSyntaxError("Non-whitespace character '%s' found after default value of column %s"%(sql[pos], len(columns)+1))
                else:
                    raise Bug('Programming Error')

            elif part=='foreignKey':  # one
                if column['primaryKey']:  #     default 'henry' , ) 
                    raise SQLError("PRIMARY KEY column '%s' cannot also have a FOREIGN KEY value."%column['name'])
                if column['default']:
                    raise SQLError("FOREIGN KEY column '%s' cannot also have a DEFAULT value."%column['name'])
                if position == 'one':
                    if sql[pos] == ' ': #Whitespace
                        pos+=1
                    else:
                        position='foreignKeyNonString'
                        if column['foreignKey'] == None:
                            column['foreignKey'] = sql[pos]
                        else:
                            column['foreignKey'] += sql[pos]
                        pos+=1
                elif position=='foreignKeyNonString':
                    if sql[pos] == ' ':
                        position='foreignKeyNonStringEnded'
                        pos+=1
                    elif sql[pos] in [',',"'"]:
                        if sql[pos] == ",":
                            position='foreignKeyNonStringEnded'
                        else:
                            raise SQLSyntaxError("'%s' character found in the FOREIGN KEY value of column %s"%(sql[pos], len(columns)+1))
                    elif sql[pos] == ')':
                        position='foreignKeyNonStringEnded'
                    else:
                        column['foreignKey']+=sql[pos]
                        pos+=1
                elif position=='foreignKeyNonStringEnded':
                    if sql[pos] == ' ':
                        pos+=1
                    elif sql[pos] in [',',')']:
                        for char in column['foreignKey']:
                            if char not in allowedCharacters:
                                raise SQLSyntaxError('Invalid character %s in FOREIGN KEY value %s for column %s'%(repr(char), repr(column['foreignKey']), repr(column['name'])))
                        columns.append(column)
                        column = {
                            'name':None,'type':None,'unique':False,'required':False,'primaryKey':False,
                            'foreignKey':None,'default': None,
                        }
                        pos+=1
                        part='name'
                        position='one'
                        term = ''
                    else:
                        raise SQLSyntaxError("Non-whitespace character '%s' found after FOREIGN KEY definition of column %s"%(sql[pos], len(columns)+1))
                else:
                    raise Bug('Programming Error')
                    
                    
            if len(sql) <= pos:
                break
        primaryKey = False
        for column in columns:
            if column['primaryKey']:
                if primaryKey:
                    raise SQLError("More than one column specified as PRIMARY KEY.")
                primaryKey = True
        return {
            'table':table,
            'columns':columns,
        }

    def _parseTable(self, sql, keyword, tableIdentifier):
        """Check the syntax of the starts of the INSERT and CREATE statements
        
        Returns a tuple (remaining sql, table name)."""
        sql = stripBoth(sql)
        if sql[:len(keyword)+1].lower() <> keyword.lower()+' ':
            raise SQLSyntaxError('%s term not found at start of the %s statement.'%(keyword.upper(), keyword.upper()))
        else:
            sql = stripStart(sql[len(keyword)+1:])
        if sql[:len(tableIdentifier)+1].lower() <> tableIdentifier.lower()+' ':
            raise SQLSyntaxError('%s term not found after %s keyword.'%(tableIdentifier.upper(), keyword.upper()))
        else:
            sql = stripStart(sql[len(tableIdentifier)+1:])
            table = ''
            pos = 0
            for char in sql:
                if char in [',','(',' ']:
                    break
                elif char in allowedCharacters: 
                    table += char
                else:
                    raise SQLSyntaxError("Table name contains the invalid character '%s' after '%s'."%(char, table))
                pos += 1
            sql = stripBoth(sql[pos:])
        return sql, table

    def parseInsert(self, sql):
        "Parse an INSERT clause"
        sql, table = self._parseTable(sql, 'INSERT', 'INTO')
        if sql[0] <> "(":
            raise SQLSyntaxError("Expected a '(' after the table name.")
        else:
            sql=stripStart(sql[1:])
            columns = ''
            for char in sql:
                if not char == ')':
                    if char in allowedCharacters+', ':
                        columns+= char
                    else: 
                        raise SQLSyntaxError("Invalid character '%s' found after '%s' in INSERT statement."%(char, columns))
                else:
                    break
            if len(columns) == len(sql):
                raise SQLSyntaxError("')' not found after column names in INSERT statement.")
            sql = stripStart(sql[len(columns):])
            if not sql[0] == ')':
                raise SQLSyntaxError("Expected ')' after column names in INSERT statement.")
            sql=stripStart(sql[1:])
            columns = stripBoth(columns.split(','))
            for column in columns:
                if columns.count(column) > 1:
                    raise SQLError("The column named '%s' has been specified more than once in the INSERT statement."%(column))
            if sql[:6].lower() <> 'values':
                raise SQLSyntaxError("Expected 'VALUES' after column names in INSERT statement.")
            sql = stripStart(sql[6:])
            if sql[0] <> '(':
                raise SQLSyntaxError("Expected '(' after VALUES in INSERT statement.")
            if sql[-1:] <> ')':
                raise SQLSyntaxError("Expected ')' after column values in INSERT statement.")
            sql = sql[1:-1]
            i=0
            values = []
            curValue = ''
            quoted = False        #01     2  3 
            position = 0          # value1 ,  
            while 1:
                if position==0:
                    if sql[i] == ' ':
                        pass
                    elif sql[i:i+2] == "''" and not sql[i:i+3] == "'''":
                        raise SQLSyntaxError("The value %s characters after VALUES is not properly quoted (it should not start '')"%i)
                    elif sql[i] == "'": # Start of new quoted term
                        curValue += sql[i]
                        quoted = True
                        position = 1
                    else:
                        curValue += sql[i]
                        position = 1
                elif position == 1:
                    if quoted:
                        if sql[i:i+2] == "''":
                            curValue += "''"
                            i+=1
                        elif sql[i] == "'": # End of term
                            curValue += sql[i]
                            values.append(curValue)
                            quoted = False
                            curValue = ''
                            position=2
                        else:
                            curValue += sql[i]
                    else:
                        if sql[i] == "'":
                            raise SQLSyntaxError("Missing %s at start of value %s"%(sql[i],repr(curValue)))
                        elif sql[i] == ' ': # End of term
                            values.append(curValue)
                            quoted = False
                            curValue = ''
                            position=2
                        elif sql[i] == ',':# End of term
                            values.append(curValue)
                            quoted = False
                            curValue = ''
                            position=0
                        else:
                            curValue += sql[i]
                elif position == 2:
                    if sql[i] == " ":
                        pass
                    elif sql[i] == ",":
                        position = 0
                    else:
                        raise SQLSyntaxError("Expected ',' after %s in VALUES part of INSERT statement."%(repr(values[0])))
                if i >= len(sql)-1:
                    if quoted and curValue:
                        raise SQLSyntaxError("Last term in VALUES part of INSERT statement does not end in \"'\" character")
                    else:
                        if curValue:
                            values.append(curValue)
                        break
                else:
                    i+=1
            if len(columns) <> len(values):
                raise SQLError("The number of columns doesn't match the number of values.")
            return {
                'table':table,
                'columns':columns,
                'sqlValues':values,
            }
            
    def parseSelect(self, sql):
        """Parse a SELECT statement.
        
        The dictionary returned from this function only contains the 'where' and 'order' keys if WHERE and ORDER BY clauses respectively exist.
        """
        sql = stripBoth(sql)
        order = []
        where = []
        keyword = 'SELECT'
        if sql[:len(keyword)+1].lower() <> keyword.lower()+' ':
            raise SQLSyntaxError('%s term not found at start of the %s statement.'%(keyword.upper(), keyword.upper()))
        else:
            sql = stripStart(sql[len(keyword)+1:])
        pos = sql.lower().find('from')
        if pos == -1:
            raise SQLSyntaxError('FROM term not found after column list in SELECT statement')
        else:
            columns = stripBoth(sql[:pos].split(','))
            if columns[-1] == '':
                raise SQLSyntaxError("Unexpected ',' found after column names and before FROM keyword.")
            if columns <> ['*']:
                for column in columns:
                    for char in column:
                        if char not in allowedCharacters+'.':
                            if column == '*':
                                raise SQLSyntaxError("The special identifier '*' should be used on its own to select all columns.") 
                            raise SQLSyntaxError("Column name '%s' contains the invalid character '%s'."%(column, char))
                    if columns.count(column)>1:
                        raise SQLError("Column '%s' is selected more than once in the SELECT statement."%(column))
            tableIdentifier = 'FROM'
            sql = stripStart(sql[pos+len(tableIdentifier)+1:])
            table = ''
            pos = 0
            for char in sql:
                if sql[pos:pos+6].lower() == ' where':
                    break
                elif char in ['(']:
                    break
                elif char in allowedCharacters+'., ':
                    table += char
                else:
                    raise SQLSyntaxError("Table name contains the invalid character '%s' after '%s'."%(char, table))
                pos += 1
            t = table.split(',')
            table = []
            for tab in t:
                if not tab.strip():
                    raise SQLSyntaxError("Extra ',' found after %s"%repr(table[-1]))
                elif tab.strip().lower() in ['where', 'order']:
                    raise SQLSyntaxError("Extra ',' found after %s"%repr(table[-1]))
                table.append(tab.strip())
            sql = stripBoth(sql[pos:])
            
            if sql[:6].lower() == 'where ':
                orderbyParts = sql.lower().split('order by')
                if len(orderbyParts) == 1:
                    where = stripBoth(sql[6:])
                    order = None
                elif len(orderbyParts) == 2:
                    if sql[6:len(orderbyParts[0])].count("'")%2: # ie uneven number of ' in where, ie we've got the wrong order by
                        # No order
                        where = sql[6:]
                        order = None
                    else:
                        where = stripBoth(sql[6:len(orderbyParts[0])])
                        order = sql[len(orderbyParts[0])+8:]
                    
                        if order[0] <> ' ':
                            raise SQLSyntaxError('Expected whitespace after ORDER BY keyword')
                else:
                    order = orderbyParts[-1]
                    if order[0] <> ' ':
                        raise SQLSyntaxError('Expected whitespace after ORDER BY keyword')
                    where = stripBoth(sql[6:len('order by'.join(orderbyParts[:-1]))])
            elif sql[:8].lower() == 'order by':
                if sql[8:].lower().find('where') <> -1:
                    raise SQLSyntaxError('WHERE should come before ORDER BY in SELECT statement.')
                order = sql[8:]
                if order[0] <> ' ':
                    raise SQLSyntaxError('Expected whitespace after ORDER BY keyword')
                        
            else:
                pass # No ORDER BY or WHERE clauses
            if order and stripBoth(order):
                order = self._parseOrder(stripBoth(order))
            if where:
                where = self._parseWhere(where, tables=table)
        result = {
            'tables':table,
            'columns': columns,
        }
        if order:
            result['order']=order
        if where:
            result['where']=where
        return result
        
    def _parseOrder(self, order):
        "Parse an ORDER BY clause begining with 'ORDER BY '"
        order = stripBoth(order)
        #if order[:8].lower() != 'order by':
         #   raise Bug('The ORDER BY keyword is not present')
        #if order[8] != ' ':
        #    raise SQLSyntaxError("No whitespace found after ORDER BY keyword")
        #order = order[8:]
        parts = order.split(',')
        orderPairs = []
        cols = []
        for part in parts:
            while part[0] == ' ':
                part = part[1:]
            while part[-1:] == ' ':
                part = part[1:]
            if not part:
                raise SQLSyntaxError('Too many commas in order clause.')
            pair = part.split(' ')
            if len(pair) == 1:
                if pair[0] in cols:
                    raise SQLError("You have specified %s more than once in the ORDER BY clause."%(repr(pair[0])))
                else:
                    cols.append(pair[0])
                    orderPairs.append([pair[0],'asc'])
            elif len(pair) == 2:
                if pair[0] in cols:
                    raise SQLError("You have specified %s more than once in the ORDER BY clause."%(repr(pair[0])))
                elif pair[1].lower() not in ['asc','desc']:
                    raise SQLSyntaxError("Expected 'ASC' or 'DESC' after %s not %s."%(repr(pair[0]),repr(pair[1])))
                else:
                    cols.append(pair[0])
                    orderPairs.append([pair[0],pair[1].lower()])
            else:
                raise SQLSyntaxError("Order clause not properly formed near '%s'."%(repr(part)))
        return orderPairs

    def _parseWhere(self, where, compOperators=['>','<','=','>=','<=','<>','!=','like'], logicalOperators=['and', 'or'], tables=[]):
        """Parse WHERE clause string into a list of parts
        
        Returns a list of 'not', '(', ')', logicalOperator or [columnName, comparisonOperator, value] objects.
        e.g. This:    ((one = '''''' and not (  two='22' ))) 
             Returns: ['(', '(', ['one', '=', "''''''"], 'and', 'not', '(', ['two', '=', "'22'"], ')', ')', ')']
        """
        #if where[:5].upper() != 'WHERE':
        #    raise SQLSyntaxError("Expected 'WHERE' at begining of WHERE clause")
        #if where[5] <> ' ':
        #    raise SQLSyntaxError("Expected whitespace after WHERE keyword")
        #where = where[5:]
        def longest(a,b):
            if len(a) > len(b):
                return -1
            else:
                return 0
        compOperators.sort(longest)
        where = self._parseWhereString(where, compOperators, logicalOperators, tables)
        n=[]
        i = 0
        closed = []
        while 1:
            if where[i] in ['not','(']:
                n.append(where[i])
                i+=1
            elif where[i] in [')']:
                closed.append(')')
                i+=1
            else:
                n.append(where[i])
                for item in closed:
                    n.append(item)
                closed = []
                i+=1
            if i > len(where)-1:
                break
        return n

    def _parseWhereString(self, where, compOperators, logicalOperators, tables):
        """Do initial parsing of a WHERE clause string
        
        Returns a list of 'not', '(', ')', logicalOperator or [columnName, comparisonOperator, value] objects where the ')' occur before their repective [columnName, comparisonOperator, value] object.
        """
        if not where:               # -2  -1    0  1    2 3 4 5 6 7    8 9   10
            return []               #  | (| not (| |test| |=| |'|3|' ) | |and| |  
        elif where.count('(') > where.count(')'):
            raise SQLSyntaxError("Expected ')' in WHERE clause")
        elif where.count('(') < where.count(')'):
            raise SQLSyntaxError("Extra ')' character found in WHERE clause")
        pos = 0
        position = -2
        blocks = []
        terms = []
        term = ''
        quote = False
        while 1:
            if position == -2:
                if where[pos] == '(':
                    blocks.append('(')
                    pos+=1
                elif where[pos] == ' ':
                    pos+=1
                elif where[pos:pos+3] == 'not' and where[pos+3] == ' ':
                    blocks.append('not')
                    pos+=3
                elif where[pos] in allowedCharacters:
                    position = 1
                    term+=where[pos]
                    pos+=1
                else:
                    if len(blocks) == 0:
                        raise SQLSyntaxError("Invalid character '%s' found after WHERE keyword."%(where[pos]))
                    else:
                        raise SQLSyntaxError("Invalid character '%s' found after '%s' in WHERE clause."%(where[pos], blocks[0][0]))
            elif position == 1:
                if where[pos] in allowedCharacters:
                    term+=where[pos]
                    pos+=1
                elif where[pos] == '.':
                    if term not in tables:
                        raise SQLError('Table %s used in WHERE clause is not one of the tables being operated on'%repr(term))
                    term+=where[pos]
                    pos+=1
                elif where[pos] == ' ': # End of first column
                    position = 2
                    terms.append(term)
                    term = ''
                    pos+=1
                else:
                    terms.append(term)
                    term = ''
                    position=2
            elif position == 2:
                if where[pos] == ' ': 
                    pos+=1
                else:
                    found = False
                    if where[pos:pos+2].lower() == '==':
                        raise SQLError("Found invalid operator '==' in WHERE clause")
                    for operator in compOperators:
                        if where[pos:pos+len(operator)].lower() in compOperators: # The next section is a two character operator
                            terms.append(where[pos:pos+len(operator)].lower())
                            term = ''
                            pos+=len(operator)
                            position = 4 
                            found = True
                        
                    if not found:
                        raise SQLSyntaxError("Invalid character '%s' found after '%s' in WHERE clause."%(where[pos], terms[0]))
            elif position == 4:               
                if where[pos] == ' ': 
                    pos+=1
                elif where[pos] == "'":
                    term += "'"
                    quote=True
                    pos+=1
                    position = 6
                elif where[pos] in allowedCharacters+'?':
                    position = 6
                    term += where[pos]
                    pos+=1
                else:
                    raise SQLSyntaxError("Invalid character '%s' found after '%s' in WHERE clause."%(where[pos], terms[1]))
            elif position == 6:
                if not quote:
                    if where[pos] in ["'",',','\n']:
                        raise SQLSyntaxError("Invalid character '%s' found after operator in WHERE clause. Try removing the space after the operator or quoting the value."%(where[pos]))
                    elif where[pos] == ' ':
                        if term.upper() == 'NULL':
                            terms.append('NULL')
                        else:
                            terms.append(term)
                        term = ''
                        position = 8
                        pos+=1
                    elif where[pos] == ')':
                        if term.upper() == 'NULL':
                            terms.append('NULL')
                        else:
                            terms.append(term)
                        term = ''
                        blocks.append(')')
                        position = 8
                        pos+=1
                    else:
                        term+=where[pos]
                        pos+=1
                        if len(where) <= pos:
                            if term.upper() == 'NULL':
                                terms.append('NULL')
                            else:
                                terms.append(term)
                            blocks.append(terms)
                            return blocks
                else:
                    if where[pos] == "'" and where[pos:pos+2] == "''":
                        term += "''"
                        pos += 2
                    elif where[pos] == "'" and where[pos:pos+2] == "' ":
                        term += "'"
                        pos += 2
                        terms.append(term)
                        term = ''
                        position = 8
                    elif where[pos] == "'" and where[pos:pos+2] == "')":
                        term += "'"
                        pos += 2
                        terms.append(term)
                        blocks.append(')')
                        term = ''
                        position = 8
                    elif where[pos] == "'" and len(where) == pos+1:
                        term += "'"
                        terms.append(term)
                        blocks.append(terms)
                        return blocks
                    elif where[pos] == "'":
                        raise SQLSyntaxError("Invalid character '%s' found after '%s' in WHERE clause."%(where[pos], term))
                    else:
                        term+=where[pos]
                        pos+=1
            elif position == 8:
                if where[pos] == ' ':
                    pos+=1
                elif where[pos] == ')':
                    blocks.append(')')
                    pos+=1
                else:
                    max = 0
                    found = False
                    for operator in logicalOperators:
                        if len(operator)>max:
                            max = len(operator)
                    r = range(1,max)
                    r.reverse()
                    for length in r:
                        if length < len(where[pos:]):
                            if where[pos:pos+length+1].lower() in logicalOperators and where[pos+length+1] == ' ':
                                blocks.append(terms)
                                blocks.append(where[pos:pos+length+1].lower())
                                terms=[]
                                term = ''
                                pos+=length+1
                                position = -2
                                quote=False
                                found = True
                    if not found:
                        raise SQLSyntaxError("Extra character %s found after %s in WHERE clause."%(repr(where[pos+1]), repr(where[pos])))
            else:
                raise Bug('Unknown position in parsing WHERE clause.')
            
            if len(where) < pos+1:
                
                if len(terms) != 3:
                    terms.append(term)
                    if len(terms) != 3:
                        raise Bug('Unexpected term length of %s whilst parsing last term of WHERE clause'%repr(terms))
                
                blocks.append(terms[:3])
                return blocks
                #elif 
                #    return blocks
                #else:
                    #raise SQLSyntaxError("WHERE clause ended too early.")

    def parseUpdate(self, sql):
        "Parse an UPDATE statement"
        sql = stripBoth(sql)
        table = ''
        where = []
        columns = []
        keyword = 'UPDATE'
        if sql[:len(keyword)+1].lower() <> keyword.lower()+' ':
            raise SQLSyntaxError('%s term not found at start of the %s statement.'%(keyword.upper(), keyword.upper()))
        else:
            sql = stripStart(sql[len(keyword)+1:])
        pos = sql.lower().find('set')
        if pos == -1:
            raise SQLSyntaxError('SET term not found after table name in UPDATE statement')
        else:
            table = ''
            for char in stripBoth(sql[:pos]):
                if char in allowedCharacters:
                    table+=char
                else:
                    raise SQLSyntaxError("Invalid character '%s' near '%s' before SET keyword."%(char, table))
            sql = stripStart(sql[pos+len('set')+1:])
            whereParts = sql.lower().split(' where')
            if len(whereParts) == 1:
                columns = stripBoth(sql[:len(whereParts[0])])
            elif len(whereParts) == 2:
                columns = stripBoth(sql[:len(whereParts[0])])
                where = self._parseWhere(stripBoth(sql[len(whereParts[0])+6:]))
            else:
                raise SQLSyntaxError("More than one WHERE clause specified.")
            cols = []
            vals = []
            for col, op, val in self._parseColumns(columns):
                cols.append(col)
                vals.append(val)
        result = {
            'table':table,
            'columns': cols,
            'sqlValues': vals,
        }
        if where:
            result['where'] = where
        return result

    def _parseColumns(self, sql):
        "Split up the columnName='value' pairs in an update clause"
        if sql.count("'")%2:
            raise SQLSyntaxError("Expected ' character in SET part of UPDATE clause")
        compOperators=['=']   #0  1   2 3 4 5 6  7 8 9 10
        update = sql          #|  |one| |=| |'67'| |,| |
        pos = 0
        position = 0
        blocks = []
        terms = []
        term = ''
        quote = False
        while 1:
            if position == 0:
                if update[pos] == ' ':
                    pos+=1
                elif update[pos] in allowedCharacters:
                    position = 1
                    term+=update[pos]
                    pos+=1
                else:
                    if len(blocks) == 0:
                        raise SQLSyntaxError("Invalid character '%s' found after SET keyword."%(update[pos]))
                    else:
                        raise SQLSyntaxError("Invalid character '%s' found after '%s' in UPDATE statement"%(update[pos], blocks[0][0]))
            elif position == 1:
                if update[pos] in allowedCharacters:
                    term+=update[pos]
                    pos+=1
                elif update[pos] == ' ': # End of first column
                    position = 2
                    terms.append(term)
                    term = ''
                    pos+=1
                else:
                    terms.append(term)
                    term = ''
                    position=2
            elif position == 2:
                if update[pos] == ' ': 
                    pos+=1
                elif update[pos:pos+2] in compOperators: # The next section is a two character operator
                    terms.append(update[pos:pos+2])
                    term = ''
                    pos+=2
                    position = 4
                elif update[pos] in compOperators: # The next section is a one character operator
                    terms.append(update[pos])
                    term=''
                    pos+=1
                    position = 4
                else:
                    raise SQLSyntaxError("Invalid character '%s' found after '%s' in UPDATE statement"%(update[pos], terms[0]))
            elif position == 4:        
                if update[pos] == ' ':
                    pos+=1
                elif update[pos] == "'":
                    quote=True
                    term += "'"
                    pos+=1
                    position = 6
                elif update[pos] in allowedCharacters:
                    position = 6
                    term += update[pos]
                    pos+=1
                elif update[pos] == '?':
                    terms.append('?')
                    term = ''
                    position = 8
                    pos+=1
                    if len(update) == pos:
                        blocks.append(terms)
                        return blocks
                else:
                    raise SQLSyntaxError("Invalid character '%s' found after '%s' in UPDATE statement"%(update[pos], terms[1]))
            elif position == 6: # END SAME AS WHERE CODE
                if not quote:
                    if update[pos] in ["'",'\n']:
                        raise SQLSyntaxError("Invalid character '%s' found after = in UPDATE statement. Try removing the space after the operator or quoting the value."%(update[pos]))
                    elif update[pos] == ' ':
                        if term.upper() == 'NULL':
                            terms.append("NULL")
                        else:
                            terms.append(term)
                        term = ''
                        position = 8
                        pos+=1
                    elif update[pos] == ',':
                        if term.upper() == 'NULL':
                            terms.append('NULL')
                        else:
                            terms.append(term)
                        blocks.append(terms)
                        terms=[]
                        term = ''
                        pos+=1
                        position = 0
                    else:
                        term+=update[pos]
                        pos+=1
                        if len(update) <= pos:
                            if term.upper() == 'NULL':
                                terms.append('NULL')
                            else:
                                terms.append(term)
                            blocks.append(terms)
                            return blocks
                else:
                    if pos >= len(update)-1 and update[pos] == "'":
                        term += "'"
                        terms.append(term)
                        pos+=1
                        position = 8 
                        quote=False
                        blocks.append(terms)
                        return blocks
                    elif update[pos] == "'" and update[pos:pos+2] == "''":
                        term += "''"
                        pos += 2
                    elif update[pos] == "'" and update[pos:pos+2] == "' ":
                        pos += 2
                        term += "'"
                        quoted=False
                        terms.append(term)
                        term = ''
                        position = 8
                    elif update[pos] == "'" and update[pos:pos+2] == "',":
                        term += "'"
                        terms.append(term)
                        pos+=1
                        position = 8 
                        quote=False
                    elif update[pos] == "'":
                        raise SQLSyntaxError("Invalid character '%s' found after '%s' in UPDATE statement"%(update[pos], term))
                    else:
                        term+=update[pos]
                        pos+=1
            elif position == 8:
                if update[pos] == ' ':
                    pos+=1
                elif update[pos] == ',':
                    blocks.append(terms)
                    terms=[]
                    term = ''
                    pos+=1
                    position = 0
                    quote=False
                else:
                    raise Exception("Unexpected character %s in WHERE clause at position %s"%(repr(update[pos]), repr(pos)))
            if len(update) <= pos:
                if len(terms) == 2:
                    terms.append(term)
                    blocks.append(terms)
                    return blocks
                else:
                    raise SQLSyntaxError("SET clause ended too early. Perhaps there was an extra comma?")
        
    def parseDelete(self, sql):
        "Parse a DELETE statement"
        sql, table = self._parseTable(sql, 'DELETE', 'FROM')
        sql = stripBoth(sql)
        where=[]
        if sql[:6].lower() == 'where ':
            where = self._parseWhere(stripStart(sql[6:]))
        result = {
            'table':table,
        }
        if where:
            result['where'] = where
        return result
        

# SQL Builder
class Builder:
    """Build SQL statements from their parts
    
    - Expects all values and defaults to be properly quoted SQL
    - Doesn't do strict error checking unlike SQLParser
    """
    
    def build(self, function, **params):
        "Build an SQL statement"
        #function = params['function']
        if function == 'select':
            return self.buildSelect(**params)
        elif function == 'delete':
            return self.buildDelete(**params)
        elif function == 'insert':
            return self.buildInsert(**params)
        elif function == 'update':
            return self.buildUpdate(**params)
        elif function == 'create':
            return self.buildCreate(**params)
        elif function == 'drop':
            return self.buildDrop(**params)
        elif function == 'show':
            return "SHOW TABLES"
        else:
            raise SQLError("%s is not a supported keyword."%function.upper())
        
        return result
        
    def buildDrop(self, tables):
        "Build a DROP TABLE statements"
        if type(tables) == type(''):
            tables = [tables]
        return "DROP TABLE "+', '.join(tables)


    def buildCreate(self, table, columns):
        "Build a CREATE TABLE statements"
        sql = ['CREATE TABLE ']
        sql.append(table)
        sql.append(' (')
        sql.append(self._buildColumns(columns))
        sql.append(')')
        return ''.join(sql)
        
    def _buildColumns(self, columns):
        """Build column specifications for the CREATE statements
        
        Expects defaults to be properly quoted SQL Values"""
        sqlColumns = []
        for column in columns:
            f = []
            for param in ['name','type','required','unique','primaryKey','foreignKey','default']:
                if not column.has_key(param):
                    raise DataError('Expected the parameter %s in the column dictionary'%(repr(param)))
            for name in ['name', 'type']:
                if type(column['name']) != type(''):
                    raise DataError('Column %ss should be strings. %s is not a valid value.'%(name, repr(column['name'])))
            if column['primaryKey'] and column['default'] <> None:
                raise SQLError('A column cannot be a PRIMARY KEY and have a default value')
            if column['foreignKey'] and column['default'] <> None:
                raise SQLError('A column cannot be a FOREIGN KEY and have a default value')
            if column['primaryKey'] and column['foreignKey']:
                raise SQLError('A column cannot be a PRIMARY KEY and a FOREIGN KEY')
            f.append(column['name'])
            f.append(column['type'])
            if column['required']:
                f.append('REQUIRED')
            if column['unique']:
                f.append('UNIQUE')
            if column['primaryKey']:
                f.append('PRIMARY KEY')
            if column['foreignKey'] != None:
                f.append('FOREIGN KEY='+column['foreignKey'])
            if column['default'] != None:
                f.append('DEFAULT='+column['default'])
            sqlColumns.append(' '.join(f))
        return ', '.join(sqlColumns)

    def buildInsert(self, table, columns, sqlValues):
        "Build and INSERT statement"
        sql = ['INSERT INTO ']
        sql.append(table)
        sql.append(' (')
        sql.append(', '.join(columns))
        sql.append(') VALUES (')
        sql.append(', '.join(sqlValues))
        sql.append(')')
        return ''.join(sql)
 
    def buildSelect(self, tables, columns, where=None, order=None):
        "Build a SELECT statement."
        if type(tables) == type(''):
            tables = [tables]
        sql = ['SELECT ']
        sql.append(', '.join(columns))
        sql.append(' FROM ')
        sql.append(', '.join(tables))
        if where:
            sql.append(' WHERE')
            if type(where) == type(''):
                sql.append(' ')
                sql.append(where)
            else:
                sql.append(self._buildWhere(where))
        if order:
            sql.append(' ')
            if type(order) == type(''):
                sql.append(order)
            else:
                sql.append(self._buildOrder(order))
        return ''.join(sql)
        
    def _buildOrder(self, order):
        "Build an ORDER BY clause with the ORDER BY already removed."
        sql = ['ORDER BY ' ]
        for pair in order:
            if len(pair) != 2:
                raise DataError('Expected a the order clause to be a list of [order, value] pairs')
            if pair[1] == 'asc':
                sql.append(pair[0])
                sql.append(', ')
            elif pair[1] == 'desc':
                sql.append(pair[0])
                sql.append(' DESC, ')
            else:
                raise DataError("Expected the value of the order pair to be 'asc' or 'desc', not %s"%(repr(pair[1])))
        return ''.join(sql)[:-2] # Remove the last comma and space

    def _buildWhere(self, where):
        "Build a WHERE clause from a where list"
        sql = []
        counter = 0
        for block in where:
            sql.append(' ')
            if type(block) == type(''):
                sql.append(block)
            else:
                if block[1] not in ['>','<','=','>=','<=','<>','!=','like']:
                    raise SQLSyntaxError('Invalid comparison operator %s found at index %s of the where list'%(repr(block[1]),repr(counter)))
                sql.append(block[0])
                sql.append(block[1])
                sql.append(block[2])
            counter += 1
        return ''.join(sql)
        
    def buildUpdate(self, table, columns, sqlValues, where=None):
        "Build an UPDATE statement"
        if len(columns) != len(sqlValues):
            raise DataError("The number of columns specified doesn't match the number of values")
        sql = ['UPDATE ']
        sql.append(table)
        sql.append(' SET ')
        cols = []
        for i in range(len(columns)):
            cols.append(columns[i]+'='+sqlValues[i])
        sql.append(', '.join(cols))
        if where:
            sql.append(' WHERE')
            if type(where) == type(''):
                sql.append(' ')
                sql.append(where)
            else:
                sql.append(self._buildWhere(where))
        return ''.join(sql)

    def buildDelete(self, table, where=None):
        "Build a DELETE statement"
        sql = ['DELETE FROM %s'%table]
        if where:
            sql.append(' WHERE')
            if type(where) == type(''):
                sql.append(' ')
                sql.append(where)
            else:
                sql.append(self._buildWhere(where))
        return ''.join(sql)

class Transform(Parser, Builder):
    "Provides all the methods of both Parser and Builder classes"
    pass
