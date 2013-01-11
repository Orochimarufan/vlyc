#!/usr/bin/python32
#freeze.py
#cx_Freeze setup.py

print("Loading Build System...")
from cx_Freeze import setup, Executable
import sys, os.path, re
from subprocess import Popen, PIPE, call

#release_tarball = ("install" in sys.argv)

#--------------------------------------------------
# Build System
#--------------------------------------------------
print("Analyzing System Configuration...",end=" "*8)
if sys.platform=="win32":
    if "--win32-console" in sys.argv:
        base=None
        inits=None
        sys.argv.remove("--win32-console")
    else:
        base='Win32GUI'
        if "--win32-gui-log" in sys.argv:
            inits='Win32GUI_Log3'
            sys.argv.remove("--win32-gui-log")
        else:
            inits='Win32GUI3' #Custom Initscript
    ext=".exe"
    # installers dont support this
    #release_tarball=True
else:
    base=None
    inits=None
    ext=""

print(sys.platform.upper())

#--------------------------------------------------
# Version
#--------------------------------------------------
print("Determining Version Number...",end=" "*12)

import vlyc

pipe = Popen(["git","rev-list","--all"],stdout=PIPE)
pipe.wait()
rev = len(pipe.stdout.read().decode("utf8").strip().split("\n"))

clean = call(["git","diff-files","--quiet"])==0 and \
        call(["git","diff-index","--quiet","HEAD"])==0

if sys.platform=="win32":
    if clean:
        version = "{1}.{2}.{3}.{0}".format(rev, *vlyc.version_info)
    else:
        #XXX: something to indicate unclean builds
        version = "{1}.{2}.{3}.{0}".format(rev, *vlyc.version_info)
else:
    pipe = Popen(["git","rev-list","HEAD","-n1","--abbrev-commit"],stdout=PIPE)
    pipe.wait()
    git = pipe.stdout.read().decode("utf8").strip()
    version = "{2}.{3}.{4}-{0}git{1}".format(rev, git, *vlyc.version_info)
    if not clean:
        version+="+"

print(version)
with open("VERSION","w") as v:
    v.write(version)

#--------------------------------------------------
# Options
#--------------------------------------------------
print("Setting Build Options")

vlyc = Executable(
    script = "vlyc2.py",
    initScript = inits,
    base = base,
    targetName = "vlyc"+ext,
    )

execs   = [vlyc]
include = ["re", "io", "PyQt4.QtCore", "PyQt4.QtGui"]
exclude = ["tkinter", "Tkinter"]
package = ["libyo.compat.features"]
files   = ["VERSION"]

try:
    import lxml.html
except ImportError:
    include.append("libyo.compat.feature.htmlparser")
else:
    package.append("lxml.html")
    include.append("lxml._elementpath")
    include.append("gzip")
    include.append("inspect")

if sys.hexversion<0x3000000:
    package.append("libyo.compat.python2")

options = {"build_exe": {
            "includes": include,
            "excludes": exclude,
            "packages": package,
            "path": [],
            "optimize": 2,
            "bin_includes": [],
            "append_script_to_exe": True,
            "include_files": files,
            "create_shared_zip": False,
            }
        }

#if not release_tarball:
#    options["install"]={"install_exe":""}

#--------------------------------------------------
# Run Build
#--------------------------------------------------
if "--x" in sys.argv:
    import pprint
    pprint.pprint(options)
    sys.exit()

print("Building...")
setup(
    version = version,
    description = "Youtube Toolchain",
    author = "Orochimarufan",
    name = "YoutubeTools",
    options = options,
    executables = execs,
    )

