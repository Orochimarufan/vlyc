#!/usr/bin/env python
'''
Created on 01.02.2012

@author: hinata
'''

from __future__ import absolute_import,print_function,unicode_literals;

from libyo import LIBYO_VERSION, compat;
from libyo.youtube.resolve import profiles, resolve3;
from libyo.youtube.url import getIdFromUrl;
from libyo.youtube.exception import YouTubeException, YouTubeResolveError;
from libyo.util.choice import cichoice, qchoice, switchchoice;
from libyo.util.util import listreplace_s as lreplace;
from libyo.util.pretty import fillA, fillP;
from libyo.xspf.XspfObject import XspfObject;
from libyo.argparse import ArgumentParser, RawTextHelpFormatter, LibyoArgumentParser, ArgumentParserExit;

import tempfile;
import shlex;
import os;
import subprocess;
import copy;
import platform;
import string;

try:
    import readline;
except ImportError:
    HAS_READLINE=False
else:
    HAS_READLINE=True

valid_filename="-_.{ascii_letters}{digits}".format(**string.__dict__);
input = compat.getModule("util").input; #@ReservedAssignment

__VERSION__=(1,99,5,"");
__LIBYO_R__=(0,9,9,"x");

tofilename = lambda s: "".join(c for c in s.replace(" ","_") if c in valid_filename);
firstkey = lambda i: next(iter(i))

WINSX = platform.system()=="Windows";

def welcome():
    print("AntiFlashPlayer for YouTube v{1}.{2}.{3}{4} (libYo v{0})".format(LIBYO_VERSION,*__VERSION__));
    print("(c) 2011-2012 by Orochimarufan");
    from libyo.version import Version
    Version.LibyoVersion.fancyRequireVersion(__LIBYO_R__)
    Version.PythonVersion.fancyRequireVersion(2,6)
    if not Version.PythonVersion.minVersion(3,2):
        print("WARNING: Running on Python < 3.2 is not fully tested!")
    print();

def main_argv(argv):
    return main(len(argv),argv)

def main(ARGC,ARGV):
    welcome()
    parser = ArgumentParser(prog=ARGV[0],formatter_class=RawTextHelpFormatter,
                            description="Playback YouTube Videos without flashplayer");
    parser.add_argument("id", metavar="VideoID", type=str, help="The YouTube Video ID");
    parser.add_argument("-u","--url", dest="extract_url", action="store_true", default=False, help="VideoID is a URL; Extract the ID from it.");
    parser.add_argument("-q","--quality", metavar="Q", dest="quality", action="store", choices=qchoice.new(1080,720,480,360,240), default="480", help="Quality (Will automatically lower Quality if not avaiable!) [Default: %(default)sp]");
    parser.add_argument("-a","--avc", metavar="PRF", dest="avc", action="store", choices=cichoice(profiles.profiles.keys()), default=firstkey(profiles.profiles), help="What Profile to use [Default: %(default)s]\nUse '%(prog)s -i profiles' to show avaliable choices");
    parser.add_argument("-f","--force",dest="force",action="store_true",default=False,help="Force Quality Level (don't jump down)");
    parser.add_argument("-y","--fmt",dest="fmt",metavar="FMT",action="store",type=int,choices=profiles.descriptions.keys(),help="Specify FMT Level. (For Advanced Users)\nUse '%(prog)s -i fmt' to show known Values");
    parser.add_argument("-c","--cmd", metavar="CMD", dest="command", default="vlc %u vlc://quit", action="store", help="Media PLayer Command. use \x25\x25u for url"); #use %% to get around the usage of % formatting in argparse
    parser.add_argument("-n","--not-quiet",dest="quiet",action="store_false",default=True,help="Show Media Player Output");
    parser.add_argument("-x","--xspf",dest="xspf",action="store_true",default=False,help="Don't Play the URL directly, but create a XSPF Playlist and play that. (With Title Information etc.)");
    parser.add_argument("-i","--internal",dest="int",action="store_true",default=False,help="Treat VideoID as AFP internal command\nUse '%(prog)s -i help' for more Informations.");
    parser.add_argument("-v","--verbose",dest="verbose",action="store_true",default=False,help="Output more Details");
    #parser.add_argument("-s","--shell",dest="shell",action="store_true",default=False,help="Run internal Shell");
    args    = parser.parse_args(ARGV[1:]);
    args.id = args.id.lstrip("\\");
    args.prog = parser.prog;
    
    if args.int:
        return internal_cmd(args);
    #elif args.shell:
    #    return afp_shell(args);
    else:
        return process(args);

