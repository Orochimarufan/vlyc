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

execs = [ vlyc, youfeed, afp ]
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
options = {"build_exe": {
            "includes": ['re', 'io', "libyo.compat.features.htmlparser_fallback","lxml.html"],
            "excludes": ["libyo.compat.python2","tkinter","_tkinter","Tkinter"],
            "packages": ["libyo.compat.python3","lxml.html"],
            "path": [],
            "optimize":2,
            "bin_includes":[],
            #"bin_path_includes":["/usr/lib"],
            "append_script_to_exe":True,
            "include_files": ["VERSION"],
            }
        }

#if not release_tarball:
#    options["install"]={"install_exe":""}

#--------------------------------------------------
# Run Build
#--------------------------------------------------
print("Building...")
setup(
    version = version,
    description = "Youtube Toolchain",
    author = "Orochimarufan",
    name = "YoutubeTools",
    options = options,
    executables = execs,
    )

