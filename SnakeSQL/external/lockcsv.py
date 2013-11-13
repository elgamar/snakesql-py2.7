"""CSV database based with built-in file locks
so that only one person can read or modify the data at once

Note: CSV files with more than 2^31 rows will not work.
Note: Deleting a row changes all the keys
"""

# Imports
import lock, os
from StringParsers import parseCSV, buildCSV

class InvalidKey(Exception):
    pass
class InvalidRow(Exception):
    pass
_open = open

# Set up True and False
try:
    True
except NameError:
    True = (1==1)
    False = (1==0)

# Python 2.1 os.extsep
try:
    extsep = os.extsep
except AttributeError:
    extsep = '.'

# Lock CSV
class CSV:
    def __init__(self, filename, warn, separater, quote,linebreak, whitespace):
        self.filename = filename
        self.separater = separater
        self.quote = quote
        self.linebreak = linebreak
        self.whitespace = whitespace
        if '.' in self.filename:
            raise NameError("Database '%s' should not contain '.' character."%(self.filename))
        self.filename = filename + extsep + 'csv'
        self.locks = lock.Lock(expire=2, timeout=10, warn=warn)
        self.locks.lock(self.filename)
        
    def __getitem__(self, name):
        for file in self.locks.files.keys():
            if not self.locks.isLocked(file):
                raise lock.LockError('Lock no longer valid.')
        else:
            try:
                i = long(name)
            except ValueError:
                raise InvalidKey("Keys should be integers or longs. %s is not a valid key."%repr(name))
            if i<1:
                raise InvalidKey("Keys should be greater than one. %s is not a valid key."%repr(name))
            results = self._load()
            if len(results) >= i:
                return results[i-1]
            else:
                raise InvalidKey("Key out of range. The largest available key is '%s'."%(str(len(results))))

    def __setitem__(self, name, value):
        for file in self.locks.files.keys():
            if not self.locks.isLocked(file):
                raise lock.LockError('Lock no longer valid.')
        else:
            try:
                i = long(name)
            except ValueError:
                raise InvalidKey("Keys should be integers or longs. %s is not a valid key."%repr(name))
            if i<1:
                raise InvalidKey("Keys should be greater than one. %s is not a valid key."%repr(name))
            results = self._load()
            if not (len(results) == 1 and len(results[0]) == 0): # check row lengths
                if len(results[0]) <> len(value):
                    raise InvalidRow("Each row in %s should have %s values, not %s."%(repr(self.locks.files.keys()[0]),len(results[0]),len(value)))
            if len(results) >= i:
                results[i-1] = value
            elif len(results) == i-1:
                results.append(value)
            else:
                raise InvalidKey("Key out of range. The next available key is '%s'."%str(len(results)+1))
            self._save(results)
        
    def __delitem__(self, name):
        for file in self.locks.files.keys():
            if not self.locks.isLocked(file):
                raise lock.LockError('Lock no longer valid.')
        else:
            try:
                i = long(name)
            except ValueError:
                raise InvalidKey("Keys should be integers or longs. %s is not a valid key."%repr(name))
            if i<1:
                raise InvalidKey("Keys should be greater than one. %s is not a valid key."%repr(name))
            results = self._load()
            if i > len(results):
                raise InvalidKey("Key out of range.")
            else:
                results.pop(i-1)
                self._save(results)

    def _load(self):
        fp = _open(self.filename,'rb')
        lines = fp.read()
        fp.close()
        return parseCSV(lines, self.separater, self.quote, self.linebreak, self.whitespace)
            
    def _save(self, lines):
        fp = _open(self.filename,'wb')
        fp.write(buildCSV(lines, self.separater, self.quote, self.linebreak, self.whitespace))
        fp.close()
            
    def keys(self):
        results = self._load()
        if results == [[],]:
            return []
        else:
            keys = []
            for i in range(len(results)):
                keys.append(str(i+1))
            return keys

    def has_key(self, key):
        if key in self.keys():
            return True
        return False

    def commit(self):
        for file in self.locks.files.keys():
            self.locks.commit(file)
            
    def rollback(self):
        for file in self.locks.files.keys():
            self.locks.rollback(file)
            
    def close(self,commit=False):
        if commit:
            self.commit()
        else:
            self.rollback()
        self.locks.__del__()

    def __del__(self):
        self.rollback()
        
def open(file,warn=False, separater=',', quote='"', linebreak='\n', whitespace=' '):
    if not os.path.exists(file+'.csv'):
        fp = _open(file+'.csv','wb')
        fp.close()
    return CSV(file, warn, separater, quote, linebreak, whitespace)

if __name__ == '__main__':
    file = open('test')

    file['1'] = [1,'eight','nine']
    file['2'] = [2,'eight','nine']
    file['3'] = [3,'eight','']
    print file['1']
    print file['2']
    print file['3']
    del file['2']
    print file['1']
    print file['2']
    file.commit()