def internal_cmd(args):
    if args.id.lower() in ("fmt","fmtcodes","fmtvalues"):
        print("Known FMT Values are:");
        for c,d in profiles.descriptions.items():
            print("FMT {}. Corresponds to: {}".format(fillP(c,3),d));
    elif args.id.lower() in ("help","h"):
        print(
                """Usage: {0} -i [command]
                \tAll non-Playing Commands are considered Internal
                Commands:
                \thelp     : show this help message"
                \tfmt      : show known fmt values"
                \tprofiles : show available Profiles
                \tshell    : open a shell that continuously accepts urls""".format(args.prog));
    elif args.id.lower() in ("profiles",):
        print("Available Profiles are:");
        i=max((len(i) for i in profiles.profiles.keys()))
        j=max((len(k) for z,k in profiles.profiles.values()))
        k=" (Default)"
        print("{0} : {1} [{2}]".format(fillA("<Name>",i),fillA("<Description>",j),"<Avaiable FMTs>"))
        for n,(f,d) in profiles.profiles.items():
            print("{0} : {1} [{2}]{3}".format(fillA(n,i),fillA(d,j),",".join([str(x) for x in f.keys()]),k))
            k=""
    elif args.id.lower() in ("shell",):
        return afp_shell(args);
    else:
        print("Unknown internal Command.\nUse '{0} -i help' for more Informations.".format(args.prog))
        return 1
    return 0

def process(args):
    if args.extract_url:
        args.url=args.id;
        try:
            args.id=getIdFromUrl(args.url);
        except AttributeError:
            print("ERROR: invalid URL")
            return
    fmt_map = profiles.profiles[cichoice.unify(args.avc)][0];
    if args.fmt is None and not args.force:
        fmt_request   = [fmt_map[i] for i in (1080,720,480,360,240) if i in fmt_map and i<=qchoice.unify(args.quality)];
    elif args.fmt is not None:
        fmt_request   = [args.fmt];
    elif args.force:
        fmt_request   = [fmt_map[qchoice.unify(args.quality)]];
    
    print("Receiving Video with ID '{0}'".format(args.id));
    video_info = resolve3(args.id);
    if not video_info:
        print("ERROR: Could not find Video (Maybe your Internet connection is down?)");
        return 1;
    
    print("Found Video: \"{0}\"".format(video_info.title));
    print("Searching for a video url: {0}p ({1})".format(qchoice.unify(args.quality),args.avc));
    if (args.verbose):
        print("Requested FMT: [{0}]".format(",".join(str(k) for k in fmt_request)));
        print("Available FMT: [{0}]".format(",".join(str(k) for k in video_info.urlmap.keys())));
    for fmt in fmt_request:
        if fmt in video_info.urlmap:
            url = video_info.fmt_url(fmt);
            break;
    else:
        print("ERROR: Could not find a video url matching your request. maybe try another profile?");
        return 1;
    if args.verbose:
        print("Found FMT: {0} ({1})".format(fmt,profiles.descriptions[fmt]));
    else:
        print("Found a Video URL: {0}".format(profiles.descriptions[fmt]));
    
    if args.xspf:
        xspf = XspfObject.new(video_info.title);
        track = xspf.newTrack(video_info.title,video_info.uploader,url);
        track.setAnnotation(video_info.description);
        track.setImage("http://s.ytimg.com/vi/{0}/default.jpg".format(video_info.video_id));
        track.setInfo("http://www.youtube.com/watch?v={0}".format(video_info.video_id));
        xspf.addTrack(track);
        if not WINSX:
            temp = tempfile.NamedTemporaryFile(suffix=".xspf",prefix="afp_");
        else:
            temp = tempfile.NamedTemporaryFile(suffix=".xspf",prefix="afp-temp_",delete=False);
        xspf.toFile_c14n(temp.file);
        fn=temp.name;
        if args.verbose:
            print("XSPF Filename: "+fn)
        if not WINSX:
            temp.file.flush();
        else:
            temp.close()
    else:
        fn=url;
    argv = shlex.split(args.command);
    for pair in [("%u",fn),("%n",video_info.title),("%a",video_info.uploader),("%e",profiles.file_extensions[fmt]),("\0",""),("%f","{0}.{1}".format(tofilename(video_info.title),profiles.file_extensions[fmt]))]:
        argv = lreplace(argv,*pair);
    if args.quiet:
        out_fp=open(os.devnull,"w");
    else:
        print("calling '{0}'".format(" ".join(argv)));
        out_fp=None;
        print();
    subprocess.call(argv,stdout=out_fp,stderr=out_fp);
    if args.xspf:
        if not WINSX:
            temp.close();
        else:
            os.remove(temp.name);
    return 0;

