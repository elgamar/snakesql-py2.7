"""SnakeSQL - http://pythonweb.org/projects/snakesql

Summary:        

    Pure Python SQL database supporting NULLs

Author:         

    James Gardner <james@jimmyg.org>

Documentation:  

    Can be found in the ``doc/html`` directory of the source distribution. 

Licence:        

    Portions of this software written by James Gardner is released 
    under the GPL.

    SnakeSQL - http://www.pythonweb.org/projects/snakesql
    Copyright (C) 2004 James Gardner
    
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
    
Installation:

    python setup.py install
    
    
Optimisations
-------------

* Use keys in the where clause for keys. 
* Do the transaction in the if to save accessing data twice.

XXX Major bug.. eval is used in the if statement and loading from the database.. is this safe?

Known Bugs
----------
Default values aren't converted
Rollback doesn't always do so automatically but is restored on next connection anyway.

Possible issues
---------------
Sortout checking tables exist on disk a bit better
Question about what exactly a unique or required column should mena ie not specified, not NULL?
Is the rollback/commit code really totally stable?? Think it through and write tests.
Can floats really be trusted as keys as their precison may change??
Should where just return the strings and leave the engine to parse them ?? 
"""
__version__ = (0,5,2,'alpha')
__name__ = 'SnakeSQL'

# Check Bools are defined
try:
    True
except NameError:
    True = 1
    False = 0
    
# Imports
import sys, os.path

# Set up paths
path = os.path.join(__path__[0],'external')
if path not in sys.path:
    sys.path.insert(0,path)
path = os.path.join(__path__[0])
if path not in sys.path:
    sys.path.insert(0,path)
if sys.version_info < (2,3):
    path = os.path.join(__path__[0],'external','compat','2_3')
    if path not in sys.path:
        sys.path.insert(0,path)
del path

# Internal Imports
import lockdbm
from error import *

# Might be useful
def tableDump(file):
    import lockdbm
    dump = ''
    dbm = lockdbm.open(file)
    for key in dbm.keys():
        dump += "%10s  %s\n"%(key, dbm[key])
    dbm.close()
    return dump

def connect(database, driver='dbm', autoCreate=False):
    """Constructor for creating a connection to the database.
    Returns a Connection Object. It takes a number of
    parameters which are database dependent."""
    colTypesName='ColTypes' # XXX Should make this choosable eventually.
    if driver == 'dbm':
        import driver.dbm
        return driver.dbm.driver['Connection'](database=database, driver=driver.dbm.driver, autoCreate=autoCreate, colTypesName=colTypesName)
    elif driver == 'csv':
        import driver.csv
        return driver.csv.driver['Connection'](database=database, driver=driver.csv.driver, autoCreate=autoCreate, colTypesName=colTypesName)
    else:
        raise DatabaseError("Only 'dbm' and 'csv' databases are currently supported. Not %s."%repr(driver))
        
        
# DB-API 2.0 Compliance
import datetime, time

apilevel = '2.0'
threadsafety = 0 # Unsure of this so "Threads may not share the module." seems safest.
paramstyle='qmark' # Question mark style, e.g. '...WHERE name=?'
_type_codes = { # For converting names to codes for the .description attribute
    'BOOL':1,
    'INTEGER':2,
    'LONG':3,
    'FLOAT':4,
    'STRING':5,
    'TEXT':6,
    'BINARY':7, # XXX
    'DATE':8,
    'DATETIME':9,
    'TIME':10,
}

def Date(year,month,day):
    "This function constructs an object holding a date value."
    return datetime.date(year, month, day)

def Time(hour,minute,second):
    "This function constructs an object holding a time value."
    return datetime.time(hour,minute,second)
    
def Timestamp(year,month,day,hour,minute,second):
    "This function constructs an object holding a time stamp value."
    return datetime.datetime(year, month, day, hour, minute, second)

def DateFromTicks(ticks):
    """This function constructs an object holding a date value
    from the given ticks value (number of seconds since the
    epoch; see the documentation of the standard Python time
    module for details)."""
    t = time.localtime(ticks) 
    return datetime.date(t[0],t[1],t[2])

def TimeFromTicks(ticks):
    """This function constructs an object holding a time value
    from the given ticks value (number of seconds since the
    epoch; see the documentation of the standard Python time
    module for details)."""
    t = time.localtime(ticks) 
    return datetime.time(t[3],t[4],t[5])
    
def TimestampFromTicks(ticks):
    """This function constructs an object holding a time stamp
    value from the given ticks value (number of seconds since
    the epoch; see the documentation of the standard Python
    time module for details)."""
    t = time.localtime(ticks) 
    return datetime.datetime(t[0],t[1],t[2],t[3],t[4],t[5])

def Binary(string): # XXX Really not sure about this one!
    """This function constructs an object capable of holding a
    binary (long) string value."""
    return string

# DB-API Compliant Type objects
# Note I am not implementing any conversion for these types, this 
# is purely so that you can use 'coltype == STRING' comparisons as 
# specified in the DB-API.

class _Type:
    def __init__(self,*values):
        self.values = values
    def __cmp__(self,other):
        if other in self.values:
            return 0
        if other < self.values:
            return 1
        else:
            return -1

STRING      = _Type(_type_codes['TEXT'], _type_codes['STRING'])
BINARY      = _Type(_type_codes['BINARY'])
NUMBER      = _Type(_type_codes['INTEGER'], _type_codes['LONG'])
DATE        = _Type(_type_codes['DATE'])
TIME        = _Type(_type_codes['TIME'])
TIMESTAMP   = _Type(_type_codes['DATETIME'])
RAW = BINARY
ROWID       = _Type() # This object is not equal to any other object.


