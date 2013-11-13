"CSV file reader and writer functions. Fully support Excel and other CSV files."

# Imports
from StringParsers import parseCSV, buildCSV

# CSV
def readCSV(filename, separater=',', quote='"', linebreak='\n'):
    fp = open(filename,'rb')
    lines = fp.read()
    fp.close()
    return parseCSV(lines, separater, quote, linebreak)
    
def writeCSV(filename, lines, separater=',', quote='"', linebreak='\n'):
    fp = open(filename,'wb')
    fp.write(buildCSV(lines, separater, quote, linebreak))
    fp.close()

if __name__ == '__main__':
    csvData = [
        ['Hello','World!', 'D" ",,\n"dsfg,\n,", ,'],
        ['Row 2','World!',"Dod' difficult ' , one to deal,, with"],
    ]
    writeCSV('test.csv', csvData)
    result = readCSV('test.csv')
    if csvData == result:
        print "PASSED: The written and re-read CSV file produces identical objects to the original"
    else:
        print "FAILED: The written and re-read CSV file isn't the same as the original."
        print result