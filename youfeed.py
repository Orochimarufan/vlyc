#!/usr/bin/python3
#-@PydevCodeAnalysisIgnore
from __future__ import print_function

bytecount = 64*1024
__VERSION__=(2,0,0,"a")
__LIBYO_R__=(0,9,7)


import libyo
libyo.reqVersion(*__LIBYO_R__)
from libyo.youtube.resolve import resolve3
try:
    from libyo.youtube.playlist import mixed as playlistFull
except ImportError:
    from libyo.youtube.playlist import advanced as playlistFull
from libyo.youtube.playlist import skeleton as playlistSkeleton
from libyo.youtube.User import User
from libyo.extern import argparse
from libyo.youtube.resolve.profiles import descriptions as fmtdesc, file_extensions as fmtext
from libyo.youtube.exception import YouTubeResolveError
from libyo.interface.progress.simple import SimpleProgress2
from libyo.urllib.download import download as downloadFile
from libyo.configparser import RawPcsxConfigParser, PcsxConfigParser
import os
import json

def welcome():
    print("YouFeed v{1}.{2}.{3}{4} (libyo v{0})".format(libyo.LIBYO_VERSION,*__VERSION__))
    print("(c) 2011-2012 Orochimarufan")

def main(ARGV):
    welcome()
    parser=argparse.ArgumentParser(prog=ARGV[0],description="A nifty piece of Software that lets you download YouTube Playlists.")
    parser.add_argument("-d","--dummy",action="store_true",dest="dummy",default=False,help="Don't download anything.")
    subparsers=parser.add_subparsers(default="all",title="subcommands",description="Use '%(prog)s (command) -h' to get further help. By Default, the 'all' command is run.")
    parser_def=subparsers.add_parser("all",description="Do all Jobs defined in the jobs/ directory.")
    parser_def.add_argument("-p","--playlist",action="store_true",dest="pl",default=False,help="Only update Job Playlists.")
    parser_def.set_defaults(command="")
    parser_job=subparsers.add_parser("job",description="Do one job defined in the jobs/ directory.")
    parser_job.add_argument("job",metavar="JobFileName",help="The Filename of the job definition file to use.")
    parser_job.add_argument("-n","--max",metavar="N",dest="max",default=-1,help="Max Number of Videos to download")
    parser_job.add_argument("-o","--offset",metavar="N",dest="offset",default=0,help="Skip N Videos")
    parser_job.add_argument("-p","--playlist",action="store_true",dest="pl",default=False,help="Only update Job Playlists.")
    parser_job.set_defaults(command="job")
    parser_run=subparsers.add_parser("run",description="Do a custom job.")
    parser_run.add_argument("job_type",help="The Job Type. [favorites,playlist]")
    parser_run.add_argument("job_argument",help="[playlist] The YouTube Playlist ID; [favorites] The Youtube User ID")
    parser_run.add_argument("-p","--playlist",metavar="xspf_file",dest="xspf_file",default=False,help="Create a Playlist File")
    parser_run.add_argument("-q","--quality",metavar="QA",dest="quality",default=720,type=int,help="The Quality level (360p -> 360; 720p -> 720)")
    parser_run.add_argument("-n","--max",metavar="N",dest="max",default=-1,help="Max Number of Videos to download")
    parser_run.add_argument("-o","--offset",metavar="N",dest="offset",default=0,help="Skip N Videos")
    parser_run.set_defaults(command="run")
    args=parser.parse_args(ARGV[1:])
    if "command" not in args or args.command=="":
        return _mode_joblist(args)
    elif args.command=="job":
        if args.job[-4:]!=".ini":
            args.job=args.job+".ini";
        return _mode_job(args,[os.path.join("jobs",args.job)])
    elif args.command=="run":
        return _mode_run(args)

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
            if job_type in ("fav","favorites","favourites"):
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
    
    if job.playlist:
        job.setnosect("createpl",args.playlist)
        _xspf_job(args,job)
    print("[ MAIN] Done. Farewell!")

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
    try:
        xspf_file.index(".")
    except ValueError:
        xspf_file   += ".xspf"
    
    print("[ JOB ] Creating Local Playlist: '{0}'".format(xspf_file))
    xspf_object     = _create_xspf(meta["meta"],meta["local"],meta["downloads"])
    
    with open(xspf_file,"w") as fp:
        xspf_object.writexml(fp, "", "", "", encoding="UTF-8")

