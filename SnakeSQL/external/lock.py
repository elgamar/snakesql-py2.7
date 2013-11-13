"""Cross-platform file locking using directories.
Based on ideas in glock in the ASPN cookbook."""

# Imports
import os, time

# Errors
class TimeOut(Exception):
    pass
class LockError(Exception):
    pass
class TransactionError(Exception):
    pass
    
# Set up True and False
try:
    True
except NameError:
    True = (1==1)
    False = (1==0)

# Locking
class Lock:
    def __init__(self, expire=0, timeout=10, removeLock=False, warn=False, backup=True):
        if timeout < 1 and removeOnFail:
            raise ValueError("Parameter 'timeout' should not be less than 1 if you plan to remove a failed lock or ownership of the lock could be confused.")
        self.expire = expire
        if timeout < int(timeout) + 1:
            self.timeout = timeout
        else:
            self.timeout = int(timeout) + 1
        self.warn = warn
        self.backup = backup
        self.removeLock = removeLock
        self.files = {}
        
    def __del__(self):
        if len(self.files):
            if self.warn:
                print "Closing locks.. some locks remain and will be removed.."
        for lock in self.files.keys():
            if self.warn:
                print "Removing lock on '%s'."%lock
            self.unlock(lock)
            
    def lock(self, filename):
        if self.files.has_key(filename):
            raise LockError('Use relock() to relock an already locked file.')
        for t in range(0, self.timeout+1):
            if self._isLockInPlace(filename):
                # Check to see if lock has expired
                if self.expire:
                    cur = int(time.time())
                    if cur > os.stat(filename+'_lock2')[8]+self.expire and cur > os.stat(filename+'_lock')[8]+self.expire:
                        if self.warn:
                            print "Lock expired.. removing lock and making a new lock."
                        return self._relock(filename, restore=True)
                elif self.warn:
                    if t <> self.timeout:
                        print "Lock already in place.. waiting 1 second."
            else:
                if self.warn:
                    print "Locking file '%s'."%filename
                self._lock(filename)
                return 1
            if t == self.timeout: # Run once more.. just in case.
                time.sleep(0.01)
            else:
                time.sleep(1)
        if self.removeLock:
            if self.warn:
                print 'Forcing lock removal'
            self._relock(filename, restore=True)
        else:
            raise TimeOut('File already locked. Timeout occured.')
    
    def relock(self, filename):
        if not self.isLocked(filename):
            raise LockError('Lock is not ours. Cannot relock.')
        else:
            try:
                self._relock(filename)
                if self.warn:
                    print "Relocked file '%s'."%filename
                return 1
            except:
                raise LockError('reLock() failed.')

    def unlock(self, filename):
        if not self.isLocked(filename):
            return 0
        else:
            try:
                self._unlock(filename)
                if self.warn:
                    print "Unlocked file '%s'."%filename
                return 1
            except:
                return 0

    def isLocked(self, filename):
        if self._isLockInPlace(filename) and self._isLockOurs(filename):
            return 1
        return 0

    def _isLockInPlace(self, filename):
        if os.path.exists(filename+'_lock2') or os.path.exists(filename+'_lock'):
            return True
        return False
        
    def _isLockOurs(self, filename):
        if not self.files.has_key(filename):
            if self.warn:
                print "Nothing known about lock on '%s'."%filename
            return 0
        elif self.files[filename] <> os.stat(filename+'_lock2')[8]:
            if self.warn:
                print "Lock create time for '%s' doesn't match record.. lock is not ours."%filename
            return 0
        return 1
        
    def commit(self, filename):
        if self.backup:
            self.relock(filename)
            self._backup(filename)
        else:
            raise TransactionError('You cannot commit your changes because transactions are not supported.')

    def rollback(self, filename):
        if not self._rollback(filename):
            raise TransactionError('No backup file found')
            
    def _rollback(self, filename):
        if os.path.exists(filename+'_bak'):
            os.remove(filename)
            self._copy(filename+'_bak', filename)
            return 1
        else:
            return 0
            
    def _backup(self, filename):
        self._removeBackup(filename)
        self._copy(filename, filename+'_bak')
        
    def _removeBackup(self, filename):
        if os.path.exists(filename+'_bak'):
            os.remove(filename+'_bak')

    def _lock(self, filename):
        if self.backup:
            self._backup(filename)
        os.mkdir(filename+'_lock2')
        os.mkdir(filename+'_lock')
        self.files[filename] = os.stat(filename+'_lock2')[8]
        
    def _relock(self, filename, restore=False):
        if restore:
            self._rollback(filename)
        os.rmdir(filename+'_lock2')
        os.mkdir(filename+'_lock2')
        os.rmdir(filename+'_lock')
        os.mkdir(filename+'_lock')
        self.files[filename] = os.stat(filename+'_lock2')[8]
        
    def _unlock(self, filename):
        if self.backup:
            self._removeBackup(filename)
        del self.files[filename]
        os.rmdir(filename+'_lock2')
        os.rmdir(filename+'_lock')

    def _copy(self, src, dest):
        s = open(src, 'rb')
        d = open(dest,'wb')
        d.write(s.read())
        d.close()
        s.close()
