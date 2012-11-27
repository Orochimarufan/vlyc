#!/usr/bin/python3
from __future__ import unicode_literals,print_function,absolute_import

# Settings
bytecount = 64*4096
_xspf_relpath=True
# Version
version = "2.0.4"
need_libyo = (0,9,13)
# Filenames
allow_spaces    = False
allow_invalid   = False
valid_filename  = "-_.{ascii_letters}{digits}"
invalid_replace = ""
space_replace   = "_"

# Imports
import sys
import logging

import libyo
from libyo.youtube.resolve import resolve3
from libyo.youtube.Playlist import Playlist
from libyo.youtube.url import getIdFromUrl
from libyo.youtube.User import User
from libyo.extern import argparse
from libyo.youtube.resolve.profiles import descriptions as fmtdesc, file_extensions as fmtext, profiles
from libyo.youtube.exception import YouTubeResolveError
from libyo.interface.progress.simple import SimpleProgress2
from libyo.interface.progress.file import SimpleFileProgress
from libyo.urllib.download import download as downloadFile
from libyo.configparser import RawPcsxConfigParser, PcsxConfigParser

import os
import json
import string
import platform

# Platform
if platform.system()=="cli": #IronPython OS Detection
    WINSX = platform.win32_ver()[0]!=""
else:
    WINSX = platform.system()=="Windows"

# Filename Gen
valid_filename = valid_filename.format(**string.__dict__)
_tfn_spaces = (lambda s: s) if allow_spaces \
else (lambda s: s.replace(" ","_"))
_tfn_validc = (lambda c: c) if allow_invalid \
else (lambda c: c if c in valid_filename else invalid_replace)
tofilename = lambda s: "".join([_tfn_validc(c) for c in _tfn_spaces(s)])

def welcome():
    print("YouFeed {1} (libyo {0})".format(libyo.version,version))
    print("(c) 2011-2012 Orochimarufan")
    if need_libyo > libyo.version_info:
        raise SystemError("libyo > {0} required.".format(".".join(map(str,need_libyo))))
    if (2,6) > sys.version_info:
        raise SystemError("python > 2.6 required.")

def main(ARGV):
    welcome()
    parser=argparse.ArgumentParser(prog=ARGV[0],description="A nifty piece of Software that lets you download YouTube Playlists.")
    parser.add_argument("-d","--dummy",action="store_true",dest="dummy",default=False,help="Don't download anything.")
    parser.add_argument("-v","--verbose",action="store_true",dest="verbose",default=False,help="Verbose Output")
    subparsers=parser.add_subparsers(default="all",title="subcommands",description="Use '%(prog)s (command) -h' to get further help. By Default, the 'all' command is run.",dest="command")
    parser_all=subparsers.add_parser("all",description="Do all Jobs defined in the jobs/ directory.")
    parser_all.add_argument("-p","--playlist",action="store_true",dest="pl",default=False,help="Only update Job Playlists.")
    parser_all.add_argument("-pa","--playlist-abs",action="store_false",dest="xspf_rel",default=_xspf_relpath)
    parser_all.set_defaults(max=-1,offset=0)
    parser_job=subparsers.add_parser("job",aliases=["jobs"],description="Do one job defined in the jobs/ directory.")
    parser_job.add_argument("job",metavar="JobFileName",help="The Filename of the job definition file to use.",nargs="+")
    parser_job.add_argument("-n","--max",metavar="N",dest="max",type=int,default=-1,help="Max Number of Videos to download")
    parser_job.add_argument("-o","--offset",metavar="N",dest="offset",type=int,default=-1,help="Skip N Videos")
    parser_job.add_argument("-p","--playlist",action="store_true",dest="pl",default=False,help="Only update Job Playlists.")
    parser_run=subparsers.add_parser("run",description="Do a custom job.")
    parser_run.add_argument("job_type",help="The Job Type. [favorites,playlist]")
    parser_run.add_argument("job_argument",help="[playlist] The YouTube Playlist ID; [favorites] The Youtube User ID")
    parser_run.add_argument("-p","--playlist",metavar="xspf_file",dest="xspf_file",default=False,help="Create a Playlist File")
    parser_run.add_argument("-q","--quality",metavar="QA",dest="quality",default=720,type=int,help="The Quality level (360p -> 360; 720p -> 720)")
    parser_run.add_argument("-n","--max",metavar="N",dest="max",default=-1,type=int,help="Max Number of Videos to download")
    parser_run.add_argument("-o","--offset",metavar="N",dest="offset",default=0,type=int,help="Skip N Videos")
    parser_sin=subparsers.add_parser("sin",aliases=["single"],description="Download a single video")
    parser_sin.add_argument("video_id",help="Video ID/URL",nargs="+")
    parser_sin.add_argument("target_dir",help="Folder to store the Files")
    parser_sin.add_argument("-u",help="Video IDs are Youtube URLs",action="store_true",default=False)
    parser_sin.add_argument("-q",default=720,type=int,help="Quality: progressive height, integer")
    parser_sin.add_argument("-a",help="Profile",default="mixed-avc")
    args=parser.parse_args(ARGV[1:])
    if not os.path.exists("pl"):
        os.makedirs("pl")
    if "command" not in args or args.command=="all":
        return _mode_joblist(args)
    elif args.command in ("job","jobs"):
        paths = []
        for pt in args.job:
            if not os.path.exists(pt):
                path = os.path.join("jobs",pt)
                if not os.path.exists(path):
                    if os.path.exists(path+".ini"):
                        path+=".ini"
                    else:
                        print("[ERROR] Job not Found (Did you put it into jobs/?): "+path)
                        continue
                paths.append(path)
            else:
                paths.append(pt)
        if len(paths)>1 and (args.offset!=0 or args.max!=-1):
            print("[ERROR] --offset and --max are only valid on single-job calls.")
            args.offset=0;args.max=-1
        return _mode_job(args,paths)
    elif args.command=="run":
        return _mode_run(args)
    elif args.command in ("sin","single"):
        return _mode_sin(args)

