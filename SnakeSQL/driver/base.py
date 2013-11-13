"""Table and Column objects

Rationale
---------
By making all the conversion names the same it makes it easier to convert using a loop:
for i in range(len(columns)):
    table[tableName][i].valueToSQL(values[i])
By having the type as a member
# XXX All SQL conversions should use the properly quoted versions.
Note SQL to value means parsed SQL not raw SQL.


Really need to make proper use of these functions rather than eval() as implementors of other drivers may have problems

"""

# Set up True and False
try:
    True
except NameError:
    True = (1==1)
    False = (1==0)
    
from error import *
from tablePrint import table
import datetime, types, sys, os, SQLParserTools

class BaseTable:
    def __init__(self, name, filename=None, file=None, columns=[]):
        self.name = name
        self.file = file # XXX
        self.columns = columns
        self.filename = filename
        self.open = False
        self.primaryKey = None
        self.parentTables = []
        self.childTables = []
    
    def __repr__(self):
        return "<Table %s>"%self.name
        
    def has_key(self, key):
        return self.columnExists(key)

    def columnExists(self, columnName):
        for column in self.columns:
            if column.name == columnName:
                return True
        return False

    def get(self, columnName):
        for column in self.columns:
            if column.name == columnName:
                return column
        raise Bug("Column %s not found in table %s"%(repr(columnName), repr(self.name)))
        
    def __getitem__(self, name):
        if type(name) == type(1):
            return self.columns[name]
        else:
            return self.get(name)

    def _load(self):
        self.open = True
        raise Exception("Should be implemented in derived class.")

    def _close(self):
        self.open=False
        raise Exception("Should be implemented in derived class.")

    def commit(self):
        raise Exception("Should be implemented in derived class.")

    def rollback(self):
        raise Exception("Should be implemented in derived class.")

class BaseColumn:
    def __init__(self, table, name, type, required, unique, primaryKey, foreignKey, default, converter, position):
        self.name = name
        self.type = type
        self.table = table
        self.required = required
        self.unique = unique
        self.primaryKey = primaryKey
        self.foreignKey = foreignKey
        self.default = default
        self.converter = converter
        self.position = position

    def get(self, columnName):
        for column in self.columns:
            if column.name == columnName:
                return column
        raise Exception("Column %s not found."%(repr(columnName)))

class BaseConverter:
    def __init__(self):
        pass        #self.SQLQuotes = False     #self.typeCode = None

    def valueToSQL(self, value):
        "Convert a Python object to an SQL string"
        return value

    def sqlToValue(self, value):
        "Convert the an SQL string to a Python object"
        return value
    
    def storageToValue(self, value):
        "Convert the value stored in the database to a Python object"
        return value

    def valueToStorage(self, value):
        "Convert a Python object to the format needed to store it in the database"
        return value

    def SQLToStorage(self, value):
        "Convert a value returned from the SQL Parser to the format needed to store it in the database"
        return self.valueToStorage(self.sqlToValue(value))

class BaseUnknownConverter(BaseConverter):
    def __init__(self):
        a = BaseConverter.__init__(self)
        self.type = 'Unknown' # The column type should be specified in the definition
        self.SQLQuotes = False
        self.typeCode = 11
        return a

class BaseStringConverter(BaseConverter):
    def __init__(self):
        a = BaseConverter.__init__(self)
        self.type = 'String' # The column type should be specified in the definition
        self.SQLQuotes = True
        self.max  = 255
        self.typeCode = 5
        return a
    
    def storageToValue(self, column):
        if column == None:
            return None
        else:
            return str(column)
            
    def valueToStorage(self, column):
        if column == None:
            return None # Note, not NULL
        if len(str(column)) > self.max:
            raise ConversionError('Should be %s characters or less.'%self.max)
        return str(column)
        
    def valueToSQL(self, column):
        if column == None:
            return 'NULL'
        elif len(str(column)) > self.max:
            raise ConversionError('Should be %s characters or less.'%self.max)
        return "'"+str(column).replace("'","''")+"'"

    def sqlToValue(self, column):
        if column == 'NULL':
            return None
        elif len(str(column)) > self.max+2:
            raise ConversionError('Should be %s characters or less.'%self.max)
        if str(column)[0] <> "'" or str(column)[-1:] <> "'":
            raise ConversionError("%s column value %s should start and end with a ' character."%(self.type, column))
        return str(column)[1:-1].replace("''","'")

class BaseTextConverter(BaseStringConverter):
    def __init__(self):
        a = BaseStringConverter.__init__(self)
        self.type = 'Text' # The column type should be specified in the definition
        self.SQLQuotes = True
        self.max  = 16777215
        self.typeCode = 6
        return a

class BaseBinaryConverter(BaseStringConverter): # XXX Not sure how this is going to work!
    def __init__(self):
        a = BaseStringConverter.__init__(self)
        self.type = 'Binary' # The column type should be specified in the definition
        self.SQLQuotes = True
        self.max  = 16777215
        self.typeCode = 7
        return a

class BaseBoolConverter(BaseConverter):
    def __init__(self):
        a = BaseConverter.__init__(self)
        self.type = 'Bool' # The column type should be specified in the definition
        self.SQLQuotes = False
        self.typeCode = 1
        return a

    def storageToValue(self, column):
        if column == None:
            return None
        elif column in [1,0]:
            return int(column)
        else:
            raise ConversionError('Bool columns take the internal values 1 or 0 not %s, type %s'%(column,repr(type(column))[7:-2]))
        
    def valueToStorage(self, column):
        if column == None:
            return None
        elif column in [1, True]:
            return 1
        elif column in [0, False]:
            return 0
        else:
            raise ConversionError('Bool columns take can only be 1 or 0 not %s'%(column))
        
    def valueToSQL(self, column):
        if column == None:
            return 'NULL'
        elif column in [1, True]:
            return 'TRUE'
        elif column in [0, False]:
            return 'FALSE'
        else:
            raise ConversionError('Bool columns take can only be 1 or 0 not %s'%(column))
            
    def sqlToValue(self, column):
        if column == 'NULL':
            return None
        elif str(column).upper() == 'TRUE': 
            return True
        elif str(column).upper() == 'FALSE':
            return False
        else:
            raise ConversionError("Bool columns take can only be 'TRUE' or 'FALSE' not %s, type %s"%(column, repr(type(column))[7:-2]))
            
class BaseIntegerConverter(BaseConverter):
    def __init__(self):
        a = BaseConverter.__init__(self)
        self.type = 'Integer' # The column type should be specified in the definition
        self.max  = int(2L**31L-1L)
        self.min = -self.max-1
        self.SQLQuotes = False
        self.typeCode = 2
        return a
        
    def storageToValue(self, column):
        if column == None:
            return None
        else:
            try:
                i = int(column)
            except ValueError:
                raise ConversionError("Invalid value %s for %s."%(repr(column), self.type))
            else:
                if i>self.max:
                    raise ConversionError('Integer too large. Maximum value is %s'%(self.max))
                elif i<self.min:
                    raise ConversionError('Integer too small. Minimum value is %s'%(self.min))
                else:
                    return i

    def valueToStorage(self, column):
        if type(column) not in [ type(1), type(None)]:
            raise ConversionError("Invalid value %s for Integer column"%repr(column))
        v = self.storageToValue(column)
        if v == None:
            return None
        else:
            return str(v)

    def valueToSQL(self, column):
        column = self.valueToStorage(column)
        if column == None:
            return 'NULL'
        else:
            return column

    def sqlToValue(self, column):
        if column == 'NULL':
            return None
        else:
            return self.storageToValue(column)


class BaseLongConverter(BaseConverter):
    def __init__(self):
        a = BaseConverter.__init__(self)
        self.type = 'Long' # The column type should be specified in the definition
        self._conv = long
        self.SQLQuotes = False
        self.typeCode = 3
        return a
        
    def storageToValue(self, column):
        if column == None:
            return None
        else:
            try:
                i = self._conv(column)
            except ValueError:
                raise ConversionError("Invalid value %s for %s."%(repr(column), self.type))
            else:
                return i

    def valueToStorage(self, column):
        v = self.storageToValue(column)
        if v == None:
            return None
        else:
            return str(v)

    def valueToSQL(self, column):
        column = self.valueToStorage(column)
        if column == None:
            return 'NULL'
        else:
            return column

    def sqlToValue(self, column):
        if column == 'NULL':
            return None
        else:
            return self.storageToValue(column)
        
class BaseFloatConverter(BaseLongConverter):
    def __init__(self):
        a = BaseLongConverter.__init__(self)
        self.type = 'Float' # The column type should be specified in the definition
        self._conv = float
        self.SQLQuotes = False
        self.typeCode = 4
        return a

