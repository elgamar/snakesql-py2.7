##############################################################################
#
# Test 1
#

CREATE TABLE test( columnDate Date, keyString String Primary Key, columnString String, columnText Text, requiredText Text required, columnBool Bool, columnInteger Integer, uniqueInteger Integer unique, columnLong Long, columnFloat Float, columnDateTime DateTime, columnTime Time)
insert into test ( columnDate,  keyString, columnString, columnText, requiredText, columnBool, columnInteger, uniqueInteger, columnLong, columnFloat,columnDateTime, columnTime) VALUES ('2004-12-12', 'str''''ing1', 'string3', 'string4', 'string2', FaLsE, 1, 2, 999999999999999999, 1.2, '2004-12-12 12:12:12', '01:12:12')
insert into test (keyString) VALUES ('str''''ing2')
insert into test (uniqueInteger) VALUES (2)
insert into test (keyString, uniqueInteger) VALUES ('string2', 2)
insert into test (keyString, uniqueInteger, requiredText) VALUES ('string2', 2, NULL)
insert into test (keyString, uniqueInteger, requiredText) VALUES ('string2', 2, 'Text')
insert into test (keyString, uniqueInteger, requiredText) VALUES ('string2', 3, 'Text')
select * from test
UPDATE test SET uniqueInteger=2 WHERE keyString <> NULL
UPDATE test SET keyString='str''''ing2' WHERE keyString <> NULL
UPDATE test SET uniqueInteger=3 WHERE uniqueInteger = 2
UPDATE test SET requiredText='newtext' WHERE uniqueInteger = 2
select columnDate, keyString, columnDateTime, columnString, columnText, requiredText, columnBool, columnInteger, uniqueInteger, columnLong, columnFloat, columnTime from test
delete from test where keyString='string2'
select * from test
UPDATE test SET columnDate=Null, columnLong=Null ,columnString=Null ,columnText =    NUll,  columnBool  =  NULL,columnInteger =null ,columnFloat= null , columnDateTime= Null , columnTime=nULL
select * from test
drop table test
select * from test


Results:

SnakeSQL Interactive Prompt
Type SQL or "exit" to quit, "help", "copyright" or "license" for information.
>>> CREATE TABLE test( columnDate Date, keyString String Primary Key, columnStri
ng String, columnText Text, requiredText Text required, columnBool Bool, columnI
nteger Integer, uniqueInteger Integer unique, columnLong Long, columnFloat Float
, columnDateTime DateTime, columnTime Time)
Query OK, 0 rows affected (0.03 sec)

>>> insert into test ( columnDate,  keyString, columnString, columnText, require
dText, columnBool, columnInteger, uniqueInteger, columnLong, columnFloat,columnD
ateTime, columnTime) VALUES ('2004-12-12', 'str''''ing1', 'string3', 'string4',
'string2', FaLsE, 1, 2, 999999999999999999, 1.2, '2004-12-12 12:12:12', '01:12:1
2')
Query OK, 1 row affected (0.01 sec)

