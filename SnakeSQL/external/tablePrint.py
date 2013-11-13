
# Check Bools are defined
try:
    True
except NameError:
    True = 1
    False = 0

def table(columns, values, width=80, mode=None):

    # Verify Data
    length = len(columns)
    for i in range(len(values)):
        if length <> len(values[i]):
            raise Exception("There are %s columns but row %s of values contains %s value(s)."%(length, i, len(values[i])))
    
    # Format the data if asked
    if mode == 'sql':
        rows=[]
        for value in values:
            row=[]
            for v in value:
                if type(v) == type(''):
                    row.append(repr(v))
                elif v == None:
                    row.append('NULL')
                else:
                    row.append(str(v))
            rows.append(row)
        values = rows
        
    # Put the data in a more managable form
    vals = []
    for i in range(len(columns)):
        vals.append([columns[i],[]])
    for row in values:
        for i in range(len(columns)):
            vals[i][1].append(row[i])
    values = vals
    
    # Get the column widths
    if (width <> None) and (width < 0 or type(width) <> type(1)):
        raise Exception('The output width must be an integer greater than 0.')
    else:
        d = {}
        for p in values:
            d[p[0]] = {'names':p[1],'widths':[], 'max':0}
        for column, v in d.items():
            d[column]['max'] = len(repr(str(column)))-2
            for field in v['names']:
                d[column]['widths'].append(len(repr(str(field)))-2)
                if len(repr(str(field)))-2 > d[column]['max']:
                    d[column]['max'] = len(repr(str(field)))-2

        # Create the output
        output = ''
        length = len(d)
        c = 0
        for column in columns:
            c += 1
            end = ''; first = ''
            if c == 1:
                first = '+'
            if c == length:
                end = '\n'
            output += first+'-'+('-'*d[column]['max'])+'-+'+end
        c = 0
        for column in columns:
            c += 1
            end = ''; first = ''
            if c == 1:
                first = '|'
            if c == length:
                end = '\n'
            output += first+' '+repr(str(column))[1:-1]+(' '*(d[column]['max'] - len(repr(str(column)))+2))+' |'+end
        c = 0
        for column in columns:
            c += 1
            end = ''; first = ''
            if c == 1:
                first = '+'
            if c == length:
                end = '\n'
            output += first+'-'+('-'*d[column]['max'])+'-+'+end
        for value in range(len(d[column]['names'])):
            c = 0
            for column in columns:
                c += 1
                end = ''; first = ''
                if c == 1:
                    first = '|'
                if c == length:
                    end = '\n'
                output += first+' '+repr(str(d[column]['names'][value]))[1:-1]+(' '*(d[column]['max'] - len(repr(str(d[column]['names'][value])))+2))+' |'+end
        c = 0
        for column in columns:
            c += 1
            end = ''; first = ''
            if c == 1:
                first = '+'
            if c == length:
                end = '\n'
            output += first+'-'+('-'*d[column]['max'])+'-+'+end
        if width:
            lines = output.split('\n')
            j = len(lines[0]) # Maximum number of characters in lines
            k = int((j / float(width))+1) # Number of rows
            rows = []
            for j in range(k):
                rows.append([])
            for line in lines:
                for j in range(k):
                    if j == (k-1):
                        rows[j].append(line[(j*width):((j+1)*width)]+'\n')
                    else:
                        rows[j].append(line[(j*width):((j+1)*width)]+'')
            o = ''
            for row in rows:
                o += ''.join(row)
            while o and o[-1] == '\n':
                o = o[:-1]
            return o
        else:
            while output and output[-1] == '\n':
                output = output[:-1]
            return output[:-2]
            