def _download(args,meta,target,fmt_list,video_item):
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
    if not args.dummy:
        video       = resolve3(video_id)
        filename    = video.title.replace("/","-").replace(" ","_")+"."+fmtext[fmt]
        path        = target
        fullpath    = os.path.join(path,filename)
        progress    = SimpleProgress2()
        progress.name = video.title
        progress.task = "Downloading. (\x11)"
        if len(progress.name)>20:
            print(progress.name)
            progress.name="Downloading"
            progress.task="\x11"
        downloadFile(url,fullpath,progress,2,bytecount)
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
    skel                = playlistSkeleton(playlist_id)
    playlist_name       = skel["data"]["title"]
    playlist_author     = skel["data"]["author"]
    playlist_file=os.path.abspath(os.path.join("pl",os.path.normpath(playlist_id+".plm")))
    if not os.path.exists(playlist_file):
        meta            = dict([
            ("meta",dict([("name",playlist_name),("author",skel["data"]["author"]),("description",skel["data"]["description"]),
                          ("tags",list(skel["data"]["tags"])),("playlist_id",playlist_id),("url","http://youtube.com/playlist?list=PL"+playlist_id)])),
            ("items",list()),("cache",dict()),("local",list()),("local_id",dict()),("local_title",dict()),("downloads",dict())
        ])
    else:
        meta            = json.load(open(playlist_file))
    playlist_target     = os.path.abspath(os.path.join("playlists",meta["meta"]["name"]))
    if not os.path.isdir(playlist_target):
        os.makedirs(playlist_target)
    fmt_list            = _job_quality(job)
    if not fmt_list:
        return False
    print("[ JOB ] Playlist: \"{0}\" by {1}".format(playlist_name,playlist_author))
    print("[ JOB ] Synchronizing Data. Please Wait...")
    playlist            = playlistFull(playlist_id)
    playlist_items      = playlist["data"]["items"]
    meta["cache"]       = playlist
    for item in playlist_items:
        video_item      = item["video"]
        if video_item["id"] not in meta["items"]:
            _download(args,meta,playlist_target,fmt_list,video_item);
            with open(playlist_file,"w") as fp:
                json.dump(meta,fp)
            print("[VIDEO] Done. Moving on.")
    print("[ JOB ] Done!")

def _favorites_job(args,job):
    userobj = User(job.getnosect("user"));
    skel    = userobj.favorites_skeleton();
    user    = skel["data"]["items"][0]["author"];
    meta_file=os.path.abspath(os.path.join("pl",os.path.normpath(user+".ytfav")));
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
        target = os.path.abspath(os.path.join("playlists",user+"s Favorites"));
    if not os.path.exists(target):
        os.makedirs(target);
    fmt_list            = _job_quality(job)
    if not fmt_list:
        return False
    print("[ JOB ] {0}'s Favorites".format(user));
    print("[ JOB ] Synchronizing Indexes... Please Wait.");
    fav = userobj.favorites();
    meta["cache"] = fav;
    for item in fav["data"]["items"]:
        if item["video"]["id"] not in meta["items"]:
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
    if job.getnosect("resolution",None):
        try:
            resolution = int(job.getnosect("resolution").lower().rstrip("p"))
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
def _create_xspf (meta,local,downloads):
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
        _dom_addTextNode(track,"location",   "file://"+downloads[vid]["path"])
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
    import sys
    main(sys.argv)