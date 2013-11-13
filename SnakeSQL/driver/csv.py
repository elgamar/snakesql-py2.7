

# Set up True and False
try:
    True
except NameError:
    True = (1==1)
    False = (1==0)
    

import os.path, sys
import base, dbm
import lockcsv
from error import *

class CSVTable(dbm.DBMTable):
    def _load(self):
        self.file = lockcsv.open(self.filename)
        self.open = True

        
class CSVConnection(base.BaseConnection):
    def __init__(self, database, driver, autoCreate, colTypesName):
        self._closed = None
        self.tableExtensions = ['.csv']
        base.BaseConnection.__init__(self, database=database, driver=driver, autoCreate=autoCreate, colTypesName=colTypesName)
        self._closed = False

                    
    #~ def _loadTable(self, table):
        #~ if self._closed:
            #~ raise Error('The connection to the database has been closed.')
        #~ self.tableFiles[table] = lockcsv.open(self.database+os.sep+table)

    #~ def _closeTable(self, table):
        #~ if self._closed:
            #~ raise Error('The connection to the database has been closed.')
        #~ self.tableFiles[table].close()

    # Useful methods
    def databaseExists(self):
        "Return True if the database exists, False otherwise."
        if self._closed:
            raise Error('The connection to the database has been closed.')
        if not os.path.exists(self.database):
            return False
        for ext in self.tableExtensions:
            if not os.path.exists(self.database+os.sep+self.colTypesName+ext):
                return False
        return True

    def _deleteTableFromDisk(self, table):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        for end in self.tableExtensions:
            #if os.path.exists(self.database+os.sep+table+end):
            os.remove(self.database+os.sep+table+end)

    def _insertRow(self, table, primaryKey, values, types=None):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        v = []
        for value in range(len(values)):
            v.append(repr(values[value]))
            #~ else:
                #~ primaryKey = None
                #~ for col in self.tables[table].columns:
                    #~ if col.position == value:
                        #~ primaryKey = col.name
                #~ if not primaryKey:
                    #~ raise ConversionError("No column definition found for value %s. Too many values specified."%repr(value))
                #~ v.append(repr(self.typeToInternal(self.tableStructure[table].get(primaryKey).type, values[value])))
        self.tables[table].file[str(len(self.tables[table].file.keys())+1)] = v

    def _deleteRow(self, table, primaryKey):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        del self.tables[table].file[primaryKey]

    def _getRow(self, table, primaryKey):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        r = []
        row = self.tables[table].file[primaryKey]
        for item in row:
            r.append(eval(item))
        return r
    
    def _updateRow(self, table, oldkey, newkey, values):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        #if newkey == None:
            #newkey=oldkey
        #del self.tables[table].file[oldkey]  # XXX Is this a bug in dumbdbm?
        #if self.tables[table].file.has_key(newkey):
        #    raise Bug("The table %s already has a PRIMARY KEY named '%s'. This error should have been caught earlier."%(table,newkey))
        v = []
        for value in range(len(values)):
            v.append(repr(values[value]))
        self.tables[table].file[oldkey] = v
        return values

driver = {
    'converters' : {
        'Unknown':  base.BaseUnknownConverter(),
        'String':   base.BaseStringConverter(),
        'Text':     base.BaseTextConverter(),
        'Binary':   base.BaseBinaryConverter(),
        'Bool':     base.BaseBoolConverter(),
        'Integer':  base.BaseIntegerConverter(),
        'Long':     base.BaseLongConverter(),
        'Float':    base.BaseFloatConverter(),
        'Date':     base.BaseDateConverter(),
        'Datetime': base.BaseDatetimeConverter(), # Decision already made.
        'Time':     base.BaseTimeConverter(),
    },
    'Table':CSVTable,
    'Column':base.BaseColumn,
    'Connection':CSVConnection,
}