>>> insert into test (keyString) VALUES ('str''''ing2')
Error: The REQUIRED value 'requiredText' has not been specified.
>>> insert into test (uniqueInteger) VALUES (2)
KeyError: PRIMARY KEY 'keyString' must be specified when inserting into the 'tes
t' table.
>>> insert into test (keyString, uniqueInteger) VALUES ('string2', 2)
Error: The REQUIRED value 'requiredText' has not been specified.
>>> insert into test (keyString, uniqueInteger, requiredText) VALUES ('string2',
 2, NULL)
Error: The REQUIRED value 'requiredText' cannot be NULL.
>>> insert into test (keyString, uniqueInteger, requiredText) VALUES ('string2',
 2, 'Text')
Error: The UNIQUE column 'uniqueInteger' already has a value '2'.
>>> insert into test (keyString, uniqueInteger, requiredText) VALUES ('string2',
 3, 'Text')
Query OK, 1 row affected (0.01 sec)

>>> select * from test
+------------+---------------+--------------+------------+--------------+-------
| columnDate | keyString     | columnString | columnText | requiredText | column
+------------+---------------+--------------+------------+--------------+-------
| 2004-12-12 | "str\'\'ing1" | 'string3'    | 'string4'  | 'string2'    | 0
| NULL       | 'string2'     | NULL         | NULL       | 'Text'       | NULL
+------------+---------------+--------------+------------+--------------+-------
-----+---------------+---------------+--------------------+-------------+-------
Bool | columnInteger | uniqueInteger | columnLong         | columnFloat | column
-----+---------------+---------------+--------------------+-------------+-------
     | 1             | 2             | 999999999999999999 | 1.2         | 2004-1
     | NULL          | 3             | NULL               | NULL        | NULL
-----+---------------+---------------+--------------------+-------------+-------
--------------+------------+
DateTime      | columnTime |
--------------+------------+
2-12 12:12:12 | 01:12:12   |
              | NULL       |
--------------+------------+
2 rows in set (0.01 sec)

>>> UPDATE test SET uniqueInteger=2 WHERE keyString <> NULL
Error: The UNIQUE column 'uniqueInteger' cannot be updated setting 2 values to '
2'.
>>> UPDATE test SET keyString='str''''ing2' WHERE keyString <> NULL
Error: The PRIMARY KEY column 'keyString' cannot be updated setting 2 values to
"str''ing2".
>>> UPDATE test SET uniqueInteger=3 WHERE uniqueInteger = 2
Error: The UNIQUE column 'uniqueInteger' already has a value '3'.
>>> UPDATE test SET requiredText='newtext' WHERE uniqueInteger = 2
Query OK, 1 row affected (0.01 sec)

>>> select columnDate, keyString, columnDateTime, columnString, columnText, requ
iredText, columnBool, columnInteger, uniqueInteger, columnLong, columnFloat, col
umnTime from test
+------------+---------------+---------------------+--------------+------------+
| columnDate | keyString     | columnDateTime      | columnString | columnText |
+------------+---------------+---------------------+--------------+------------+
| 2004-12-12 | "str\'\'ing1" | 2004-12-12 12:12:12 | 'string3'    | 'string4'  |
| NULL       | 'string2'     | NULL                | NULL         | NULL       |
+------------+---------------+---------------------+--------------+------------+
--------------+------------+---------------+---------------+--------------------
 requiredText | columnBool | columnInteger | uniqueInteger | columnLong
--------------+------------+---------------+---------------+--------------------
 'newtext'    | 0          | 1             | 2             | 999999999999999999
 'Text'       | NULL       | NULL          | 3             | NULL
--------------+------------+---------------+---------------+--------------------
+-------------+------------+
| columnFloat | columnTime |
+-------------+------------+
| 1.2         | 01:12:12   |
| NULL        | NULL       |
+-------------+------------+
2 rows in set (0.01 sec)

>>> delete from test where keyString='string2'
Query OK, 1 row affected (0.01 sec)

>>> select * from test
+------------+---------------+--------------+------------+--------------+-------
| columnDate | keyString     | columnString | columnText | requiredText | column
+------------+---------------+--------------+------------+--------------+-------
| 2004-12-12 | "str\'\'ing1" | 'string3'    | 'string4'  | 'newtext'    | 0
+------------+---------------+--------------+------------+--------------+-------
-----+---------------+---------------+--------------------+-------------+-------
Bool | columnInteger | uniqueInteger | columnLong         | columnFloat | column
-----+---------------+---------------+--------------------+-------------+-------
     | 1             | 2             | 999999999999999999 | 1.2         | 2004-1
-----+---------------+---------------+--------------------+-------------+-------
--------------+------------+
DateTime      | columnTime |
--------------+------------+
2-12 12:12:12 | 01:12:12   |
--------------+------------+
1 row in set (0.01 sec)

>>> UPDATE test SET columnDate=Null, columnString=Null ,columnText =    NUll,  c
olumnBool  =  NULL,columnInteger =null ,columnFloat= null , columnDateTime= Null
 , columnTime=nULL
Query OK, 1 row affected (0.01 sec)

>>> select * from test
+------------+---------------+--------------+------------+--------------+-------
| columnDate | keyString     | columnString | columnText | requiredText | column
+------------+---------------+--------------+------------+--------------+-------
| NULL       | "str\'\'ing1" | NULL         | NULL       | 'newtext'    | NULL
+------------+---------------+--------------+------------+--------------+-------
-----+---------------+---------------+--------------------+-------------+-------
Bool | columnInteger | uniqueInteger | columnLong         | columnFloat | column
-----+---------------+---------------+--------------------+-------------+-------
     | NULL          | 2             | 999999999999999999 | NULL        | NULL
-----+---------------+---------------+--------------------+-------------+-------
---------+------------+
DateTime | columnTime |
---------+------------+
         | NULL       |
---------+------------+
1 row in set (0.01 sec)

>>> drop table test
Query OK, 0 rows affected (0.05 sec)

>>> select * from test
Error: Table 'test' not found.
>>>

##############################################################################
#
# Test 2
#

CREATE TABLE People( LastName String PRIMARY KEY, FirstName String , Number Integer, DateOfBirth Date )
CREATE TABLE Houses( House Integer, Owner String FOREIGN KEY=People)
INSERT INTO People ( LastName, FirstName, Number, DateOfBirth) VALUES ('Smith', 'John', 10, '1980-01-01')
INSERT INTO People ( LastName, FirstName, Number, DateOfBirth) VALUES ('Doe', 'James', 3, '1981-12-25')
INSERT INTO Houses ( House, Owner ) VALUES (1, 'Smith')
INSERT INTO Houses ( House, Owner ) VALUES (2, 'Smith')
INSERT INTO Houses ( House, Owner ) VALUES (3, 'Doe')
select * from People
select * from Houses
DELETE FROM People
SELECT Houses.House, People.FirstName, Houses.Owner FROM People, Houses WHERE People.LastName=Houses.Owner and People.DateOfBirth<'1981-01-01'
DROP table People
DROP table Houses, People


Results:

SnakeSQL Interactive Prompt
Type SQL or "exit" to quit, "help", "copyright" or "license" for information.
>>> CREATE TABLE People( LastName String PRIMARY KEY, FirstName String , Number
Integer, DateOfBirth Date )
Query OK, 0 rows affected (0.01 sec)

>>> CREATE TABLE Houses( House Integer, Owner String FOREIGN KEY=People)
Query OK, 0 rows affected (0.01 sec)

>>> INSERT INTO People ( LastName, FirstName, Number, DateOfBirth) VALUES ('Smit
h', 'John', 10, '1980-01-01')
Query OK, 1 row affected (0.01 sec)

>>> INSERT INTO People ( LastName, FirstName, Number, DateOfBirth) VALUES ('Doe'
, 'James', 3, '1981-12-25')
Query OK, 1 row affected (0.01 sec)

>>> INSERT INTO Houses ( House, Owner ) VALUES (1, 'Smith')
Query OK, 1 row affected (0.03 sec)

>>> INSERT INTO Houses ( House, Owner ) VALUES (2, 'Smith')
Query OK, 1 row affected (0.02 sec)

>>> INSERT INTO Houses ( House, Owner ) VALUES (3, 'Doe')
Query OK, 1 row affected (0.02 sec)

>>> select * from People
+----------+-----------+--------+-------------+
| LastName | FirstName | Number | DateOfBirth |
+----------+-----------+--------+-------------+
| 'Smith'  | 'John'    | 10     | 1980-01-01  |
| 'Doe'    | 'James'   | 3      | 1981-12-25  |
+----------+-----------+--------+-------------+
2 rows in set (0.00 sec)

>>> select * from Houses
+-------+---------+
| House | Owner   |
+-------+---------+
| 1     | 'Smith' |
| 3     | 'Doe'   |
| 2     | 'Smith' |
+-------+---------+
3 rows in set (0.01 sec)

>>> DELETE FROM People
ForeignKeyError: Table 'Houses' contains references to record with PRIMARY KEY '
1' in 'People'
>>> SELECT Houses.House, People.FirstName, Houses.Owner FROM People, Houses WHER
E People.LastName=Houses.Owner and People.DateOfBirth<'1981-01-01'
+--------------+------------------+--------------+
| Houses.House | People.FirstName | Houses.Owner |
+--------------+------------------+--------------+
| 1            | 'John'           | 'Smith'      |
| 2            | 'John'           | 'Smith'      |
+--------------+------------------+--------------+
2 rows in set (0.03 sec)

>>> DROP table People
ForeignKeyError: Cannot drop table 'People' since child table 'Houses' has a for
eign key reference to it
>>> DROP table Houses, People
Query OK, 0 rows affected (0.08 sec)

>>>


##############################################################################
#
# Test 3
#


UPDATE Houses SET Owner='NotSmith' WHERE Owner = 'Smith'
DROP TABLE People
INSERT INTO Houses (Owner) VALUES ('NotSmith')

Type SQL or "exit" to quit, "help", "copyright" or "license" for information.
>>> UPDATE Houses SET Owner='NotSmith' WHERE Owner = 'Smith'
ForeignKeyError: Invalid value for foreign key 'Owner' since table 'People' does
 not have a primary key value 'NotSmith'
>>> DROP TABLE People
ForeignKeyError: Cannot drop table 'People' since child table 'Houses' has a for
eign key reference to it
>>> INSERT INTO Houses (Owner) VALUES ('NotSmith')
ForeignKeyError: Invalid value for foreign key 'Owner' since table 'People' does
 not have a primary key value 'NotSmith'
>>>