def _mode_joblist(args):
    joblist=[]
    for i in os.listdir("jobs"):
        if i[-3:]=="ini":
            joblist.append(os.path.join("jobs",i))
    return _mode_job(args,joblist)

def _mode_job(args,joblist):
    for jobfile in joblist:
        job=PcsxConfigParser()
        job.read(jobfile)
        job_name=job.getnosect("name")
        print("[ MAIN] Processing Job \"{0}\"...".format(job_name))
        job_type=job.getnosect("type").lower()

        if not args.pl:
            if job_type in ("pl","playlist"):
                _playlist_job(args,job)
            elif job_type in ("fav","favorites","favourites"):
                _favorites_job(args,job);
            else:
                print("[ JOB ] Unknown Job Type: "+job_type)
                continue

        if job.getnosect("createpl",False):
            _xspf_job(args,job)

    print("[ MAIN] Done. Farewell, may we meet again!")

def _mode_run(args):
    job = RawPcsxConfigParser()
    job.setnosect("name","Explicit Job")
    job.setnosect("type",args.job_type)
    job.setnosect("quality",args.quality)
    if args.job_type in ("pl","playlist"):
        job.setnosect("playlist",args.job_argument)
        _playlist_job(args,job)
    elif args.job_type in ("fav","favorites","favourites"):
        job.setnosect("user",args.job_argument)
        _favorites_job(args,job)
    else:
        print("[ MAIN] Unknown Job Type: "+args.job_type)
        return 1

    if args.xspf_file:
        job.setnosect("createpl",args.xspf_file)
        _xspf_job(args,job)
    print("[ MAIN] Done. Farewell!")

class DummyParser(dict):
    def getnosect(self,k,defa=None):
        return self.get(k,defa)

def _mode_sin(args):
    q = _job_quality(DummyParser({"resolution":str(args.q),"profile":args.a}))
    m = {"items":[],"local":[],"local_id":{},"downloads":{},"local_title":{}}
    if not os.path.exists(args.target_dir):
        os.makedirs(os.path.abspath(args.target_dir))
    for video_id in args.video_id:
        vid = video_id if not args.u else id_from_url(video_id)
        vi  = resolve3(vid)
        v = {"id":vid, "title": vi.title}
        _download(args,m,args.target_dir,q,v)


def _xspf_job(args,job):
    xspf_file       = job.getnosect("createpl")

    if job.getnosect("type").lower() in ("pl","playlist"):
        filename = os.path.abspath(os.path.join("pl",os.path.normpath(job.getnosect("playlist")+".plm")))
        with open(filename) as fp:
            meta = json.load(fp)
        if "url" not in meta["meta"]:
            meta["meta"]["url"]="http://youtube.com/playlist?list=PL"+job.getnosect("playlist")
        if "playlist_id" not in meta["meta"]:
            meta["meta"]["playlist_id"]=job.getnosect("playlist")
        if "title" not in meta["meta"]:
            meta["meta"]["title"]=meta["meta"]["name"]
    elif job.getnosect("type").lower() in ("fav","favorites","favourites"):
        filename=os.path.abspath(os.path.join("pl",os.path.normpath(job.getnosect("user")+".ytfav")))
        with open(filename) as fp:
            meta = json.load(fp)
        if "title" not in meta["meta"]:
            meta["meta"]["title"]=meta["meta"]["name"]
    else:
        print("[ XSPF] Cannot handle Jobtype: "+job.getnosect("type"))
        return 1
    try:
        xspf_file.index(".")
    except ValueError:
        xspf_file   += ".xspf"

    relative = os.path.dirname(xspf_file) if (args.xspf_rel and not xspf_file.startswith("/")) else False

    print("[ JOB ] Creating Local Playlist: '{0}'".format(xspf_file))
    xspf_object     = _create_xspf(meta["meta"],meta["local"],meta["downloads"],relative)

    with open(xspf_file,"w") as fp:
        xspf_object.writexml(fp, "", "", "", encoding="UTF-8")

