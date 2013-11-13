#!/usr/bin/env python

"""Useage: setup.py [option]

Options
 install   Install the modules
 bdist     Create a binary distribution"""

if __name__ == '__main__':
    import sys
    from SnakeSQL.external.distTools import install, bdist
    if not len(sys.argv)>1 or  sys.argv[1] == 'install':
        install(directory='SnakeSQL', name='SnakeSQL')
    elif sys.argv[1] == 'bdist':
        import SnakeSQL
        version = '%s.%s.%s-%s'%SnakeSQL.__version__[:4]
        bdist(
            archiveName = 'snakesql-'+version,
            dirName = 'SnakeSQL',
            archiveTypes = ['zip','gztar','bztar'],#,'ztar','tar'],
            excludeExtensions = ['.pyc','.csv','.dat','.pl'],
            excludeAllDirs = ['CVS'],
            excludeDirs=['doc/src/icons', 'scripts/test', 'tests/test', 'tests/testdbm', 'tests/testcsv'],
            excludeFiles=['doc/src/README.txt'],
        )
        