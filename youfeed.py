#!/usr/bin/python3
#-@PydevCodeAnalysisIgnore
from __future__ import print_function

bytecount = 64*1024


import libyo
from libyo.youtube.resolve import resolve3
try:
    from libyo.youtube.playlist import mixed as playlistFull
except ImportError:
    from libyo.youtube.playlist import advanced as playlistFull
from libyo.youtube.playlist import skeleton as playlistSkeleton
from libyo.youtube.resolve.profiles import descriptions as fmtdesc, file_extensions as fmtext
from libyo.interface.progress.simple import SimpleProgress2
from libyo.urllib.download import download as downloadFile
from libyo.configparser import PcsxConfigParser
import argparse
import os
import json

def welcome():
    print("YouFeed v1.99.1b (libYo! v{0})".format(libyo.LIBYO_VERSION))
    print("(c) 2011-2012 Orochimarufan")

def main(ARGV):
    welcome()
    parser=argparse.ArgumentParser(prog=ARGV[0])
    parser.add_argument("-j","--job",metavar="JobFileName",dest="job",default=None,help="The Filename of the job definition file to use. (default: loop through everything in jobs dir)")
    args=parser.parse_args(ARGV[1:])
    joblist=[]
    if args.job:
        joblist.append(args.job)
    else:
        for i in os.listdir("jobs"):
            if i[-3:]=="ini":
                joblist.append(os.path.join("jobs",i))
    for jobfile in joblist:
        job=PcsxConfigParser()
        job.read(jobfile)
        job_name=job.getnosect("name")
        print("[ MAIN] Processing Job \"{0}\"...".format(job_name))
        job_type=job.getnosect("type").lower()
        if job_type in ("pl","playlist"):
            _playlist_job(job)
        else:
            print("YouFeed 2.0 does only support Playlist jobs as of now.")
    print("[ MAIN] Done. Farewell, may we meet again!")

def _playlist_job(job):
    playlist_id         = job.getnosect("playlist")
    skel                = playlistSkeleton(playlist_id)
    playlist_name       = skel["data"]["title"]
    playlist_author     = skel["data"]["author"]
    playlist_file=os.path.abspath(os.path.join("pl",os.path.normpath(playlist_id+".plm")))
    if not os.path.exists(playlist_file):
        meta            = dict([
            ("meta",dict([("name",playlist_name),("author",skel["data"]["author"]),("description",skel["data"]["description"]),("tags",list(skel["data"]["tags"]))])),
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
            video_title = video_item["title"]
            video_id    = video_item["id"]
            if video_id == "":
                print("[VIDEO] Found Deleted Video in Playlist. please clean up!")
                continue
            print("[VIDEO] Found new Video: \"{0}\" (ID='{1}')".format(video_title,video_id))
            print("[VIDEO] Preparing to Download...",end="\r")
            url,fmt     = _recursive_resolve(video_id,fmt_list)
            print("[VIDEO] Downloading with Quality level {0}".format(fmtdesc[fmt]))
            video       = resolve3(video_id)
            filename    = video.title.replace("/","-").replace(" ","_")+"."+fmtext[fmt]
            path        = playlist_target
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
            with open(playlist_file,"w") as fp:
                json.dump(meta,fp)
            print("[VIDEO] Done. Moving on.")
    if job.getnosect("createpl",False):
        xspf_file       = job.getnosect("createpl")
        try:
            xspf_file.index(".")
        except ValueError:
            xspf_file   += ".xspf"
        print("[ JOB ] Creating Local Playlist: '{0}'".format(xspf_file))
        xspf_object     = _create_xspf({"title":playlist_name,"url":"http://youtube.com/playlist?list=PL"+playlist_id,
                                  "author":playlist_author},meta["local"],meta["downloads"])
        with open(xspf_file,"w") as fp:
            xspf_object.writexml(fp, "", "", "", encoding="UTF-8")
            
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