class BaseDateConverter(BaseConverter):
    def __init__(self):
        a = BaseConverter.__init__(self)
        self.type = 'Date' # The column type should be specified in the definition
        self.SQLQuotes = True
        self.typeCode = 8
        return a
        
    def storageToValue(self, column):
        if column == None:
            return None
        else:
            sql = str(column)
            try:
                return datetime.date(int(sql[0:4]),int(sql[5:7]),int(sql[8:10]))
            except ValueError:
                raise ConversionError("%s is not a valid Date string."%(repr(column)))

    def valueToStorage(self, column):
        if column == None:
            return None
        else:
            return column.isoformat()[:10]

    def valueToSQL(self, column):
        if column == None:
            return 'NULL'
        return "'"+str(self.valueToStorage(column)).replace("'","''")+"'"

    def sqlToValue(self, column):
        if column == 'NULL':
            return None
        if str(column)[0] <> "'" or str(column)[-1:] <> "'":
            raise ConversionError("%s column value %s should start and end with a ' character."%(self.type, column))
        return self.storageToValue(str(column)[1:-1].replace("''","'"))
            
        

        
class BaseDatetimeConverter(BaseConverter):
    def __init__(self):
        a = BaseConverter.__init__(self)
        self.type = 'DateTime' # The column type should be specified in the definition
        self.SQLQuotes = True
        self.typeCode = 9
        return a

    def storageToValue(self, column):
        if column == None:
            return None
        else:
            sql = str(column)
            try:
                return datetime.datetime(int(sql[0:4]),int(sql[5:7]),int(sql[8:10]),int(sql[11:13]),int(sql[14:16]),int(sql[17:19]))
            except ValueError:
                raise ConversionError("%s is not a valid DateTime string."%(repr(column)))
                
    def valueToStorage(self, column):
        if column == None:
            return None
        else:
            return column.isoformat()[:19]

    def valueToSQL(self, column):
        if column == None:
            return 'NULL'
        return "'"+str(self.valueToStorage(column)).replace("'","''")+"'"

    def sqlToValue(self, column):
        if column == 'NULL':
            return None
        if str(column)[0] <> "'" or str(column)[-1:] <> "'":
            raise ConversionError("%s column value %s should start and end with a ' character."%(self.type, column))
        return self.storageToValue(str(column)[1:-1].replace("''","'"))

class BaseTimeConverter(BaseConverter):
    def __init__(self):
        a = BaseConverter.__init__(self)
        self.type = 'Time' # The column type should be specified in the definition
        self.SQLQuotes = True
        self.typeCode = 10
        return a
        
    def storageToValue(self, column):
        if column == None:
            return None
        else:
            sql = str(column)
            try:
                return datetime.time(int(sql[0:2]),int(sql[3:5]),int(sql[6:8]))
            except ValueError:
                raise ConversionError("%s is not a valid Time string."%(repr(column)))
                
    def valueToStorage(self, column):
        if column == None:
            return None
        else:
            return column.isoformat()[:8]

    def valueToSQL(self, column):
        if column == None:
            return 'NULL'
        return "'"+str(self.valueToStorage(column)).replace("'","''")+"'"

    def sqlToValue(self, column):
        if column == 'NULL':
            return None
        if str(column)[0] <> "'" or str(column)[-1:] <> "'":
            raise ConversionError("%s column value %s should start and end with a ' character."%(self.type, column))
        return self.storageToValue(str(column)[1:-1].replace("''","'"))

