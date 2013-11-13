"# XXX Connection also neeeds ignoreSQLReservedWords, ignoreDtupleReservedWords, compatibilitySQL, updateWhereValues"

import sys; sys.path.append('../')
import SnakeSQL, datetime

connection = SnakeSQL.connect('test', driver='dbm', autoCreate=True)
cursor = connection.cursor()
sql = cursor.create(
    table = 'test', 
    columns = [
        cursor.column(name='columnDate', type='Date'),
        cursor.column(name='keyString', type='String', key=True),
        cursor.column(name='columnString', type='String'),
        cursor.column(name='columnText', type='Text'),
        cursor.column(name='requiredText', type='Text', required=True),
        cursor.column(name='columnBool', type='Bool'),
        cursor.column(name='columnInteger', type='Integer'),
        cursor.column(name='uniqueInteger', type='Integer', unique=True),
        cursor.column(name='columnLong', type='Long'),
        cursor.column(name='columnFloat', type='Float'),
        cursor.column(name='columnDateTime', type='DateTime'),
        cursor.column(name='columnTime', type='Time'),
    ],
    execute = False
)
cursor.execute(sql, [5])
#print connection.tables['test'].get('columnInteger').default
cursor.insert(
    table = 'test',
    columns = [
        'columnDate', 
        'keyString', 
        'columnString', 
        'columnText', 
        'requiredText', 
        'columnBool', 
        'columnInteger', 
        'uniqueInteger', 
        'columnLong', 
        'columnFloat',
        'columnDateTime', 
        'columnTime',
    ],
    values = [
        datetime.date(2004,12,12), 
        "str''ing1", 
        'string3', 
        'string4', 
        'string2', 
        False, 
        1, 
        2, 
        999999999999999999,
        1.2, 
        datetime.datetime(2004,12,12,12,12,12), 
        datetime.time(1,12,12),
    ]
)
print cursor.insert(table='test', columns='keyString', values=["str''ing2"], execute=False)
print cursor.update(table='test', columns='keyString', values=["str''ing2"], where="keyString > '56'", execute=False)
try:
    cursor.insert(table='test', columns='keyString', values="str''ing2")
except:
    print "Caught: ", sys.exc_info()[1]
else:
    print "FAILED to catch an error"

try:
    cursor.insert(table='test', columns='uniqueInteger', values=2)
except:
    print "Caught: ", sys.exc_info()[1]
else:
    print "FAILED to catch an error"

try:
    cursor.insert(
        table='test', 
        columns=[
            'keyString',
            'uniqueInteger',
        ],
        values=[
            'string2', 
            2,
        ]
    )
except:
    print "Caught: ", sys.exc_info()[1]
else:
    print "FAILED to catch an error"

try:
    cursor.insert(
        table='test', 
        columns=[
            'keyString',
            'uniqueInteger',
        ],
        values=[
            'string2', 
            2,
        ]
    )
except:
    print "Caught: ", sys.exc_info()[1]
else:
    print "FAILED to catch an error"
    
    
try:
    cursor.insert(
        table='test', 
        columns=[
            'keyString',
            'uniqueInteger',
            'requiredText',
        ],
        values=[
            'string2', 
            2,
            None,
        ]
    )
except:
    print "Caught: ", sys.exc_info()[1]
else:
    print "FAILED to catch an error"

try:
    cursor.insert(
        table='test', 
        columns=[
            'keyString',
            'uniqueInteger',
            'requiredText',
        ],
        values=['string2', 2, 'Text']
    )
except:
    print "Caught: ", sys.exc_info()[1]
else:
    print "FAILED to catch an error"

cursor.insert(
    table='test', 
    columns=[
        'keyString',
        'uniqueInteger',
        'requiredText',
    ],
    values=['string2', 3, 'Text']
)

cursor.select(
    tables='test',
    columns='*',
)

