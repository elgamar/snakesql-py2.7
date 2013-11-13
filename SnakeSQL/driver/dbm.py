

# Set up True and False
try:
    True
except NameError:
    True = (1==1)
    False = (1==0)
    
import os.path, sys
import base
sys.path.append('../external') # For lockdbm
sys.path.append('../') # For errors
import lockdbm
from error import *

class DBMTable(base.BaseTable):
    def _load(self):
        self.file = lockdbm.open(self.filename)
        self.open = True

    def _close(self):
        self.file.close()
        self.open=False

    def commit(self):
        self.file.commit()

    def rollback(self):
        self.file.rollback()
        
class DBMConnection(base.BaseConnection):
    def __init__(self, database, driver, autoCreate, colTypesName):
        self._closed = None
        self.tableExtensions = ['.dir','.dat','.bak']
        base.BaseConnection.__init__(self, database=database, driver=driver, autoCreate=autoCreate, colTypesName=colTypesName)
        self._closed = False

    # Useful methods
    def databaseExists(self):
        "Return True if the database exists, False otherwise."
        if self._closed:
            raise Error('The connection to the database has been closed.')
        if os.path.exists(self.database) and os.path.exists(self.database+os.sep+self.colTypesName+'.dir') and os.path.exists(self.database+os.sep+self.colTypesName+'.dat') and os.path.exists(self.database+os.sep+self.colTypesName+'.bak'):
            return True
        else:
            return False

    def _deleteTableFromDisk(self, table):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        for end in self.tableExtensions:
            #if os.path.exists(self.database+os.sep+table+end):
            os.remove(self.database+os.sep+table+end)

    def _insertRow(self, table, primaryKey, values, types=None):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        if self.tables[table].file.has_key(str(primaryKey)):
            raise Bug('Key %s already exists in table %s'%(repr(str(primaryKey)), repr(table)))
        self.tables[table].file[str(primaryKey)] = str(values)

    def _deleteRow(self, table, primaryKey):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        del self.tables[table].file[primaryKey]

    def _getRow(self, table, primaryKey):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        if not self.tables[table].file.has_key(str(primaryKey)):
            raise Bug('No such key %s exists in table %s'%(repr(str(primaryKey)), repr(table)))
        row = self.tables[table].file[str(primaryKey)]
        return eval(row)
    
    def _updateRow(self, table, oldkey, newkey, values):
        if self._closed:
            raise Error('The connection to the database has been closed.')
        if newkey == None:
            newkey=oldkey
        del self.tables[table].file[oldkey]  # XXX Is this a bug in dumbdbm?
        if self.tables[table].file.has_key(newkey):
            raise Bug("The table %s already has a PRIMARY KEY named %s. This error should have been caught earlier."%(repr(table) ,repr(newkey)))
        self.tables[table].file[newkey] = str(values)
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
    'Table':DBMTable,
    'Column':base.BaseColumn,
    'Connection':DBMConnection,
}