class BaseConnection:
    # Other Methods
    def __init__(self, database, driver, autoCreate, colTypesName):
        self.database = database
        self.driver = driver
        self.colTypesName = colTypesName
        self.tables = {}
        self.parser = SQLParserTools.Transform()
        self.createdTables = []
        if not self.databaseExists():
            if autoCreate:
                self.createDatabase()
            else:
                raise DatabaseError("The database '%s' does not exist."%(self.database))
        self._loadTableStructure()

    def __del__(self):
        if self._closed == False:
            self.close()

    # DB-API 2.0 Methods
    def close(self): # XXX This should stop everything else from working but currently doesn't!
        """Close the connection now (rather than whenever __del__ is
        called).  The connection will be unusable from this point
        forward; an Error (or subclass) exception will be raised
        if any operation is attempted with the connection. The
        same applies to all cursor objects trying to use the
        connection.  Note that closing a connection without
        committing the changes first will cause an implicit
        rollback to be performed."""
        if self._closed:
            raise Error('The connection to the database has already been closed.')
        self.rollback()
        for table in self.tables.keys():
            if self.tables[table].open:
                self.tables[table]._close()
        self._closed = True

    def commit(self):
        """Commit any pending transaction to the database. Note that
        if the database supports an auto-commit feature, this must
        be initially off. An interface method may be provided to
        turn it back on.
        Database modules that do not support transactions should
        implement this method with void functionality."""
        if self._closed:
            raise Error('The connection to the database has been closed.')
        for table in self.tables.keys():
            if self.tables[table].open:
                self.tables[table].commit()
        self.createdTables = []
        
    def rollback(self):
        """In case a database does provide transactions this method
        causes the the database to roll back to the start of any
        pending transaction.  Closing a connection without
        committing the changes first will cause an implicit
        rollback to be performed.""" 
        if self._closed:
            raise Error('The connection to the database has been closed.')
        for table in self.tables.keys():
            if self.tables[table].open:
                self.tables[table].rollback()
        for table in self.createdTables:
            if self.tables.has_key(table):
                if self.tables[table].open:
                    self.tables[table]._close()
                del self.tables[table]
            for end in self.tableExtensions:
                if os.path.exists(self.database+os.sep+table+end):
                    os.remove(self.database+os.sep+table+end)
        self.createdTables = []

    def cursor(self):
        """Return a new Cursor Object using the connection.  If the
        database does not provide a direct cursor concept, the
        module will have to emulate cursors using other means to
        the extent needed by this specification.  [4]"""
        if self._closed:
            raise Error('The connection to the database has been closed.')
        return Cursor(self)

    # Type conversions
    def _getConverters(self, table, columns):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        typeConverters = []
        sqlConverters = []
        for column in columns:
            if not self.tables.has_key(table):
                raise SQLError("Table '%s' doesn't exist."%table)
            if not self.tables[table].columnExists(column):
                raise SQLError("Table '%s' has no column named '%s'."%(table, column))
            typeConverters.append(self.driver['converters'][self.tables[table].get(column).type.capitalize()].valueToStorage)
            sqlConverters.append(self.driver['converters'][self.tables[table].get(column).type.capitalize()].SQLToStorage)
        return sqlConverters, typeConverters
        
    # SQL helpers
    def createDatabase(self):
        "Create the database"
        #[table, column, type, required, unique, primaryKey, default]
        if self._closed:
            raise Error('The connection to the database has been closed.')

        if not self.databaseExists(): # XXX Does this need to check files don't already exist?
            if not os.path.exists(self.database):
                os.mkdir(self.database)
            if self.tables.has_key(self.colTypesName):
                raise Error("ColTypes table already exists.")
            self.tables[self.colTypesName] = self.driver['Table'](self.colTypesName, filename=self.database+os.sep+self.colTypesName, columns=[])
            self.tables[self.colTypesName]._load()
            types = ['String','String','String','Bool','Bool','Bool','Text','Text','Integer']
            self._insertRow(self.colTypesName, '1', [self.colTypesName, 'TableName',  'String', 1, 0, 0, None, None,0],types)
            self._insertRow(self.colTypesName, '2', [self.colTypesName, 'ColumnName', 'String', 1, 0, 0, None, None,1],types)
            self._insertRow(self.colTypesName, '3', [self.colTypesName, 'ColumnType', 'String', 1, 0, 0, None, None,2],types)
            self._insertRow(self.colTypesName, '4', [self.colTypesName, 'Required',   'Bool',   0, 0, 0, None, None,3],types)
            self._insertRow(self.colTypesName, '5', [self.colTypesName, 'Unique',     'Bool',   0, 0, 0, None, None,4],types)
            self._insertRow(self.colTypesName, '6', [self.colTypesName, 'PrimaryKey', 'Bool',   0, 0, 0, None, None,5],types)
            self._insertRow(self.colTypesName, '7', [self.colTypesName, 'ForeignKey', 'Text',   0, 0, 0, None, None,6],types)
            self._insertRow(self.colTypesName, '8', [self.colTypesName, 'Default',    'Text',   0, 0, 0, None, None,7],types)
            self._insertRow(self.colTypesName, '9', [self.colTypesName, 'Position',   'Integer',1, 0, 0, None, None,8],types)
            self.tables[self.colTypesName].commit()
        else:
            raise DatabaseError("The database '%s' already exists."%(self.database))

    def _loadTableStructure(self):
        "Get the values from the ColTypes table into a suitable structure."
        if self._closed:
            raise Error('The connection to the database has been closed.')
        if not self.tables.has_key(self.colTypesName):
            self.tables[self.colTypesName] = self.driver['Table'](self.colTypesName, filename=self.database+os.sep+self.colTypesName, columns=[])
            self.tables[self.colTypesName]._load()
        if not self.tables[self.colTypesName].open:
            raise Error("No Coltypes File loaded.")
        vals = []
        keys = self.tables[self.colTypesName].file.keys()
        for k in keys:
            row = self._getRow(self.colTypesName,k)
            vals.append([k,row])
        vals.sort()
        tables = {}
        for val in vals:        # Get info in the correct format
            v = val[1]
            if v[2] not in self.driver['converters'].keys():
                raise ConverterError("No converter registered for '%s' used in table '%s' column '%s'."%(v[2],v[0],v[1]))
            if not tables.has_key(v[0]):
                tables[v[0]] = []
            tables[v[0]].append(
                self.driver['Column'](
                    table = v[0],
                    name = v[1],
                    type = v[2],
                    required = v[3],
                    unique = v[4],
                    primaryKey = v[5],
                    foreignKey = v[6],
                    default = v[7],
                    converter = self.driver['converters'][v[2]],
                    position = v[8],
                )
            )
        self._checkTableFilesExist(tables.keys())
        for name, columns in tables.items():
            if name != self.colTypesName:
                self.tables[name] = self.driver['Table'](name, filename=self.database+os.sep+name, columns=columns)
            else:
                self.tables[name].columns = columns
        for name, columns in self.tables.items():
            for column in columns:
                if column.primaryKey:
                    self.tables[name].primaryKey = column.name
                if column.foreignKey:
                    self.tables[column.foreignKey].childTables.append(name)
                    self.tables[name].parentTables.append(column.foreignKey)
                    

    def _insertRowInColTypes(self, table):
        "Insert the data from Table Structure into ColTypes"
        if self._closed:
            raise Error('The connection to the database has been closed.')
        primaryKey = int(self._getNewKey(self.colTypesName))
        counter = 0
        for col in self.tables[table].columns:
            self._insertRow(self.colTypesName, primaryKey+counter, [
                    col.table, 
                    col.name, 
                    col.type, 
                    col.required, 
                    col.unique, 
                    col.primaryKey,
                    col.foreignKey, 
                    col.default, 
                    col.position
                ], types= ['String','String','String','Bool','Bool','Bool','Text','Text','Integer']
            )
            counter += 1


    def _checkTableFilesExist(self, tables):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        for table in tables: # Check each of the tables listed actually exists.
            for end in self.tableExtensions:
                if not os.path.exists(self.database+os.sep+table+end):
                    raise CorruptionError("Table file '%s' not found."%(table+end))
                    
    def _getColumnPositions(self, table, columns):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        cols = []          
        if not self.tables.has_key(table):
            raise InternalError("No such table '%s'."%(table))
        for column in columns:
            if not self.tables[table].columnExists(column):
                raise SQLError("'%s' is not a column in table '%s'."%(column, table))
            cols.append(self.tables[table].get(column).position)
        return cols

    def _convertValuesToInternal(self, table, columns, sqlValues=[], values=[]):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        #~ if values and sqlValues:
            #~ if len(sqlValues) <> len(values):
                #~ raise SQLError("The number of ? doesn't match the number of values.")
        sqlConverters, typeConverters = self._getConverters(table, columns)
        internalValues = []
        
        i = 0
        length = len(values)
        if len(sqlValues) == 0:
            for value in values:
                internalValues.append(typeConverters[i](value))
                i+=1
            return internalValues, len(values)
        else:
            counter = 0
            for value in sqlValues:
                if value == '?':
                    if len(sqlValues) > counter:
                        if counter == length:
                            raise SQLError('Too many ? specified in SQL')
                        internalValues.append(typeConverters[i](values[counter]))
                        counter += 1
                    else:
                        raise SQLError("Not enough values supplied in execute() to substitue each '?'.")
                else:
                    try:
                        internalValues.append(sqlConverters[i](value))
                    except ConversionError:
                        raise SQLSyntaxError('Incorrect quoting - ' + str(sys.exc_info()[1]))
                i+=1
            return internalValues, counter

    def _convertWhereToInternal(self, table, where='', values=[]):
        if self._closed:
            raise Error('The connection to the database has been closed.')

        if where:
            columns = []
            tables = []
            sqlValues = []
            typeConverters = []
            sqlConverters = []
            for block in where:
                if type(block) <> type(''):
                    if '.' not in block[0]:
                        if not table:
                            raise SQLError('No table specified for column %s in WHERE clause'%repr(block[0]))
                        else: # Use the default table
                            tables.append(table)
                            columns.append(block[0])
                    else:
                        table, column = block[0].split('.')
                        columns.append(column)
                        if not self.tables.has_key(table):
                            raise SQLError("Table %s specified in WHERE clause doesn't exist"%table)
                        else:
                            tables.append(table)
                    sqlValues.append(block[2])
                    if not self.tables.has_key(tables[-1]):
                        raise SQLError("Table %s specified in WHERE clause doesn't exist"%(repr(tables[-1])))
                    if not self.tables[tables[-1]].has_key(columns[-1]):
                        raise SQLError("Table %s specified in WHERE clause doesn't have a column %s"%(repr(tables[-1]), repr(columns[-1])))
                    typeConverters.append(self.driver['converters'][self.tables[tables[-1]].get(columns[-1]).type.capitalize()].valueToStorage)
                    sqlConverters.append(self.driver['converters'][self.tables[tables[-1]].get(columns[-1]).type.capitalize()].SQLToStorage)
            

            internalValues = []
            counter = 0
            i = 0
            length = len(values)
            for value in sqlValues:

                if value == '?':
                    if len(sqlValues) > counter:
                        if counter == length:
                            raise SQLError('Too many ? specified in SQL')
                        internalValues.append(typeConverters[i](values[counter]))
                        counter += 1
                    else:
                        raise SQLError("Not enough values supplied in execute() to substitue each '?'.")
                else:
                    try:
                        internalValues.append(sqlConverters[i](value))
                    except ConversionError, e:
                        if type(value) == type('') and value[0] <> "'":
                            res1 = value.split('.')
                        if len(res1) == 1:
                            raise SQLError(str(e))
                        else:
                            t1, col1 = res1
                            internalValues.append([value])
                            
                        
                        
                i+=1
            c = 0
            for i in range(len(where)):
                if type(where[i]) <> type(''):
                    where[i][2] = internalValues[c]
                    c += 1
            return where, counter
        else:
            return [], 0

            

    # Database Internal Methods
    def _tables(self):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        return self.tables.keys()

    def _columns(self, table):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        
        if not table in self._tables():
            raise SQLError('The table %s does not exist'%(repr(table)))
        cols = []    
        for i in range(len(self.tables[table].columns)):
            cols.append(None)
        for col in self.tables[table].columns:
            cols[col.position]=col.name
        return tuple(cols)
        
    # Actual SQL Methods 
    def _where(self, tables, where=[]):
        
        "Where should contain None for NULLs"
        

        if self._closed:
            raise Error('The connection to the database has been closed.')
        if type(tables) == type(''):
            tables = [tables]
        for table in tables:
            if not self.tables.has_key(table):
                raise InternalError("The table '%s' doesn't exist."%table)
            if not self.tables.has_key(table):
                self.tables[table]._load()
        # 1. Convert name to number in the array
        if len(where):
            columns = {}
            for table in tables:
                columns[table] = {}
                for column in self.tables[table].columns:
                    columns[table][column.name] = column.position
            #~ for table in tables:
                #~ for block in where:
                    #~ columns[table] = {}
            #~ for block in where:
                #~ if type(block) <> type(''):
                    #~ res = block[0].split('.')
                    #~ if len(res) == 1:
                        #~ t = tables[0]
                        #~ col = block[0]
                    #~ else:
                        #~ t, col = res
                    #~ if not columns.has_key(t):
                        #~ columns[t] = {}
                    #~ if not columns[t].has_key(block[0]):
                        #~ columns[t][col] = self.tables[t].get(col).position
            # 2. Build the if statemnt to look like this
            ifStatement = """
def like(value, sql):
    import re
    sql = sql.replace('\\\\','\\\\\\\\').replace('*','\*').replace('%%','*')
    if sql[0] == '*':
        if re.search(sql[1:], value):
            return 1
        else:
            return 0
    else:
        if re.match(sql, value):
            return 1
        else:
            return 0
tables = %s
tabs={}
for table in tables:
    tabs[table] = []
    for primaryKey in self.tables[table].file.keys():
        tabs[table].append([primaryKey, self._getRow(table, primaryKey)])
        
found = []    
"""%str(tables)
            tableString = []
            tabDepth = 0
            for table in tables:
                tableString.append("%sfor %sRow in tabs['%s']:"%(tabDepth*'    ', table, table))
                tabDepth += 1
            ifStatement+= '\n'.join(tableString)
            ifStatement+="""
%sif"""%((tabDepth)*'    ')
    # ie we need to know the keyPosition of each tables row and the position of each field we want to select against
            for block in where:
                # Prepare the values
                if type(block) == type(''):
                    ifStatement += ' '+block+' '
                else:
                    res = block[0].split('.')
                    if len(res) == 1:
                        t = tables[0]
                        col = block[0]
                    else:
                        t, col = res
                    if not self.tables[t].columnExists(col):
                        raise SQLError("'%s' in the WHERE clause is not one of the column names of table %s"%(col, t))
                    columnName = col
                    table = t
                    if block[1].lower() == 'like':
                        if '%%' in block[2]:
                            raise SQLSyntaxError("You cannot have '%%' in a LIKE clause. To escape a '%' character use '\%'.")
                        ifStatement += " like(%sRow[1][columns['%s']['%s']], %s)"%(table, table, columnName, repr(block[2]))
                    else:
                        if block[1] == '=':
                            logicalOperator = '=='
                        else:
                            logicalOperator = block[1]
                        if block[2] == None:
                            value = None
                        else:
                            if type(block[2]) == type([]):
                                res1 = block[2][0].split('.')
                                if len(res1) == 1:
                                    raise SQLSyntaxError("No '.' character found in right operand column %s in WHERE clause"%(repr(block[2])))
                                else:
                                    t1, col1 = res1
                                    value = " %sRow[1][columns['%s']['%s']]"%(t1, t1, col1)
                            else:
                                value = repr(block[2])
                        ifStatement += " %sRow[1][columns['%s']['%s']] %s %s"%(table, table, columnName, logicalOperator, value)
            tablesJoined = []
            for table in tables:
                tablesJoined.append("%sRow[0]"%(table))
            ifStatement += ":\n%sfound.append((%s))\n"%((tabDepth+1)*'    ',', '.join(tablesJoined))
            # 3. Now execute the code for each value in the database to get a list of keys
            try:
                exec(ifStatement)
            except:
                raise Bug("Exception: "+str(sys.exc_info()[1])+"If: "+ifStatement+'\n\nWhere: '+str(where))
        else:
            return self.tables[table].file.keys()
        return found

    def _getNewKey(self, table):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        if not self.tables.has_key(table):
            raise InternalError("There is no such table '%s'."%table)
        else:
            for col in self.tables[table].columns:
                if col.primaryKey:
                    raise SQLError("The table '%s' has a primary key. You cannot obtain a new integer key for it."%table)
            keys = self.tables[table].file.keys()
            if not keys:
                return 1
            else:
                keyints = []
                for key in keys:
                    try:
                        keyints.append(long(key))
                    except:
                        raise Bug('Keys for tables without a PRIMARY KEY specified should be capable of being used as integers or longs, %s in not a valid key.'%(repr(key)))
                m = max(keyints)
                try:
                    m = long(m)
                except:
                    raise SQLError("Invalid primary key '%s' for the '%s' table."%(m, table))
                else:
                    return str(m+1) 

    def _create(self, table, columns, values):
        columns = columns
        if self._closed:
            raise Error('The connection to the database has been closed.')
        # Check the table doesn't already exist
        self.createdTables.append(table) # Add to the list of created tables in case of a rollback
        if self.tables.has_key(table):
            raise SQLError("Table '%s' already exists."%table)
        # Add the column information to the ColTypes table and the tableStructure
        if not self.tables[self.colTypesName].open:
            self.tables[self.colTypesName]._load()
        # Add to tableStructure
        cols = []
        counter = 0
        defaultsUsed = 0
        for column in columns:
            if not column['type'].capitalize() in self.driver['converters'].keys():
                raise SQLError("The type '%s' selected for column '%s' isn't supported."%(column['type'],column['name']))
            default = 'NULL'
            if column['default'] != None:
                default = column['default'] 
            if default == '?':
                if len(values) == defaultsUsed:
                    raise SQLError("Not enough values specified for '?' parameter substitution")
                default = self.driver['converters'][column['type'].capitalize()].valueToStorage(values[defaultsUsed])
                defaultsUsed += 1
            else:
                default = self.driver['converters'][column['type'].capitalize()].SQLToStorage(default)
            if column['foreignKey']:
                try:
                    t = column['foreignKey']
                except ValueError:
                    raise SQLSyntaxError('Invalid value %s for FOREIGN KEY - should be of the form table.column'%(repr(column['foreignKey'])))
                if not self.tables.has_key(t):
                    raise SQLError('Table %s specified in FOREIGN KEY option does not exist'%(repr(t)))
                f = False
                for c in self.tables[t].columns:
                    if c.primaryKey:
                        f = c
                if f == False:
                    raise SQLError('Table %s specified in FOREIGN KEY option does not have a PRIMARY KEY'%(repr(t)))
                if column['type'].capitalize() <> f.type:
                    raise SQLError('Column %s specified in FOREIGN KEY option is not of the same type %s as PRIMARY KEY in table %s'%(repr(f.name), repr(f.type), repr(t)))
            cols.append(
                self.driver['Column'](
                    table, 
                    column['name'], 
                    column['type'].capitalize(),
                    column['required'],
                    column['unique'],
                    column['primaryKey'],
                    column['foreignKey'],
                    default,
                    self.driver['converters'][column['type'].capitalize()],
                    counter,
                )
            )
            counter += 1
        self.tables[table] = self.driver['Table'](table, filename=self.database+os.sep+table, columns = cols)
        self.tables[table]._load()
        # Add to ColTypes table
        self._insertRowInColTypes(table)
        return {
            'affectedRows': 0,
            'columns': ['TableName','ColumnName','ColumnType','Required','Unique','PrimaryKey','ForeignKey','Default','Position'],
            'table': table,
            'results':  None,
        }

    def _drop(self, tables):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        if type(tables) == type(''):
            tables = [tables]
        for table in tables:
            if not self.tables.has_key(table):
                raise SQLError("Cannot drop '%s'. Table not found."%(table))
            if not self.tables[table].open:
                self.tables[table]._load()
            # Check foreign key constraints:
            # cannot drop a parent table until all children are removed, can drop child table
            if self.tables[table].childTables:
                for child in self.tables[table].childTables:
                    if not child in tables:
                            raise SQLForeignKeyError('Cannot drop table %s since child table %s has a foreign key reference to it'%(repr(table), repr(child)))
        for table in tables:
            # Remove from ColTypes table
            self._delete(self.colTypesName, where=[['TableName',"=","'"+table+"'"]])
            # Close table and remove from files list
            if self.tables.has_key(table):
                self.tables[table]._close()
                del self.tables[table]
            # Delete the actual files
            self._deleteTableFromDisk(table)
            # Delete table structure
            if table in self.createdTables:
                self.createdTables.pop(self.createdTables.index(table))
        return {
            'affectedRows': 0,
            'columns': None,
            'table': tables,
            'results':  None,
        }

    def _insert(self, table, columns, sqlValues=[], values=[]):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        if not self.tables.has_key(table):
            raise SQLError("Table '%s' not found."%(table))
        internalValues, used = self._convertValuesToInternal(table, columns, sqlValues, values)
        if not self.tables[table].open:
            self.tables[table]._load()
        # Get a new primaryKey
        primaryKey = None
        for col in self.tables[table].columns:
            if col.primaryKey:
                primaryKey = col.name
                break
        if primaryKey and primaryKey not in columns:
            raise SQLKeyError("PRIMARY KEY '%s' must be specified when inserting into the '%s' table."%(primaryKey, table))
        elif not primaryKey:
            keyval = self._getNewKey(table)
        else:
            keyval = internalValues[columns.index(primaryKey)]
            if self.tables[table].file.has_key(keyval):
                raise SQLKeyError("Row with the PRIMARY KEY '%s' already exists."%(keyval))
        # XXX Should unique mean "unique apart from NULLs"?
        for col in self.tables[table].columns:
            name = col.name
            # Check other internalValues needing to be unique are
            if col.unique and name in columns:
                for primaryKey in self.tables[table].file.keys():
                    row = self._getRow(table,primaryKey)
                    oldval = row[col.position]
                    val = internalValues[columns.index(name)]
                    if val <> None and val == oldval:
                        raise SQLError("The UNIQUE column '%s' already has a value '%s'."%(name,val))
            if col.required and name not in columns:
                raise SQLError("The REQUIRED value '%s' has not been specified."%(name))
            if col.required and internalValues[columns.index(name)] == None:
                raise SQLError("The REQUIRED value '%s' cannot be NULL."%(name))
            if col.primaryKey:
                if name not in columns:
                    # XXX Already specified.
                    raise SQLError("The PRIMARY KEY '%s' has not been specified."%(name))
                elif internalValues[columns.index(name)] == None:
                    raise SQLError("The PRIMARY KEY value '%s' cannot be NULL."%(name))
                    

        # Arrange the internalValues in the correct order, filling defaults as necessary
        cols = []
        for col in self.tables[table].columns:
            cols.append([col.position, col.name])
        cols.sort()
        columnNames = []
        defaults = []
        for col in cols:
            columnNames.append(col[1])
            defaults.append(self.tables[table].get(col[1]).default)
        vals = []
        for col in columns:
            if col not in columnNames:
                raise SQLError("Column '%s' does not exist in table '%s'."%(col, table))
            defaults[columnNames.index(col)] = internalValues[columns.index(col)]
            vals.append(internalValues[columns.index(col)])

        # Check foreign keys are specified if needed
        if self.tables[table].parentTables:
            for column in self.tables[table].columns:
                if column.foreignKey:
                    if column.name not in columns:
                        raise SQLForeignKeyError("Foreign key %s not specified when inserting into table %s"%(repr(column.name), repr(table)))
                    else:
                        v = []
                        results = self._select([self.tables[column.foreignKey].primaryKey], column.foreignKey, [], [])['results']
                        for result in results:
                            v.append(result[0])
                        if defaults[column.position] not in v:
                            raise SQLForeignKeyError("Invalid value for foreign key %s since table %s does not have a primary key value %s"%(repr(column.name), repr(column.foreignKey), repr(defaults[column.position])))

        self._insertRow(table, keyval, defaults)
        return {
            'affectedRows': 1,
            'columns': columns,
            'table': table,
            'results':  None,
        }
        
    def _update(self, table, columns, where=[], sqlValues=[], values=[]):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        if not self.tables.has_key(table):
            raise SQLError("Table '%s' not found."%(table))
        internalValues, used = self._convertValuesToInternal(table, columns, sqlValues, values)
        where, used2 = self._convertWhereToInternal(table, where, values[used:])
        if not used+used2 == len(values):
            raise SQLError('There are %s ? in the SQL but %s values have been specified to replace them.'%(used+used2, len(values)))
        if not self.tables[table].open:
            self.tables[table]._load()
        positions = self._getColumnPositions(table, columns)
        keys = self._where(table, where)
        #print keys
            #keys.append(result[0])
        if not keys:
            return {
                'affectedRows': 0,
                'columns': columns,
                'table': table,
                'results':  None,
            }   
        elif len(keys) > 1:
            # Check that there isn't a or unique column being updated with more than one value
            for col in self.tables[table].columns:
                if col.unique and col.name in columns:
                    raise SQLError("The UNIQUE column '%s' cannot be updated setting %s values to %s."%(col.name,len(keys),repr(internalValues[columns.index(col.name)])))
                if col.primaryKey and col.name in columns:
                    raise SQLError("The PRIMARY KEY column '%s' cannot be updated setting %s values to %s."%(col.name,len(keys),repr(internalValues[columns.index(col.name)])))
        newkey=None
        for col in self.tables[table].columns:
            # Check other internalValues needing to be unique are
            if col.unique and col.name in columns:
                for primaryKey in self.tables[table].file.keys():
                    if not primaryKey in keys:
                        oldval = self._getRow(table,primaryKey)[col.position]
                        val = internalValues[columns.index(col.name)]
                        if val <> None and val == oldval:
                            raise SQLError("The UNIQUE column '%s' already has a value '%s'."%(col.name,oldval))
            if col.required and col.name in columns and internalValues[columns.index(col.name)] == None:
                    raise SQLError("The REQUIRED value '%s' cannot be NULL."%(col.name))
            if col.primaryKey: # ie must be just one update otherwise would have raised an error earlier
                if col.name in columns:
                    if internalValues[columns.index(col.name)] == None:
                        raise SQLError("The PRIMARY KEY value '%s' cannot be NULL."%(col.name))
                    for primaryKey in self.tables[table].file.keys():
                        if not primaryKey in keys and primaryKey == internalValues[columns.index(col.name)]:
                            raise SQLError("A PRIMARY KEY '%s' has already been specified."%(col.name))
                    newkey = internalValues[columns.index(col.name)]
        # Check foreign key constraints
        # 1. Find out if this is a child table
        if self.tables[table].parentTables:
            # 2. See if we are updating any Foreign Keys
            counter = 0
            for column in columns:
                column = self.tables[table].get(column)
                if column.foreignKey:
                    v = []
                    results = self._select([self.tables[column.foreignKey].primaryKey], column.foreignKey, [], [])['results']
                    for result in results:
                        v.append(result[0])
                if not internalValues[counter] in v:
                    raise SQLForeignKeyError("Invalid value for foreign key %s since table %s does not have a primary key value %s"%(repr(column.name), repr(column.foreignKey), repr(internalValues[counter])))
                counter += 1

        vals=[]
        #print keys
        for primaryKey in keys:
            if not self.tables[table].file.has_key(primaryKey):
                raise DatabaseError("Table %s has no row with the primary key %s."%(repr(table), repr(primaryKey)))
            else:
                row = self._getRow(table, primaryKey)
                for pos in range(len(positions)):
                    row[positions[pos]] = internalValues[pos]
                self._updateRow(table, primaryKey, newkey, row)
                vals.append(row)
        return {
            'affectedRows': len(keys),
            'columns': columns,
            'table': table,
            'results':  None,
        }

    def _select(self, columns, tables, where, order, values=[]):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        if type(tables) == type(''):
            tables = [tables]
        for table in tables:
            if not self.tables.has_key(table):
                raise SQLError("Table '%s' not found."%(table))
            if not self.tables[table].open:
                self.tables[table]._load()
        cols = []
        if columns == ['*']:
            fullList = []
            if len(tables) == 1:
                for column in self._columns(tables[0]):
                    fullList.append(column)
                    cols.append(self.tables[tables[0]].get(column).position)
            else:
                for table in tables:
                    offset = len(fullList)
                    for column in self._columns(table):
                        fullList.append(table+'.'+column)
                        cols.append(offset + self.tables[table].get(column).position)
            columns = fullList
        elif len(tables) == 1:
            for i in range(len(columns)):
                if columns[i][:len(tables[0])+1] == tables[0]+'.':
                    columns[i] = columns[i].split('.')[1]
                elif '.' in columns[i]:
                    raise SQLSyntaxError("Table in column name %s is not listed after the FROM part of the SELECT statement"%(repr(columns[i].split()[0]), repr(columns[i])))
                cols.append(self._getColumnPositions(tables[0], [columns[i]])[0])
        else:
            lengths = [0]
            for table in tables:
                if len(lengths) == 0:
                    lengths.append(len(self._columns(table)))
                else:
                    lengths.append(lengths[-1]+len(self._columns(table)))
            for column in columns:
                if '.' not in column:
                    raise SQLSyntaxError("Expected table name followed by a '.' character before column name %s "%column)
                else:
                    res = column.split('.')
                    if len(res) <> 2:
                        raise SQLError("Invalid column name %s too many '.' characters."%column)
                    cols.append(lengths[tables.index(res[0])]+self._getColumnPositions(res[0], [res[1]])[0])
        where, used = self._convertWhereToInternal(table, where, values)
        if not used == len(values):
            raise SQLError('There are %s ? in the SQL but %s values have been specified to replace them.'%(used, len(values)))
        keys = self._where(tables, where)
        if keys:
            rows = []
            for results in keys:
                if type(results) <> type((1,)):
                    r = self._getRow(tables[0], results)
                else:
                    r = []
                    for i in range(len(results)):
                        for term in self._getRow(tables[i], results[i]):
                            r.append(term)
                rows.append(r)
            results = []
            for row in rows:
                result = []
                for col in cols:
                    result.append(row[col])
                results.append(result)
            if order:
                orderDesc = []
                orderCols = []
                for order in order:
                    orderCols.append(order[0])
                    orderDesc.append(order[1])
                orderPos = self._getColumnPositions(table, orderCols)
    
                class OrderCompare:
                    def __init__(self, orderPos, orderDesc):
                        self.orderPos  = orderPos
                        self.orderDesc = orderDesc
                    
                    def __call__(self, x, y):
                        for i in range(len(self.orderPos)):
                            if x[self.orderPos[i]] < y[self.orderPos[i]]:
                                if self.orderDesc[i] == 'asc':
                                    return -1
                                else:
                                    return 1
                            elif x[self.orderPos[i]] > y[self.orderPos[i]]:
                                if self.orderDesc[i] == 'asc':
                                    return 1
                                else:
                                    return -1
                        return 0
    
                results.sort(OrderCompare(orderPos, orderDesc))
            if len(tables) == 1:
                tables = tables[0]
            return {
                'affectedRows': len(results),
                'columns': columns,
                'table': tables,
                'results':  tuple(results),
            }
        else:
            if len(tables) == 1:
                tables = tables[0]
            return {
                'affectedRows': 0,
                'columns': columns,
                'table': tables,
                'results': [],
            }
    def _delete(self, table, where=[], values=[]):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        if not self.tables.has_key(table):
            raise SQLError("Table '%s' not found."%(table))
        if not self.tables[table].open:
            self.tables[table]._load()
        where, used = self._convertWhereToInternal(table, where, values)
        if not used == len(values):
            raise SQLError('There are %s ? in the SQL but %s values have been specified to replace them.'%(used, len(values)))
        keys = self._where(table, where)
            #keys.append(result[0])
        # Check foreign key constraints
        # 1. Find out if this is a parent table
        if self.tables[table].childTables:
            # 2. If they do get all the distinct primary key values of the table, cahing the values
            parentTableKeyValues = []
            results = self._select([self.tables[table].primaryKey], table, [], [])['results']
            for result in results:
                if result[0] in parentTableKeyValues:
                    raise Bug('Duplicate key values %s in table %s'%(repr(table), repr(result[0])))
                else:
                    parentTableKeyValues.append(result[0])
            # 3. For all the child table columns with this table as a foreign key, check the cache to make sure
            #    the value doesn't exist.
            for childTable in self.tables[table].childTables:
                foreignKeyPosition = None
                for column in self.tables[childTable].columns:
                    if column.foreignKey:
                        foreignKeyPosition = column.position
                if foreignKeyPosition == None:
                    raise Bug('No foreign key found in child table.')
                else:
                    if not self.tables[childTable].open:
                        self.tables[childTable]._load()
                    for key in self.tables[childTable].file.keys():
                        row = self._getRow(childTable, key)
                        if row[foreignKeyPosition] in parentTableKeyValues:
                            raise SQLForeignKeyError("Table %s contains references to record with PRIMARY KEY %s in %s"%(repr(childTable), repr(key), repr(table)))
        # Delete the rows
        for primaryKey in keys:
            if not self.tables[table].open:
                self.tables[table]._load()
            if not self.tables[table].file.has_key(primaryKey):
                raise DatabaseError("Table %s has no row with the primary key %s."%(repr(table), repr(primaryKey)))
            else:
                self._deleteRow(table, primaryKey)
        return {
            'affectedRows': len(keys),
            'columns': None,
            'table': table,
            'results': None,
        }
        
    def _showTables(self):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        tables = self._tables()
        results = []
        for table in tables:
            results.append([table])
        return {
            'affectedRows': 0,
            'columns': ['Tables'],
            'table': None,
            'results': results,
        }