try:
    cursor.update(
        table='test', 
        columns='uniqueInteger',
        values=2,
        where="keyString <> NULL", # XXX Not good.
    )
except:
    print "Caught: ", sys.exc_info()[1]
else:
    print "FAILED to catch an error"
    
    

cursor.update(
    table='test', 
    columns='keyString',
    values="str''ing2",
    where="keyString <> NULL", # XXX Not good.
)

try:
    cursor.update(
        table='test', 
        columns='uniqueInteger',
        values=3,
        where="uniqueInteger = 2", # XXX Not good.
    )
except:
    print "Caught: ", sys.exc_info()[1]
else:
    print "FAILED to catch an error"
    
cursor.update(
    table='test', 
    columns='requiredText',
    values='newtext',
    where="uniqueInteger = 2", # XXX Not good.
)

print cursor.select(
    tables='test',
    columns = [
        'columnDate', 
        'keyString', 
        'columnDateTime', 
        'columnString', 
        'columnText', 
        'requiredText', 
        'columnBool', 
        'columnInteger', 
        'uniqueInteger', 
        'columnLong', 
        'columnFloat',
        'columnTime',
    ],
)

cursor.delete(
    table='test', 
    where="keyString='string2'", # XXX Not good.
)

print cursor.select(
    tables='test',
    columns='*',
)

cursor.update(
    table = 'test',
    columns = [
        'columnDate', 
        'columnString', 
        'columnText', 
        'columnBool', 
        'columnInteger', 
        'columnLong', 
        'columnFloat',
        'columnDateTime', 
        'columnTime',
    ],
    values = [
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ]
)

print "TEST,", cursor.select(
    tables='test',
    columns='*',
    where="requiredText='newtext'"
)

cursor.drop(
    tables=['test'],
)

try:    
    print cursor.select(
        tables='test',
        columns='*',
    )
except:
    print "Caught: ", sys.exc_info()[1]
else:
    print "FAILED to catch an error"

import SQLParserTools
sql = "SELECT one, two FROM table WHERE ( one='NU ORDER BY LL' ) and two>=' 2 asd 1 ' ORDER BY column DESC, two"
blocks = SQLParserTools.Parser().parse(sql)
del blocks['function']
blocks['execute'] = False
if cursor.select(**blocks) == sql:
    print "PASSED"
else:
    print "FAILED"

sql = "INSERT INTO table_name1 (column_name1, column_name2) VALUES ('te,''\nst', '546')"
blocks = SQLParserTools.Parser().parse(sql)
del blocks['function']
blocks['execute'] = False
if cursor.insert(**blocks) == sql:
    print "PASSED"
else:
    print "FAILED"
    
sql = "UPDATE table SET one='''', two='dfg'"
blocks = SQLParserTools.Parser().parse(sql)
del blocks['function']
blocks['execute'] = False
if cursor.update(**blocks) == sql:
    print "PASSED"
else:
    print "FAILED"

sql = "CREATE TABLE table_name1 (columnName1 String REQUIRED UNIQUE PRIMARY KEY, column_name2 Integer DEFAULT='4''')"
blocks = SQLParserTools.Parser().parse(sql)
del blocks['function']
blocks['execute'] = False
if cursor.create(**blocks) == sql:
    print "PASSED"
else:
    print "FAILED"
    
sql = "DELETE FROM table WHERE one=11 or two=22 or three='2 3' or four=55 or five=90"
blocks = SQLParserTools.Parser().parse(sql)
del blocks['function']
blocks['execute'] = False
if cursor.delete(**blocks) == sql:
    print "PASSED"
else:
    print "FAILED"
    
sql = "DROP TABLE tableName"
blocks = SQLParserTools.Parser().parse(sql)
del blocks['function']
blocks['execute'] = False
if cursor.drop(**blocks) == sql:
    print "PASSED"
else:
    print "FAILED"
print 'Warning: cursor.update() and cursor.insert() not tested for execute="False" with real values'
connection.commit()




    
    