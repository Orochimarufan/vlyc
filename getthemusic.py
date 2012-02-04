#!/usr/bin/python3
import argparse
import os
import json
from libyo import configparser as myconfigparser
import warnings
import subprocess

def makeext(filename,destination,extension):
    bn=".".join(os.path.split(filename)[-1].split(".")[:-1])
    fn=bn+"."+extension
    if destination is None:
        dns=os.path.split(filename)[:-1]
        if dns==("",) or dns==():
            return fn
        else:
            destination=os.path.join(dns)
    return os.path.realpath(os.path.join(destination,fn))

def handle(handler,filename,destination): #make detection reliable
    if args.f: #do not try to detect format
        TYPE = 0x5
    elif filename.split()[-1].split(".")[-1].lower()=="webm":#audio = vorbis
        TYPE = 0x1
    elif filename.split()[-1].split(".")[-1].lower()=="mp4": #audio = aac
        TYPE = 0x2
    elif filename.split()[-1].split(".")[-1].lower()=="flv": #audio = mp3 # not reliable!
        TYPE = 0x3
    else:
        TYPE = 0x5
    if not args.verbose:
        nul=open(os.devnull,"w")
    else:
        nul=None
    return handler(TYPE,filename,destination,None,nul,args.o)

def handle_file_ogg(TYPE,fn_in,fn_out,stdout=None,stderr=None,ov=False):
    ARGV = ["ffmpeg","-i",os.path.realpath(fn_in),"-vn","-f","ogg"]
    if not ov and os.path.exists(fn_out):
        #print("[---] File  EXISTING: "+fn_out)
        return
    if TYPE in (0x1,):
        ARGV += ["-acodec","copy"]
        print("[+++] Writing VORBIS: "+os.path.split(fn_out)[-1]+" ("+os.path.split(fn_in)[-1]+")")
    elif TYPE in (0x2,0x3,0x5):
        ARGV += ["-acodec","libvorbis"]
        print("[+++] Coding  VORBIS: "+os.path.split(fn_out)[-1]+" ("+os.path.split(fn_in)[-1]+")")
    else:
        warnings.warn("Unknown TYPE: "+hex(TYPE))
    ARGV.append(fn_out)
    try:
        subprocess.check_call(ARGV,stdout=stdout,stderr=stderr)
    except subprocess.CalledProcessError as e:
        warnings.warn("Error while running FFMPEG: "+str(e))
    except KeyboardInterrupt:
        if os.path.exists(fn_out):
            os.remove(fn_out)
        raise

def handle_file_aac(TYPE,fn_in,fn_out,stdout=None,stderr=None,ov=False):
    ARGV = ["ffmpeg","-i",os.path.realpath(fn_in),"-vn","-strict","experimental"]
    if TYPE in (0x2,):
        ARGV += ["-acodec","copy"]
    elif TYPE in (0x1,0x3,0x5):
        ARGV += ["-acodec","aac"]
    else:
        warnings.warn("Unknown TYPE: "+hex(TYPE))
    if not ov and os.path.exists(fn_out):
        #print("[---] File already exists: "+fn_out)
        return
    ARGV.append(fn_out)
    print("[+++] Converting [AAC]: "+fn_out)
    try:
        subprocess.check_call(ARGV,stout=stdout,stderr=stderr)
    except subprocess.CalledProcessError as e:
        warnings.warn("Error while running FFMPEG: "+str(e))

def welcome():
    for line in \
            ("YouFeed {} / GetTheMusic".format("2.0-0.9"),) \
            : print(line)

def printinf(DIR,TARG,NAME):
    for line in \
            ("Processing '{}'".format(NAME),
             "Fetching from '{}'".format(DIR),
             "Saving to '{}'".format(TARG)) \
            : print(line)

