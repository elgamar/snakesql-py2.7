"Useful functions for automating setups."
import shutil, sys, os, os.path
# Set up True and False
try:
    True
except NameError:
    True = (1==1)
    False = (1==0)

def choosePath(inst, directory):
    while not os.path.exists(inst) and not os.path.exists(inst+os.sep+directory):
        if not os.path.exists(inst):
            print "There is no such path '%s'."%inst
        else:
            print "There is already a '%s' directory at the location '%s'. Are the modules already installed?"%(directory, inst+os.sep+directory)
            
        if raw_input('Would you like to install the modules somewhere else? [y/n]: ') == 'y':
            inst = raw_input('Please enter a directory into which to install the modules: ')
        else:
            print "Install aborted."
            raw_input('Press ENTER to exit.')
            sys.exit(1)
    return inst
        
def install(directory, name):
    print "Installing %s"%name
    from distutils import sysconfig
    inst = sysconfig.get_python_lib()
    if raw_input("The default directory for installation is '%s' Accept this location? [y/N]: "%(inst+os.sep)) == 'y':
        inst = choosePath(inst, directory)
    else:
        inst = choosePath(raw_input('Enter install directory: '), directory)
    paths = []
    if os.name == "nt":
        for path in sys.path:
            paths.append(path.lower())
            
        if inst.lower() not in paths and inst.lower()+os.sep not in sys.path:
            print "The installation directory '%s' is not on your sys.path. This means that if the modules were to be installed there you would not be able to import them unless you modified your path with code as follows:"%inst
            print "import sys; sys.path.append('%s')\n"%inst
    else:
        if inst not in sys.path and inst+os.sep not in sys.path:
            print "The installation directory '%s' is not on your sys.path. This means that if the modules were to be installed there you would not be able to import them unless you modified your path with code as follows:"%inst
            print "import sys; sys.path.append('%s')\n"%inst
    
    if raw_input('Continue with installation? [y/N]: ') == 'y':
        print "Installing the modules to '%s'..."%(inst+os.sep+directory)
        shutil.copytree(directory, inst+os.sep+directory)
        print "%s successfully installed."%name
    else:
        print "Install aborted."
    raw_input('Press ENTER to exit.')

def copytree(src, dst, options, symlinks=0):
    if options['binaries']:
        options['binaries'].remove(str(sys.platform+'-'+sys.version[:3].replace('.','_')))
    names = os.listdir(src)
    if os.path.normpath(dst).replace(os.sep,'/') not in options['excludeDirs'] and dst not in options['excludeAllDirs']:
        os.mkdir(dst)
    for name in names:
        srcname = os.path.normpath(os.path.join(src, name)).replace(os.sep,'/')
        dstname = os.path.normpath(os.path.join(dst, name)).replace(os.sep,'/')
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                if srcname not in options['excludeDirs']:
                    if os.path.split(srcname)[1] not in options['excludeAllDirs']:
                        if srcname not in options['binaries']:
                            copytree(srcname, dstname, options, symlinks)
                        else:
                            pass
                    else:
                        pass
                else:
                    pass
            elif srcname in options['excludeFiles']:
                pass
            elif os.path.split(srcname)[1] in options['excludeAllFiles']:
                pass
            else:
                found = False
                for ext in options['excludeExtensions']:
                    if os.path.split(srcname)[1][-len(ext):] == ext:
                        found=True
                if not found:
                    print "Copying %s"%srcname
                    shutil.copy2(srcname, dstname)

        except (IOError, os.error), why:
            print "Can't copy %s to %s: %s" % (`srcname`, `dstname`, str(why))

def bdist(dirName, archiveName, archiveTypes=['zip'], excludeAllDirs=[], excludeDirs=[], excludeAllFiles=[], excludeFiles=[], binaries=[], excludeExtensions=[]):
    excludeDirs.append('build')
    excludeDirs.append('dist')
    import os
    from distutils.errors import DistutilsExecError
    from distutils.spawn import spawn
    from distutils.dir_util import mkpath
    from distutils.archive_util import make_tarball,make_zipfile,ARCHIVE_FORMATS,check_archive_formats, make_archive
    options = {
        'binaries':binaries,
        'excludeAllDirs':excludeAllDirs,
        'excludeDirs':excludeDirs,
        'excludeAllFiles':excludeAllFiles,
        'excludeFiles':excludeFiles,
        'excludeExtensions':excludeExtensions,
    }
    print "Building a new binary distribution..."
    if os.path.exists('build'):
        print "Removing old builds..."
        shutil.rmtree('build')
    print "Copying directories..."
    os.mkdir('build')
    copytree('./','build/'+dirName, options)
    zip_filename = '../dist/'+archiveName+'.zip'
    if not os.path.exists('dist'):
        print "Creating dist directory..."
        os.mkdir('dist')
    if os.path.exists(zip_filename):
        print "Removing old version..."
        os.remove(zip_filename)
    os.chdir('build')
    type2ext = {
        'zip':'.zip',
        'gztar':'.tar.gz',
        'bztar':'.tar.bz2',
        'ztar':'.tar.Z',
        'tar':'.tar',
    }
    print '\n'
    for atype in archiveTypes:
        try:
            make_archive(archiveName, atype, root_dir=None, base_dir=dirName,verbose=0, dry_run=0)
        except:
            print "COMPRESSION FAILED", atype, "archive:", str(sys.exc_info()[1])
        else:
            if os.path.exists(archiveName+type2ext[atype]):
                
                if os.path.exists('../dist/'+archiveName+type2ext[atype]):
                    print "Removing old distribution..."
                    os.remove('../dist/'+archiveName+type2ext[atype])
                os.rename(archiveName+type2ext[atype], '../dist/'+archiveName+type2ext[atype])
                print "%s %s distribution created successfully."%(dirName, atype)
            else:
                print "MOVE FAILED: %s %s."%(dirName, atype)