def afp_shell(args):
    my_args = copy.copy(args);
    running = True;
    parser = LibyoArgumentParser(prog="AFP Shell",may_exit=False,autoprint_usage=False,error_handle=sys.stdout);
    parser.add_argument("id",help="VideoID / URL / literals '+exit', '+pass', '+print'", metavar="OPERATION");
    parser.add_argument("-s","--switches",dest="switches",help="Set enabled switches (u,x,f,n,v)",choices=switchchoice(["u","x","f","n","v"]),metavar="SW");
    parser.add_argument("-a","--avc",dest="avc",help="Set Profile",choices=cichoice(profiles.profiles.keys()),metavar="PROFILE");
    parser.add_argument("-q","--quality",dest="quality",help="Set Quality Level",choices=qchoice.new(1080,720,480,360,240));
    parser.add_argument("-c","--cmd",dest="command",help="set command");
    if HAS_READLINE:
        readline.parse_and_bind("\eA: previous-history");
        readline.parse_and_bind("\eB: next-history");
    else:
        print("WARNING: No Readline extension found. Readline functionality will NOT be available. If you're on Windows you might want to consider PyReadline.")
    sw = my_args.switches = ("u" if args.extract_url else "")+("x" if args.xspf else "")+("f" if args.force else"")+("n" if not args.quiet else "")+("v" if args.verbose else "");
    while running:
        line = input("{0}> ".format(args.prog));
        try:
            parser.parse_args(shlex.split(line), my_args);
        except ArgumentParserExit:
            print("""Use "+pass --help" to show available options""");
            continue;
        if sw != my_args.switches:
            my_args.extract_url = "u" in my_args.switches;
            my_args.xspf = "x" in my_args.switches;
            my_args.force = "f" in my_args.switches;
            my_args.quiet = "n" not in my_args.switches;
            my_args.verbose = "v" in my_args.switches;
            sw = my_args.switches;
        if my_args.id =="+pass":
            continue;
        elif my_args.id == "+print":
            print("Switches: [{0}]\nProfile: {1}p {2}\nCommand: {3}".format(my_args.switches,my_args.quality,my_args.avc,my_args.command));
            continue;
        elif my_args.id == "+exit":
            running = False;
            break;
        else:
            try:
                process(my_args);
            except YouTubeException:
                print(sys.exc_info()[1]);
    #end while
    return 0;

if __name__ == '__main__':
    import sys;
    sys.exit(main_argv(sys.argv));