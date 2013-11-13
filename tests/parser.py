import sys; sys.path.append('../')

import unittest, SnakeSQL, SQLParserTools

parser = SQLParserTools.Transform()

class BuilderAndParser(unittest.TestCase):
    def setUp(self):
        self.sql = {}
        self.sql['delete'] = "DELETE FROM table WHERE one=11 or two=22 or three='2 3' or four=55 or five=90"
        self.sql['update'] = "UPDATE table SET one='''', two='dfg' WHERE ( ( one='''''' and ( not two='22' ) or ( not two='22' ) ) )"
        self.sql['select'] = "SELECT one, two FROM table1, table2 WHERE ( one='NU ORDER BY LL' ) and table1.ty>=' 2 asd 1 ' ORDER BY column DESC, two"
        self.sql['select2']= "SELECT one, two FROM table WHERE ( one='NU ORDER BY LL' ) and two>=' 2 asd 1 '"
        self.sql['select3']= "SELECT * FROM test WHERE keyString='3'"
        self.sql['insert'] = "INSERT INTO table_name1 (column_name1, column_name2) VALUES ('te,''\nst', ?)"
        self.sql['create'] = "CREATE TABLE table_name1 (columnName1 String REQUIRED UNIQUE PRIMARY KEY, column_name2 Integer DEFAULT=?, column_name3 Integer FOREIGN KEY=table)"
        self.sql['drop']   = "DROP TABLE tableName, table2"
        
    def testBuilderAndParserEqual(self):
        "Parsing and Building an SQL statement produces the same SQL"
        for sql in self.sql.keys():
            self.assertEqual(parser.build(**parser.parse(self.sql[sql])), self.sql[sql])
            

    # Do these later!
    #~ self.assertRaises(TypeError, average, 20, 30, 70)

suite = unittest.makeSuite(BuilderAndParser)
unittest.TextTestRunner(verbosity=2).run(suite).errors