class Cursor:
    """These objects represent a database cursor, which is used to
    manage the context of a fetch operation. Cursors created from 
    the same connection are not isolated, i.e., any changes
    done to the database by a cursor are immediately visible by the
    other cursors. Cursors created from different connections can
    or can not be isolated, depending on how the transaction support
    is implemented (see also the connection's rollback() and commit() 
    methods.)
    
    My note:
    SQL Values should be specified with single quotes.
    
    self.info has the following specification:
    'columns'      - list of column names from the result set
    'table'        - table name of result set
    'results'      - tuple of results or None if no result set
    'affectedRows' - number of affected rows.
    """

    def __init__(self, connection, debug=False, format='tuple'):
        self.debug = debug
        self.format = format
        self.sql = []
        self._closed = False
        self.connection = connection
        if self.connection._closed:
            raise Error('The connection to the database has been closed.')
        self.info = {'affectedRows':0,'columns':[],'results':(),'table':''}
        # DB-API 2.0 attributes:
        self.arraysize = 1
        """This read/write attribute specifies the number of rows to
        fetch at a time with fetchmany(). It defaults to 1 meaning
        to fetch a single row at a time.
        
        Implementations must observe this value with respect to
        the fetchmany() method, but are free to interact with the
        database a single row at a time. It may also be used in
        the implementation of executemany()."""
        self.position = 0

    def __getattr__(self, name):
        #~ converter = None # Use the converter methods as class methods
        #~ if name[:2] == 'to':
            #~ converter = 'SQLTo' + name[2:]
        #~ elif name[:5] == 'SQLTo' or name[5:] == 'ToSQL':
            #~ converter = name
        #~ if converter:
            #~ return self.connection._converter(converter)
        #~ el
        if name == 'rowcount':
            """This read-only attribute specifies the number of rows that
            the last executeXXX() produced (for DQL statements like
            'select') or affected (for DML statements like 'update' or
            'insert').
            
            The attribute is -1 in case no executeXXX() has been
            performed on the cursor or the rowcount of the last
            operation is not determinable by the interface. [7]
    
            Note: Future versions of the DB API specification could
            redefine the latter case to have the object return None
            instead of -1."""
            return self.info['affectedRows']
        elif name == 'description':
            """This read-only attribute is a sequence of 7-item
            sequences.  Each of these sequences contains information
            describing one result column: (name, type_code,
            display_size, internal_size, precision, scale,
            null_ok). The first two items (name and type_code) are
            mandatory, the other five are optional and must be set to
            None if meaningfull values are not provided.
    
            This attribute will be None for operations that
            do not return rows or if the cursor has not had an
            operation invoked via the executeXXX() method yet.
            
            The type_code can be interpreted by comparing it to the
            Type Objects specified in the section below."""
            if self.info['results'] == None:
                return None
            else:
                l = []
                if self.info['table'] in self.connection.tables.keys() and self.info['columns']:
                    for column in self.info['columns']:
                        l.append(
                            (
                                column,
                                _type_codes[self.connection.tables[self.info['table']].get(column).type],
                                None,
                                None,
                                None,
                                None,
                                self.connection.tables[self.info['table']].get(column).required,
                            )
                        )
                    return tuple(l)
                else:
                    raise Bug("No table specified or no columns present.")
        else:
            raise AttributeError("Cursor instance has no attribute %s"%(repr(name)))
            
    def executemany(self, operation, seq_of_parameters):
        """Prepare a database operation (query or command) and then
        execute it against all parameter sequences or mappings
        found in the sequence seq_of_parameters.
        
        Modules are free to implement this method using multiple
        calls to the execute() method or by using array operations
        to have the database process the sequence as a whole in
        one call.
        
        Use of this method for an operation which produces one or
        more result sets constitutes undefined behavior, and the
        implementation is permitted (but not required) to raise 
        an exception when it detects that a result set has been
        created by an invocation of the operation.
        
        The same comments as for execute() also apply accordingly
        to this method.
        
        Return values are not defined."""
        if self._closed:
            raise Error('The cursor has been closed.')
        if self.connection._closed:
            raise Error('The connection to the database has been closed.')
        for parameters in seq_of_parameters:
            self.execute(operation, parameters)
        
    def execute(self, operation, parameters=[]):
        """Prepare and execute a database operation (query or
        command).  Parameters may be provided as sequence or
        mapping and will be bound to variables in the operation.
        Variables are specified in a database-specific notation
        (see the module's paramstyle attribute for details). [5]
        
        A reference to the operation will be retained by the
        cursor.  If the same operation object is passed in again,
        then the cursor can optimize its behavior.  This is most
        effective for algorithms where the same operation is used,
        but different parameters are bound to it (many times).
        
        For maximum efficiency when reusing an operation, it is
        best to use the setinputsizes() method to specify the
        parameter types and sizes ahead of time.  It is legal for
        a parameter to not match the predefined information; the
        implementation should compensate, possibly with a loss of
        efficiency.
        
        The parameters may also be specified as list of tuples to
        e.g. insert multiple rows in a single operation, but this
        kind of usage is depreciated: executemany() should be used
        instead."""
        if self._closed:
            raise Error('The cursor has been closed.')
        if self.connection._closed:
            raise Error('The connection to the database has been closed.')
        # start web.database
        if self.debug:
            self.sql.append(sql)
        # end web.database
        if type(parameters) not in [type(()), type([])]:
            parameters = [parameters]
        parsedSQL = self.connection.parser.parse(operation)
        if parsedSQL['function'] == 'create':
            self.info = self.connection._create(parsedSQL['table'], parsedSQL['columns'], parameters)
        elif parsedSQL['function'] == 'drop':
            self.info = self.connection._drop(parsedSQL['tables'])
        elif parsedSQL['function'] == 'insert':
            self.info = self.connection._insert(parsedSQL['table'], parsedSQL['columns'], parsedSQL['sqlValues'], parameters)
        elif parsedSQL['function'] == 'update':
            if parsedSQL.has_key('where'):
                self.info = self.connection._update(parsedSQL['table'], parsedSQL['columns'], parsedSQL['where'], parsedSQL['sqlValues'], parameters)
            else:
                self.info = self.connection._update(parsedSQL['table'], parsedSQL['columns'], sqlValues = parsedSQL['sqlValues'], values = parameters)
        elif parsedSQL['function'] == 'select':
            del parsedSQL['function']
            return self.select(**parsedSQL)
        elif parsedSQL['function'] == 'delete':
            if parsedSQL.has_key('where'):
                self.info = self.connection._delete(parsedSQL['table'], parsedSQL['where'], parameters)
            else:
                self.info = self.connection._delete(parsedSQL['table'], values=parameters)
        elif parsedSQL['function'] == 'show':
            self.info = self.connection._showTables()
        else:
            raise SQLError("%s is not a supported keyword."%parsedSQL['function'].upper())
        self.position = 0

    def fetchall(self, autoConvert=True, format=None):
        """Fetch all (remaining) rows of a query result, returning
        them as a sequence of sequences (e.g. a list of tuples).
        Note that the cursor's arraysize attribute can affect the
        performance of this operation.
        
        An Error (or subclass) exception is raised if the previous
        call to executeXXX() did not produce any result set or no
        call was issued yet."""
        if self._closed:
            raise Error('The cursor has been closed.')
        if self.connection._closed:
            raise Error('The connection to the database has been closed.')
        return self.fetchmany('all', autoConvert, format)

    def fetchone(self, autoConvert=True, format=None):
        """Fetch the next row of a query result set, returning a
        single sequence, or None when no more data is
        available. [6]
        
        An Error (or subclass) exception is raised if the previous
        call to executeXXX() did not produce any result set or no
        call was issued yet."""
        if self._closed:
            raise Error('The cursor has been closed.')
        if self.connection._closed:
            raise Error('The connection to the database has been closed.')
        if self.info['results'] == None:
            raise Error('Previous call to execute() did not produce a result set. No results to fetch.')
        else:
            res = self.fetchmany(1, format)
            if res == ():
                return None
            else:
                return res[0]
        
        
    def fetchmany(self, size=None, autoConvert=True, format=None):
        """Fetch the next set of rows of a query result, returning a
        sequence of sequences (e.g. a list of tuples). An empty
        sequence is returned when no more rows are available.
        
        The number of rows to fetch per call is specified by the
        parameter.  If it is not given, the cursor's arraysize
        determines the number of rows to be fetched. The method
        should try to fetch as many rows as indicated by the size
        parameter. If this is not possible due to the specified
        number of rows not being available, fewer rows may be
        returned.
        
        An Error (or subclass) exception is raised if the previous
        call to executeXXX() did not produce any result set or no
        call was issued yet.
        
        Note there are performance considerations involved with
        the size parameter.  For optimal performance, it is
        usually best to use the arraysize attribute.  If the size
        parameter is used, then it is best for it to retain the
        same value from one fetchmany() call to the next."""
        if self._closed:
            raise Error('The cursor has been closed.')
        if self.connection._closed:
            raise Error('The connection to the database has been closed.')
        if self.info['results'] == None:
            raise Error('Previous call to execute() did not produce a result set. No results to fetch.')
        else:
            results = None
            if autoConvert and self.info['table']:
                converters = []
                for column in self.info['columns']:
                    if type(self.info['table']) == type([]):
                        converters.append(self.connection.tables[column.split('.')[0]].get(column.split('.')[1]).converter.storageToValue)
                    else:    
                        converters.append(self.connection.tables[self.info['table']].get(column).converter.storageToValue)
                    
                #print len(self.info['columns']), self.info['results'][0]
                rows = []
                for result in self.info['results']:
                    row = []
                    
                    for i in range(len(result)):
                        c = converters[i]
                        r = result[i]
                        row.append(c(r))
                    rows.append(tuple(row))
                results = tuple(rows)
            else:
                results = tuple(self.info['results'])
            if size == None:
                # XXX returnVal = results[self.position:self.arraysize] self.arraysize ignored considered infinity.
                results = results[self.position:]
            elif size == 'all':
                pass#results = results
            else:
                #results[self.position:self.position+size]
               #if max value returned
                #print len(results)
                if self.position + size <= len(results):
                    res = results[self.position:self.position+size]
                    self.position += size
                    results = res
                else:
                    return ()
        
            # start web.database
            if format == None:
                format = self.format
            if format == 'text':
                if results <> None:
                    return table(self.info['columns'], results, mode='sql')
            else:
                rows = []
                for row in results:
                    if format == 'dict':
                        dict={}
                        for i in range(len(row)):
                            dict[self.info['columns'][i]] = row[i]
                        rows.append(dict)
                    elif format == 'object':
                        descr = dtuple.TupleDescriptor([[n] for n in self.info['columns']])
                        rows.append(dtuple.DatabaseTuple(descr, row))
                    elif format == 'tuple':
                        rows.append(tuple(row))
                    else:
                        raise Bug("'%s' is not a valid option for format."%format)
                return tuple(rows)
            # end web.database

    # Unused DB-API 2.0 Methods
    def setinputsizes(self, sizes):
        """This can be used before a call to executeXXX() to
        predefine memory areas for the operation's parameters.
        
        sizes is specified as a sequence -- one item for each
        input parameter.  The item should be a Type Object that
        corresponds to the input that will be used, or it should
        be an integer specifying the maximum length of a string
        parameter.  If the item is None, then no predefined memory
        area will be reserved for that column (this is useful to
        avoid predefined areas for large inputs).
        
        This method would be used before the executeXXX() method
        is invoked.
        
        Implementations are free to have this method do nothing
        and users are free to not use it."""
        if self._closed:
            raise Error('The cursor has been closed.')
        if self.connection._closed:
            raise Error('The connection to the database has been closed.')
        else:
            pass

    def setoutputsize(self, size, column=None):
        """Set a column buffer size for fetches of large columns
        (e.g. LONGs, BLOBs, etc.).  The column is specified as an
        index into the result sequence.  Not specifying the column
        will set the default size for all large columns in the
        cursor.
        
        This method would be used before the executeXXX() method
        is invoked.
        
        Implementations are free to have this method do nothing
        and users are free to not use it."""
        if self._closed:
            raise Error('The cursor has been closed.')
        if self.connection._closed:
            raise Error('The connection to the database has been closed.')
        else:
            pass

    def close(self):
        """Close the cursor now (rather than whenever __del__ is
        called).  The cursor will be unusable from this point
        forward; an Error (or subclass) exception will be raised
        if any operation is attempted with the cursor."""
        if self.connection._closed:
            raise Error('The connection to the database has been closed.')
        if self._closed:
            raise Error('The cursor has already been closed.')
        else:
            self._closed = True

    # Unimplemented DB-API 2.0 Methods
    #~ def callproc(self, procname[,parameters])
        #~ """(This method is optional since not all databases provide
        #~ stored procedures. [3])
        
        #~ Call a stored database procedure with the given name. The
        #~ sequence of parameters must contain one entry for each
        #~ argument that the procedure expects. The result of the
        #~ call is returned as modified copy of the input
        #~ sequence. Input parameters are left untouched, output and
        #~ input/output parameters replaced with possibly new values.
        
        #~ The procedure may also provide a result set as
        #~ output. This must then be made available through the
        #~ standard fetchXXX() methods."""
        #~ pass
        
    #~ def nextset(self) 
        #~ """(This method is optional since not all databases support
        #~ multiple result sets. [3])
        
        #~ This method will make the cursor skip to the next
        #~ available set, discarding any remaining rows from the
        #~ current set.
        
        #~ If there are no more sets, the method returns
        #~ None. Otherwise, it returns a true value and subsequent
        #~ calls to the fetch methods will return rows from the next
        #~ result set.
        
        #~ An Error (or subclass) exception is raised if the previous
        #~ call to executeXXX() did not produce any result set or no
        #~ call was issued yet."""
        #~ pass
        
    # Non DB-API Methods
    def __del__(self):
        if not self.connection._closed and not self._closed:
            return self.close()
        
    def tables(self):
        if self._closed:
            raise Error('The cursor has been closed.')
        if self.connection._closed:
            raise Error('The connection to the database has been closed.')
        return self.connection._tables()

    def columns(self, table):
        if self._closed:
            raise Error('The cursor has been closed.')
        if self.connection._closed:
            raise Error('The connection to the database has been closed.')
        return self.connection._columns(table)



    # web.database API
    def tableExists(self, table):
        if table in self.tables():
            return True
        else:
            return False
        
    def columnExists(self, column, table):
        if column in self.columns(table):
            return True
        else:
            return False

    #def execute():
    #   if self.debug:
    #       self.sql.append(sql)
    

    #def fetchall(format=None):
    #    

