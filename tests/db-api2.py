"""Unit tests for SnakeSQL

Things to check:
- Multiple primary keys
"""

# Imports
import cgitb; cgitb.enable()

import sys; sys.path.append('../')
import SnakeSQL
import datetime, time

sqlValues = ["'str''in''''g2'", 'FaLsE' ,"'string2'", '2', '1.2', "'"+str(datetime.date(2004,12,12))+"'", "'"+str(datetime.datetime(2004,12,12,12,12,12))+"'", "'"+str(datetime.time(1,12,12))+"'"]
values = ["str'in''g2", 0 ,"string2", 2, 1.2, datetime.date(2004,12,12), datetime.datetime(2004,12,12,12,12,12), datetime.time(1,12,12)]
types = ['String','Bool','Text','Integer','Float','Date','DateTime','Time']

# Begin test
def create():
    print "Testing creating all combinations of tables."

    for type in types:
        table = type # Call the table the same as the type
        for name in ['columnName']:
            for required in ['','required']:
                for unique in ['','unique']:
                    for key in ['','primary key']:
                        for default in ['', 'NULL', defaults[types.index(type)]]:
                            if not default:
                                default == ''
                            else:
                                default = " default = "+str(default)
                            # Drop the table if it already exists
                            try:
                                cursor.execute("drop table %s"%table)
                            except SnakeSQL.SQLError, e:
                                pass
                            sql = "create table %s (%s %s %s %s %s%s ) "%(table, name, type, required, unique, key, default )
                            print sql
                            try:
                                cursor.execute(sql)
                            except SnakeSQL.SQLParser.SQLError, e:
                                if str(e)[:8] not in ['REQUIRED', 'PRIMARY ']:
                                    raise
                                print str(e)+'\n'
                            except SnakeSQL.SQLError, e:
                                print str(e)+'\n'
                            except e:
                                print str(e)+'\n'
                            else:
                                print "PASSED"

def insertTest():
    sql = "create table tableTest ("
    for type in types:
        sql+= " column%s %s,"%(type, type)
    sql = sql[:-1]+")"
    if debug: print sql
    cursor.execute(sql)

    sql = "INSERT INTO tableTest (column%s) VALUES (%s)" %(', column'.join(types), ', '.join(sqlValues))
    if debug: print sql
    cursor.execute(sql)
    

    
    sql = "Select column%s from tableTest"%', column'.join(types)
    if debug: print sql
    cursor.execute(sql)
    results1 = cursor.fetchall()
    if debug==2: print results1
        
    sql = "delete from tableTest"
    if debug: print sql
    cursor.execute(sql)

    sql = "INSERT INTO tableTest (column%s) VALUES (?,?,?,?,?,?,?,?)" %(', column'.join(types))
    if debug: print sql
    cursor.execute(sql, values)
    
    sql = "Select column%s from tableTest"%', column'.join(types)
    if debug: print sql
    cursor.execute(sql)
    results2 = cursor.fetchall()
    if debug==2: print results2
        
    if results1 == results2 == (tuple(values),):
        print "PASSED Insert test."
    else:
        print "FAILED Insert test."
        print results2, values

def updateTest():
    sql = "UPDATE tableTest SET "
    for i in range(len(values)):
        sql+= 'column'+types[i] +' = '+sqlValues[i]+', '
    sql = sql[:-2]
    if debug==2: print sql
    cursor.execute(sql)
    
    sql = "Select column%s from tableTest"%', column'.join(types)
    if debug: print sql
    cursor.execute(sql)
    results1 = cursor.fetchall()
    if debug==2: print results1

    sql = "UPDATE tableTest SET "
    for i in range(len(values)):
        sql+= 'column'+types[i] +' = ? , '
    sql = sql[:-2] + "where columnString <> 'hd'"
    if debug: print sql
    cursor.execute(sql, values)
    
    sql = "Select column%s from tableTest"%', column'.join(types)
    if debug: print sql
    cursor.execute(sql)
    results2 = cursor.fetchall()
    
    if debug==2: print results2
        
    cursor.execute("update tableTest SET columnString = ?, columnText = ? WHERE columnString = ? and columnText = ?  ", ("4","4", "str'ing2", "string2"))
    cursor.execute("update tableTest SET columnString = ?, columnText = ? WHERE columnString = '4'     and columnText =  '4'   ", ("str'ing2", "string2"))
    sql = "Select column%s from tableTest"%', column'.join(types)
    if debug: print sql
    cursor.execute(sql)
    results3 = cursor.fetchall()
    
    if results1 == results2 == results3 == (tuple(values),):
        print "PASSED Update test."
    else:
        print "FAILED Update test."
        print results3, values
    
def conversionTest():
    if SnakeSQL.Date(2004,12,12) <> datetime.date(2004,12,12):
        print "Date failed."
    if SnakeSQL.Time(12,12,12) <> datetime.time(12,12,12):
        print "Time failed."
    if SnakeSQL.Timestamp(2004,12,12,12,12,12) <> datetime.datetime(2004,12,12,12,12,12):
        print "Timestamp failed."
    if SnakeSQL.DateFromTicks(time.time()) <> datetime.date.today():
        print "DateFromTicks failed."
    #TODO: define a way to test TimeFromTicks and TimestampFromTicks, because there's no trace of now() in modern Python
    #if SnakeSQL.TimeFromTicks(time.time()) <> datetime.time(12,12,12).now():
    #    print "TimeFromTicks failed."
    #if SnakeSQL.TimestampFromTicks(time.time()) <> datetime.datetime(2004,12,12,12,12,12).now():
    #    print "TimestampFromTicks failed."
    if SnakeSQL.Binary('hello') <> 'hello':
        print "Binary failed."
        
def typesTest():
    if not SnakeSQL.STRING == SnakeSQL._type_codes['TEXT'] and SnakeSQL.STRING == SnakeSQL._type_codes['STRING']:
        print "STRING comparison failed."
    if not SnakeSQL.BINARY == SnakeSQL._type_codes['BINARY']:
        print "BINARY comparison failed."
    if not SnakeSQL.DATE == SnakeSQL._type_codes['DATE']:
        print "DATE comparison failed."
    if not SnakeSQL.TIME == SnakeSQL._type_codes['TIME']:
        print "TIME comparison failed."
    if not SnakeSQL.TIMESTAMP == SnakeSQL._type_codes['DATETIME']:
        print "TIMESTAMP comparison failed."
    if not SnakeSQL.NUMBER == SnakeSQL._type_codes['INTEGER'] and SnakeSQL.NUMBER == SnakeSQL._type_codes['LONG']:
        print "NUMBER comparison failed."
    #ROWID   This object is not equal to any other object.

if __name__ == '__main__':
    
    debug = False # Can be 0, 1, 2
    
    print "Results are not commited. Use connection.commit() to save these tests."
    print "DBM Test"
    print "--------"
    connection = SnakeSQL.connect('testdbm', driver='dbm', autoCreate=True)
    cursor = connection.cursor()
    insertTest()
    updateTest()
    conversionTest()
    typesTest()
    #connection.commit()
    connection.close()
    
    print "\nCSV Test."
    print "--------"
    connection = SnakeSQL.connect('testcsv', driver='csv', autoCreate=True)
    cursor = connection.cursor()
    insertTest()
    updateTest()
    conversionTest()
    typesTest()
    #connection.commit()
    connection.close()