def _download(args,meta,target,fmt_list,video_item):
    try:
        video_title = video_item["title"]
        video_id    = video_item["id"]
        if video_id == "":
            print("[VIDEO] Found Deleted Video in Playlist. please clean up!")
            return
        print("[VIDEO] Found new Video: \"{0}\" (ID='{1}')".format(video_title,video_id))
        print("[VIDEO] Preparing to Download...",end="\r")
        try:
            url,fmt     = _recursive_resolve(video_id,fmt_list)
        except YouTubeResolveError:
            print("[VIDEO] Video could not be resolved.")
            return
        print("[VIDEO] Downloading with Quality level {0}".format(fmtdesc[fmt]))
    except Exception:
        import traceback
        print("-"*40)
        print("Exception while Resolving Video:")
        if args.verbose:
            traceback.print_exc(limit=None,chain=True)
        else:
            print("".join(traceback.format_exception_only(*sys.exc_info()[:2])),end="")
        print("-"*40)
        return meta
    if not args.dummy:
        video       = resolve3(video_id)
        filename    = tofilename(video.title)+"."+fmtext[fmt]
        path        = target
        fullpath    = os.path.join(path,filename)
        progress = SimpleFileProgress("{position}/{total} {bar} {percent} {speed} ETA: {eta}")
        retry = 0
        while retry<5:
            try:
                downloadFile(url,fullpath,progress,2,bytecount)
            except Exception:
                import traceback
                traceback.print_exception(*sys.exc_info())
                #print("[ERROR] " + "".join(traceback.format_exception_only(*sys.exc_info()[:2])))
                retry+=1
            else:
                break
        else:
            print("[ERROR] Cannot Download. Continuing")
            return meta
        meta["items"].append(video_id)
        meta["local"].append(video_item)
        idx         = meta["local"].index(video_item)
        meta["local_id"][video_id] = idx
        meta["local_title"][video_title] = idx
        meta["downloads"][video_id] = {
                                       "path": fullpath,
                                       "location": path,
                                       "filename": filename,
                                       "type": fmtext[fmt],
                                       "fmt": fmt,
                                       "quality": fmtdesc[fmt]
                                       }
    else:
        print("[ URL ] '{0}'".format(url))
    return meta

def _playlist_job(args,job):
    playlist_id         = job.getnosect("playlist")
    pl_factory          = Playlist(playlist_id)
    skel                = pl_factory.skeleton()
    playlist_name       = skel["data"]["title"]
    playlist_author     = skel["data"]["author"]
    playlist_file=os.path.abspath(os.path.join("pl",os.path.normpath(playlist_id+".plm")))
    if not os.path.exists(playlist_file):
        meta            = dict([
            ("meta",dict([("name",playlist_name),("author",skel["data"]["author"]),("description",skel["data"]["description"]),
                          #("tags",list(skel["data"]["tags"])),
                          ("playlist_id",playlist_id),("url","http://youtube.com/playlist?list=PL"+playlist_id)])),
            ("items",list()),("cache",dict()),("local",list()),("local_id",dict()),("local_title",dict()),("downloads",dict())
        ])
    else:
        meta            = json.load(open(playlist_file))
    if job.getnosect("target_dir",False):
        playlist_target        = os.path.abspath(os.path.join("playlists",job.getnosect("target_dir")));
    else:
        playlist_target     = os.path.abspath(os.path.join("playlists",tofilename(meta["meta"]["name"])))
    if not os.path.isdir(playlist_target):
        os.makedirs(playlist_target)
    fmt_list            = _job_quality(job)
    if not fmt_list:
        return False
    print("[ JOB ] Playlist: \"{0}\" by {1}".format(playlist_name,playlist_author))
    print("[ JOB ] Synchronizing Data. Please Wait...")
    playlist            = pl_factory.advanced()
    meta["cache"]       = playlist
    items = playlist["data"]["items"]
    start = (args.offset if args.offset>-1 else job.getnosect("start",0))
    stop  = (start+args.max-1 if args.max>-1 else job.getnosect("stop",-1))
    items = (items[start:stop] if stop>-1 else items[start:])
    items = [i for i in items if i["video"]["id"] not in meta["items"]]
    for item in items:
        video_item      = item["video"]
        _download(args,meta,playlist_target,fmt_list,video_item);
        with open(playlist_file,"w") as fp:
            json.dump(meta,fp)
        print("[VIDEO] Done. Moving on.")
    print("[ JOB ] Done!")