#
# SQL statement generators
#
       
    def select(self, columns, tables, where=None, order=None, execute=None, format=None, distinct=False):
        #if as <> None:
        #    raise NotSupportedError("SnakeSQL doesn't support aliases.")
        #if distinct:
        #    raise NotSupportedError("SnakeSQL doesn't support the DISTINCT keyword.")
        if format == None:
            format = self.format
        if type(columns) == type(''):
            columns = [columns]
        if type(tables) == type(''):
            tables = [tables]
        if execute == False:
            return self.connection.parser.buildSelect(tables, columns, where, order)
        else:
            # Don't need to worry about convertResult since it is taken care of in fetchRows()
            # Don't need to worry about format since it is taken care of in fetchRows()
            if type(where) == type(''):
                where = self.where(where)
            if type(order) == type(''):
                order = self.order(order)
            #if columns == ['*']:
            #    columns = self.columns(table)
            self.info = self.connection._select(
                columns=columns,
                tables=tables,
                where=where,
                order=order,
            )
            return self.fetchall(format=format)

    def insert(self, table, columns, values=None, sqlValues=None, execute=None):
        if sqlValues == None and values == None:
            raise SQLError('You must specify either values or sqlValues, they can be []')
        if sqlValues <> None and values <> None:
            raise SQLError('You cannot specify both values and sqlvalues')
        if type(columns) == type(''):
            columns = [columns]
        if type(values) not in [type((1,)), type([])]:
            values = [values]
        if type(sqlValues) not in [type((1,)), type([])]:
            sqlValues = [sqlValues]
        if (sqlValues <> [None] and len(columns) <> len(sqlValues)) or (values <> [None] and len(columns) <> len(values)):
            raise SQLError('The number of columns does not match the number of values')
        if execute == False:                
            if sqlValues == [None]:
                sqlValues = []
                if not self.connection.tables.has_key(table):
                    raise SQLError("Table '%s' doesn't exist."%table)
                for i in range(len(columns)):
                    if not self.connection.tables[table].columnExists(columns[i]):
                        raise SQLError("Table '%s' has no column named '%s'."%(table, columns[i]))
                    sqlValues.append(self.connection.driver['converters'][self.connection.tables[table].get(columns[i]).type.capitalize()].valueToSQL(values[i]))
            return self.connection.parser.buildInsert(table, columns, sqlValues)
        else:
            self.info = self.connection._insert(
                table=table, 
                columns=columns, 
                values=values, # Note: not sqlValues
            )
            #return sql

    def update(self, table, columns, values=None, sqlValues=None, where=None, execute=None):
        if sqlValues == None and values == None:
            raise SQLError('You must specify either values or sqlValues, they can be []')
        if sqlValues <> None and values <> None:
            raise SQLError('You cannot specify both values and sqlvalues')
        if type(columns) == type(''):
            columns = [columns]
        if type(values) not in [type((1,)), type([])]:
            values = [values]
        if type(sqlValues) not in [type((1,)), type([])]:
            sqlValues = [sqlValues]
        if (sqlValues <> [None] and len(columns) <> len(sqlValues)) or (values <> [None] and len(columns) <> len(values)):
            raise SQLError('The number of columns does not match the number of values')
        if execute == False:                
            if sqlValues == [None]:
                sqlValues = []
                if not self.connection.tables.has_key(table):
                    raise SQLError("Table '%s' doesn't exist."%table)
                for i in range(len(columns)):
                    if not self.connection.tables[table].columnExists(columns[i]):
                        raise SQLError("Table '%s' has no column named '%s'."%(table, columns[i]))
                    sqlValues.append(self.connection.driver['converters'][self.connection.tables[table].get(columns[i]).type.capitalize()].valueToSQL(values[i]))
            return self.connection.parser.buildUpdate(table, columns, sqlValues, where)
        else:
            if type(where) == type(''):
                where = self.where(where)
            self.info = self.connection._update(
                table=table, 
                columns=columns, 
                values=values, # Note: not sqlValues
                where=where,
            )
            #return sql

    def delete(self, table, where=None, execute=None):
        if execute == False:
            return self.connection.parser.buildDelete(table, where)
        else:
            if type(where) == type(''):
                where = self.where(where)
            self.info = self.connection._delete(
                table=table, 
                where=where,
            )
            #return sql

    def create(self, table, columns, execute=None):
        f = []
        for column in columns:
            if type(column) == type(''):
                f.append(self.column(column))
            else:
                f.append(column)        
        if execute == False:
            return self.connection.parser.buildCreate(table, f)
        else:
            self.info = self.connection._create(
                table=table, 
                columns=f,
            )
            #return sql

    def drop(self, tables, execute=None):
        "Remove a table from the database."
        if execute == False:
            return self.connection.parser.buildDrop(tables)
        else:
            self.info = self.connection._drop(tables=tables)
            #return sql

    #~ def max(self, column, table, where=None):
        #~ return self._function('max',column, table, where, True)
        
    #~ def min(self, column, table, where=None):
        #~ return self._function('min',column, table, where, True)

    #~ def _function(self, func, column, table, where=None, execute=None):
        #~ autoConvert = self._autoConvert
        #~ if execute <> None:
            #~ if execute not in self._autoExecuteOptions:
                #~ raise DatabaseError("execute must be one of %s."%(str(self._autoExecuteOptions),))
        #~ else:
            #~ execute = self._autoExecute

        #~ if func.upper() in ['MAX', 'MIN']:
            #~ if self._autoConvert == True:
                #~ if not self._typesCache.has_key(table.upper()):
                    #~ self._getTableData(table)
                #~ if not self._typesCache[table.upper()].has_key(column.upper()):
                    #~ raise Exception("No types information available for '%s' column in table '%s'."%(column, table))
                #~ self._colTypes = [self._typesCache[table.upper()][column.upper()]]
            #~ self._colName = [column]

            #~ sql = "SELECT %s(%s) FROM %s" % (func, column, table)
            #~ if where:
                #~ sql += " WHERE %s" % where

            #~ self.execute(sql)
            #~ val = self.fetchRows('tuple', None)[0][0]
            #~ return val
        #~ else:
            #~ raise DatabaseError("The function '%s' is not supported by the database module."%func)

