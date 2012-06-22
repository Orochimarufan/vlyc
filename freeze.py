#!/usr/bin/python32
#freeze.py
#cx_Freeze setup.py

print("IMPORTING..")
from cx_Freeze import setup, Executable
import sys, os.path, re
from subprocess import Popen, PIPE

print("ANALYZING SYSTEM..")
if sys.platform=="win32":
    base='Win32GUI'
    ext=".exe"
    file_deps=[("share","share")]
else:
    base=None
    ext=""
    file_deps=[]

import libyo.version

ver = libyo.version.Version.LibyoVersion.format("{major}.{minor}.{micro}.0.{patch_i}")


print("SETTING UP..")
vlyc = Executable(
    script = "vlyc2.py",
    initScript = None,
    base = base,
    targetName = "vlyc"+ext,
    #icon = os.path.join("res", "konachan.ico")
    )
youfeed = Executable(
    script = "youfeed.py",
    initScript = None,
    base = None,
    targetName = "youfeed"+ext,
    #icon = os.path.join("res", "konachan.ico")
    )
afp = Executable(
	script = "antiflashplayer.py",
	initScript = None,
	base = None,
	targetName = "afp"+ext,
	#icon = os.path.join("res", "konachan.ico")
	)

print("SETUP()...")
setup(
    version = ver,
    description = "Youtube Toolchain",
    author = "Orochimarufan",
    name = "YoutubeTools",
    options = {"build_exe": {
            "includes": ['re', 'io', "libyo.compat.features.htmlparser_fallback","lxml.html"],
            "excludes": ["libyo.compat.python2"],
            "packages": ["libyo.compat.python3"],
            "path": [],
            "optimize":2,
            "bin_includes":["libvlc.so.5","libvlccore.so.5"],
            "bin_path_includes":["/usr/lib"],
            }
        },
    executables = [afp,youfeed,vlyc]
    )

