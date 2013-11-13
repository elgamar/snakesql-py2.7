"""SnakeSQL Interactive Interpreter - James Gardner"""
    
import sys, os.path
sys.path.append('../')
import SnakeSQL
sys.path.append(SnakeSQL.__name__+'/external')
sys.path.append(SnakeSQL.__name__)
import code, traceback, time

# Set up True and False
try:
    True
except NameError:
    True = (1==1)
    False = (1==0)
    
__version__ = SnakeSQL.__version__

class SQLConsole(code.InteractiveConsole):
    "SnakeSQL Interactive Interpreter Class"
    def __init__(self, database, driver, create=False, catchErrors=True, header="SnakeSQL Console", locals=None):
        code.InteractiveConsole.__init__(self, locals, header)
        self.database = database
        self.driver = driver
        self.create = create
        self.catchErrors = catchErrors

    def push(self, line):
        "If the line is a keyword, handle it. Otherwise send the line to the database as SQL."
        if line == 'help':
            print "No help yet available."
        elif line == 'copyright':
            print "Copyright James Gardner 2004, All rights reserved. http://www.jimmyg.org"
        elif line == 'license':
            print "Released under the GNU GPL available to read at http://gnu.org"
        elif line == 'exit':
            sys.exit(0)
        else:
            while line and line[1:] == ' ':
                line = line[1:]
            while line and line[-1:] == ' ':
                line = line[:-1]
            if not line:
                pass
            else:
                try:
                    self.buffer.append(line)
                    more = self.execute(line)
                    source = "\n".join(self.buffer)
                    #more = self.runsource(source, self.filename)
                    #if not more:
                    self.resetbuffer()
                    return more
                except SystemExit:
                    raise
                except:
                    self.showtraceback()

    def execute(self, sql):
        """Connect to the database, execute the SQL, return the result then close the connection
        so other users can access it."""
        connection = SnakeSQL.connect(self.database, driver=self.driver, autoCreate=self.create)
        cursor = connection.cursor()
        start = time.time()
        cursor.execute(sql)
        results = cursor.info['results']
        end = time.time()
        t = "%0.2f"%(end-start)
        if results <> None:
            print cursor.fetchall(format='text')
            if cursor.info['affectedRows'] == 1:
                print str(cursor.info['affectedRows'])+' row in set (%s sec)\n'%t
            else:
                print str(cursor.info['affectedRows'])+' rows in set (%s sec)\n'%t
        else:
            if cursor.info['affectedRows'] == 1:
                print 'Query OK, '+str(cursor.info['affectedRows'])+' row affected (%s sec)\n'%t
            else:
                print 'Query OK, '+str(cursor.info['affectedRows'])+' rows affected (%s sec)\n'%t
        connection.commit()
        connection.close()

    def showtraceback(self):
        "Over-ride default traceback handling."
        if self.catchErrors:
            if sys.exc_info()[0].__name__ in [
                'SQLError', 
                'SQLSyntaxError',
                'SQLKeyError',
                'SQLForeignKeyError',
            ]:
                print '\a'+sys.exc_info()[0].__name__[3:]+': '+str(sys.exc_info()[1])
            else:
                code.InteractiveConsole.showtraceback(self)
                print "\aBUG: The error described above was not expected and should be considered a bug."
        else:
            raise

if __name__ == '__main__':
    from optparse import OptionParser, OptionGroup
    useage = "usage: %prog [options] database"
    parser = OptionParser(usage=useage, version="%%prog %s.%s"%(__version__[0],__version__[1]))
    parser.add_option("-c", "--create",
                      action="store_true", dest="create", default=False,
                      help="create a database if it doesn't already exist")
    parser.add_option("-d", "--driver",
                      action="store", dest="driver", default='dbm',
                      help="storage mechanism can be dbm [defualt] or csv",
                      type="string")
    parser.add_option("-e", "--raise-exceptions",
                      action="store_false", dest="catchError", default=True,
                      help="exit when any exception occurs")
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("incorrect number of arguments, expected just the database name after the options")
    if not options.create and not os.path.exists(args[0]):
        parser.error("database %s does not exist"%(repr(args[0])))
    else:
        # Check the database exists before we hide exceptions.
        try:
            connection = SnakeSQL.connect(args[0], options.driver, options.create)
        except SnakeSQL.DatabaseError,e:
            print "ERROR: %s Use '-c' to create a database.\n"%e
            print "For instructions use:\npython snake.py ? "
            sys.exit(1)
        else:
            connection.close()

        header = """SnakeSQL Interactive Prompt\nType SQL or "exit" to quit, "help", "copyright" or "license" for information."""
        c = SQLConsole(args[0], options.driver, options.create, options.catchError, header=header)
        c.interact(header)