def main(ARGV):
    welcome()
    parser = argparse.ArgumentParser(ARGV[0],description="Extract Music from YouTube Videos")
    parser.add_argument("-a","--aac",action="store_true",dest="aac",default=False,help="Convert to AAC instead of OGG/VORBIS (not recommended)")
    parser.add_argument("-f","--force",action="store_true",dest="f",default=False,help="force recoding (don't allow format guessing)")
    parser.add_argument("-o","--overwrite",action="store_true",dest="o",default=False,help="Overwrite existing files")
    parser.add_argument("-v","--verbose",action="store_true",dest="verbose",default=False,help="Print FFmpeg output")
    subparsers = parser.add_subparsers()
    parser_dir = subparsers.add_parser("dir",aliases=["folder"])
    parser_dir.add_argument("dir",metavar="DIRECTORY",help="The directory to Read")
    parser_dir.add_argument("-d","--dest",metavar="DIRECTORY",action="store",dest="target",default=os.getcwd(),help="The Directory to Put the audio Files. [Default: .]")
    parser_job = subparsers.add_parser("job")
    parser_job.add_argument("job",metavar="YouFeedJob",help="The YouFeed JobFileName")
    parser_job.add_argument("-d","--dest",metavar="DIRECTORY",action="store",dest="target",default=None,help="The Directory to Put the audio Files. [Default: Music/JobTitle]")
    parser_job.add_argument("-x","--xspf","--playlist",metavar="FILE",action="store",dest="xspf",help="Create a XSPF Playlist of the new Music")
    parser_sin = subparsers.add_parser("sin",aliases=["single","file"])
    parser_sin.add_argument("sin",metavar="VIDEOFILE",help="The File to convert/extract")
    parser_sin.add_argument("-o","--outfile","--output",metavar="MUSICFILE",dest="target",default=None,help="The Output File")
    global args
    args = parser.parse_args(ARGV[1:])
    DIRECTORY = None; NAME = None; TARGET = args.target; JOBTYPE=None
    if "sin" in args:
        FN_IN=args.sin
        FN_OUT=args.target
        FN_EXT="aac" if args.aac else "ogg"
        FN_TYP="AAC" if args.aac else "VORBIS"
        FN_FNC=handle_file_aac if args.aac else handle_file_ogg
        if FN_OUT is None:
            FN_OUT=makeext(FN_IN,None,FN_EXT)
        print("Reading '{}'\nConverting to {}\nWriting '{}'".format(FN_IN,FN_TYP,FN_OUT))
        handle(FN_FNC,FN_IN,FN_OUT)
        return 0
    elif "job" in args:
        jobconfigfile = os.path.join("jobs",args.job+".ini")
        if not os.path.exists(jobconfigfile):
            print("Job '{}' does not exist!".format(args.job))
            return 1
        jobconfig = myconfigparser.RawPcsxConfigParser()
        jobconfig.read(jobconfigfile)
        if jobconfig.get(jobconfig.NOSECT,"type",fallback="").lower()=="list":
            NAME = jobconfig[jobconfig.NOSECT]["name"]
            DIRECTORY = os.path.join("locallists",NAME)
            if TARGET is None: TARGET = os.path.join("music","locallists",NAME)
            JOBTYPE = 0x2
        elif jobconfig.get(jobconfig.NOSECT,"type",fallback="").lower()=="playlist" or jobconfig.has_option(jobconfig.NOSECT,"playlist"):
            jobmetafile = os.path.join("pl",jobconfig[jobconfig.NOSECT]["playlist"]+".plm")
            if not os.path.exists(jobmetafile):
                print("Job '{}' has no Metadata. Please Run YouFeed first!")
                return 1
            with open(jobmetafile) as jobmetadescriptor:
                jobmeta = json.load(jobmetadescriptor)
            jobtruename = jobmeta["meta"]["name"]
            NAME = jobtruename
            DIRECTORY = os.path.join("playlists",jobtruename)
            if TARGET is None: TARGET = os.path.join("music",jobtruename)
            JOBTYPE = 0x1
        elif jobconfig.get(jobconfig.NOSECT,"type",fallback="").lower()=="favorites" or jobconfig.has_option(jobconfig.NOSECT,"favorites"):
            print("Favorites not supportet now.")
            return 1
        elif jobconfig.get(jobconfig.NOSECT,"type",fallback="").lower()=="channel" or jobconfig.has_option(jobconfig.NOSECT,"channel"):
            print("Channels not supportet now.")
            return 1
        else:
            print("Malformed JobConfig!")
            return 1
    elif "dir" in args:
        DIRECTORY = os.path.realpath(args.dir)
        NAME = args.dir
    else:
        print("You need to specify a subcommand!")
        return 1

    printinf(DIRECTORY,TARGET,NAME)

    fx=handle_file_ogg
    if args.aac: fx=handle_file_aac

    if not os.path.exists(TARGET):
        os.makedirs(TARGET)

    ext="aac" if args.aac else "ogg"

    for f in os.listdir(DIRECTORY):
        handle(fx,os.path.join(DIRECTORY,f),makeext(f,TARGET,ext))

    if "job" in args and args.xspf is not None:
        fn=os.path.realpath(args.xspf)
        if JOBTYPE == 0x2:
            print("[!!!] Playlists are not supportet on Local Lists.")
            return 0
        elif JOBTYPE == 0x1:
            meta={"title":jobmeta["meta"]["name"],"url":"http://www.youtube.com/playlist?p="+jobconfig[jobconfig.NOSECT]["playlist"],"author":jobmeta["meta"]["author"]}
            local=jobmeta["local"]
            down=jobmeta["downloads"]
            down=dict([(k,{"path":makeext(v["path"],TARGET,ext)}) for k,v in down.items()])
            with open(fn,"w") as fp:
                pass
    return 0

if __name__=="__main__":
    import sys
    sys.exit(main(sys.argv))