def _favorites_job(args,job):
    userobj = User(job.getnosect("user"));
    #skel    = userobj.favorites_skeleton();
    #user    = skel["data"]["items"][0]["author"]; #broken? (*dummy*)
    user    = job.getnosect("user")
    meta_file=os.path.abspath(os.path.join("pl",os.path.normpath(tofilename(user)+".ytfav")));
    if not os.path.exists(meta_file):
        meta = dict([
            ("meta",dict([("name",user+"'s Favorites"),("author",user),("description",user+"'s favourite Videos"),
                          ("tags",[user]),("playlist_id","NULL"),("url","http://youtube.com/user/"+user),("type","favorites")])),
            ("items",list()),("cache","NULL"),("local",list()),("local_id",dict()),("local_title",dict()),("downloads",dict())
        ])
    else:
        meta = json.load(open(meta_file));
    if job.getnosect("target_dir",False):
        target=os.path.abspath(os.path.join("playlists",job.getnosect("target_dir")));
    else:
        target = os.path.abspath(os.path.join("playlists",tofilename(user)+"s Favorites"));
    if not os.path.exists(target):
        os.makedirs(target);
    fmt_list            = _job_quality(job)
    if not fmt_list:
        return False
    print("[ JOB ] {0}'s Favorites".format(user));
    print("[ JOB ] Synchronizing Indexes... Please Wait.");
    fav = userobj.favorites();
    meta["cache"] = fav;
    items = [i for i in fav["data"]["items"] if i["video"]["id"] not in meta["items"]]
    items = (items[args.offset:] if args.offset>0 else items)
    items = (items[:args.max] if args.max>0 else items)
    for item in items:
        _download(args,meta,target,fmt_list,item["video"]);
        with open(meta_file,"w") as fp:
            json.dump(meta,fp);
        print("[VIDEO] Done. Moving on.")
    print("[ JOB ] Done!")

def _job_quality(job):
    from libyo.youtube.resolve.profiles import profiles
    profile=job.getnosect("profile",list(profiles.keys())[0]).lower()
    if profile not in profiles:
        print("[ERROR] The Profile \"{0}\" is unknown".format(profile))
        return False
    if job.getnosect("resolution",job.getnosect("quality",None)):
        try:
            resolution = int(job.getnosect("resolution",job.getnosect("quality")).lower().rstrip("p"))
        except ValueError:
            print("[ERROR] Resolution has to be in this format: \"%i\" or \"%ip\" ('360' or '360p')")
            return False
        raw_map = profiles[profile][0]
        if resolution not in raw_map:
            print("[ WARN] The Exact Resolution given ({1}) is not avaiable in this Profile: \"{0}\"".format(profile,resolution))
        l= [ v for k,v in raw_map.items() if k <= resolution ]
        return l
    else:
        return list(profiles[profile][0].values())

def _recursive_resolve(video_id,resolve_order):
    umap=resolve3(video_id).urlmap
    for i in resolve_order:
        if i in umap:
            return umap[i],i

def _dom_textElement(tag,text):
    from xml.dom import minidom
    t = minidom.Text()
    t.data=text
    e = minidom.Element(tag)
    e.appendChild(t)
    return e
def _dom_addTextNode(node,tag,text):
    node.appendChild(_dom_textElement(tag,text))
def _create_xspf (meta,local,downloads,rel):
    from xml.dom import minidom
    document = minidom.getDOMImplementation().createDocument(None,"playlist",None)
    document.firstChild.setAttribute("xmlns","http://xspf.org/ns/0/")
    document.firstChild.setAttribute("version","1")
    document.firstChild.appendChild(_dom_textElement("title",  meta["title"]))
    document.firstChild.appendChild(_dom_textElement("creator",meta["author"]))
    document.firstChild.appendChild(_dom_textElement("info",   meta["url"]))
    trackList = minidom.Element("trackList")
    for i in local:
        vid = i["id"]
        track = minidom.Element("track")
        if rel:
            path = os.path.relpath(downloads[vid]["path"],rel)
        else:
            path = "file://"+downloads[vid]["path"]
        _dom_addTextNode(track,"location",   path)
        _dom_addTextNode(track,"creator",    i["uploader"])
        _dom_addTextNode(track,"title",      i["title"])
        _dom_addTextNode(track,"annotation", i["description"].replace("\r\n","\n"))
        _dom_addTextNode(track,"duration",   i["duration"])
        _dom_addTextNode(track,"image",      i["thumbnail"]["hqDefault"])
        _dom_addTextNode(track,"info",       "http://www.youtube.com/watch?v="+vid)
        trackList.appendChild(track)
    document.firstChild.appendChild(trackList)
    return document

if __name__=="__main__":
    main(sys.argv)
