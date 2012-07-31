#!/usr/bin/python32
#freeze.py
#cx_Freeze setup.py

print("Loading Build System...")
from cx_Freeze import setup, Executable
import sys, os.path, re
from subprocess import Popen, PIPE

#release_tarball = ("install" in sys.argv)

#--------------------------------------------------
# Build System
#--------------------------------------------------
print("Analyzing System Configuration...",end=" "*8)
if sys.platform=="win32":
    if "--win32-console" in sys.argv:
        base=None
        inits=None
        sys.argv.remove("--win32-gui-log")
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

from libyo.version import Version #@UnresolvedImport

pipe = Popen(["git","rev-list","--all"],stdout=PIPE)
pipe.wait()
rev = len(pipe.stdout.read().decode("utf8").strip().split("\n"))

if sys.platform=="win32":
    version = Version.LibyoVersion.format("{0}.{1}.{2}{patch_i:02}.{{0}}").format(rev)
else:
    pipe = Popen(["git","rev-list","HEAD","-n1","--abbrev-commit"],stdout=PIPE)
    pipe.wait()
    git = pipe.stdout.read().decode("utf8").strip()
    version = Version.LibyoVersion.format("{0}.{1}.{2}.{patch_i}-{{0}}git{{1}}").format(rev,git)

print(version)
with open("VERSION","w") as v:
    v.write(version)

#--------------------------------------------------
# Executables
#--------------------------------------------------
print("Setting up Executable Configurations...",end=" "*2)
vlyc = Executable(
    script = "vlyc2.py",
    initScript = inits,
    base = base,
    targetName = "vlyc"+ext,
    )
youfeed = Executable(
    script = "youfeed.py",
    initScript = None,
    base = None,
    targetName = "youfeed"+ext,
    )
afp = Executable(
    script = "antiflashplayer.py",
    initScript = None,
    base = None,
    targetName = "afp"+ext,
    )

execs   = [ vlyc, youfeed, afp ]
include = [ ]
exclude = [ "tkinter", "Tkinter" ]
package = [ ]
files   = [ "VERSION" ]

for i in sys.argv:
    if i == "--no-vlyc":
        execs.remove(vlyc)
    elif i == "--no-youfeed":
        execs.remove(youfeed)
    elif i == "--no-afp":
        execs.remove(afp)
    else:
        continue
    sys.argv.remove(i)

print(",".join([i.targetName for i in execs]))

#--------------------------------------------------
# Options
#--------------------------------------------------
print("Setting Build Options...")

def addx(self,i):
    if i not in self:
        self.append(i)

def lxml():
    try: import lxml.html
    except: return False
    addx(package,"lxml.html")
    addx(include,"lxml._elementpath")
    addx(include,"gzip")
    addx(include,"inspect")
    return True

if vlyc in execs:
    addx(include,"re")
    addx(include,"io")
    addx(package,"libyo.compat.features")
    lxml() or addx(include,"libyo.compat.features.htmlparser_fallback")
    addx(package,"PyQt4.QtCore")
    addx(package,"PyQt4.QtGui")
if afp in execs:
    addx(include,"re")
    addx(include,"io")
    lxml() or addx(include,"libyo.compat.features.htmlparser_fallback")
if youfeed in execs:
    addx(include,"re")
    lxml() or addx(include,"libyo.compat.features.htmlparser_fallback")

if sys.hexversion>0x3000000:
    addx(package,"libyo.compat.python3")
else:
    addx(package,"libyo.compat.python2")
    
options = {"build_exe": {
            "includes": include,
            "excludes": exclude,
            "packages": package,
            "path": [],
            "optimize":2,
            "bin_includes":[],
            "append_script_to_exe":True,
            "include_files": files,
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