#
# Builders
#
    def where(self, where):
        return self.connection.parser._parseWhere(where)
    
    def order(self, order):
        return self.connection.parser._parseOrder(order)
        
    def column(self, **params):
        values = {
            'name':None,
            'type':None,
            'required':0,
            'unique':0,
            'primaryKey':0,
            'foreignKey':None,
            'default':None,
        }
        for key in params.keys():
            values[key.lower()] = params[key]
        if values['name'] == None:
            raise InterfaceError("Parmeter 'name' not specified correctly for the column")
        if values['type'] == None:
            raise InterfaceError("Parmeter 'name' not specified correctly for the column")
        if values['primaryKey'] and values['default'] <> None:
            raise InterfaceError("A PRIMARY KEY column cannot also have a default value")
        if values['primaryKey'] and values['foreignKey'] <> None:
            raise InterfaceError("A PRIMARY KEY column cannot be a FOREIGN KEY value")
        if values['default'] and values['foreignKey'] <> None:
            raise InterfaceError("A FOREIGN KEY column cannot also have a default value")
        for i in ['required', 'unique', 'primaryKey']:
            if values[i] not in [0,1,True,False]:
                raise DataError("%s can be True or False, not %s"%([i],repr(values[i])))
        if values['type'].capitalize() not in ['Date','Datetime','Time','Float','Long','String','Bool','Text','Integer']:
            raise DataError("%s is not a recognised type"%(values['type'].capitalize()))
        # XXX Type checking of default done later.
        # XXX Extra fields error
        # XXX Check foreign key details.
        return values