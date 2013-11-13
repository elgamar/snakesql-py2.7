"""DBM database based on dumbdbm with built-in file locks
so that only one person can read or modify the data at once.


Note:

Python 2.1 doesn't support the mode parameter.
"""

# Imports
import sys, dumbdbm, lock, os

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

# Lock DBM
class Database(dumbdbm._Database):
    def __init__(self, file, mode, warn):
        if '.' in file:
            raise NameError("Database names should not contain '.' characters.")
        self.locks = lock.Lock(expire=2, timeout=10, warn=warn)
        self.locks.lock(file + extsep + 'dir')
        self.locks.lock(file + extsep + 'dat')
        self.locks.lock(file + extsep + 'bak')
        if sys.version_info < (2,2):
            dumbdbm._Database.__init__(self, file)
        else:
            dumbdbm._Database.__init__(self, file, mode)
        
    def __getitem__(self, name):
        for file in self.locks.files.keys():
            if not self.locks.isLocked(file):
                raise lock.LockError('Lock no longer valid.')
        else:
           return dumbdbm._Database.__getitem__(self, name)

    def __setitem__(self, name, value):
        for file in self.locks.files.keys():
            if not self.locks.isLocked(file):
                raise lock.LockError('Lock no longer valid.')
        else:
           return dumbdbm._Database.__setitem__(self, name, value)
           
    def commit(self):
        for file in self.locks.files.keys():
            self.locks.commit(file)
            
    def rollback(self):
        for file in self.locks.files.keys():
            self.locks.rollback(file)
            
    def close(self,commit=False):
        res = dumbdbm._Database.close(self)
        if commit:
            self.commit()
        else:
            self.rollback()
        self.locks.__del__()

    def __del__(self):
        self.rollback()
        
    def sync(self):
        dumbdbm._Database.sync(self)
        
def open(file, flag=None, mode=None, warn=False):
    if not os.path.exists(file+'.dir') or not os.path.exists(file+'.dat') or not os.path.exists(file+'.bak'):
        if sys.version_info < (2,2):
            if mode <> None:
                raise Exception("'mode' parameter not supported in Python < 2.2")
            fp = dumbdbm._Database(file)
            fp.close()
            fp = dumbdbm._open(file+'.bak','w')
            fp.close()
        else:
            if mode == None:
                mode = 0666
            fp = dumbdbm._Database(file, mode)
            fp.close()
            fp = dumbdbm._open(file+'.bak','w')
            fp.close()
    if mode == None:
        mode = 0666
    return Database(file, mode, warn)