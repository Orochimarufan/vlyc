"""
/*****************************************************************************
 * vlyc :: youtube.py : Youtube Thread
 ****************************************************************************
 * Copyright (C) 2012 Orochimarufan
 *
 * Authors:  Orochimarufan <orochimarufan.x3@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.
 *****************************************************************************/
"""
from __future__ import absolute_import, unicode_literals

import os
import logging
import collections
import tempfile
import io
import json

from PyQt4 import QtCore

from libyo.youtube import resolve
from libyo.youtube import subtitles
from libyo.youtube.resolve import profiles
from libyo.youtube import url as yt_url
from libyo.youtube import auth
from libyo.compat import htmlparser
from libyo.util.util import sdict_parser
from libyo import urllib

UserAgent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.4 (KHTML, like Gecko) Chrome/22.0.1229.79 Safari/537.4"


class Resolve(QtCore.QObject):
    """ VLYC's own resolver """
    
    error = QtCore.Signal(str)
    
    def __init__(self, video_id):
        super(Resolve, self).__init__()
        self.video_id = video_id
        self.title = None
        self.uploader = None
        self.urlmap = None
        self.submap = None
        self.description = None
        self.done = False
    
    def resolve(self):
        """ Resolve the video """
        req = urllib.request.Request("http://youtube.com/watch?v=%s&gl=US&hl=en&has_verified=1" % self.video_id)
        req.add_header("User-Agent", UserAgent)
        req.add_header("Referer", "http://youtube.com")
        with auth.urlopen(req) as fp:
            document = htmlparser.parse(fp)
        # same as WebBackend
        page = document.getroot()
        div = page.get_element_by_id("player")
        # See if youtube shows an error message
        try:
            error = div.get_element_by_id("unavailable-message")
        except:
            error = None
        if error is not None:
            self.error.emit(error.text.strip())
            return False
        # get the player config
        src = div[3].text
        fvars = src[src.index("ytplayer.config = {") + 18:src.rindex("}") + 1]
        try:
            data = json.loads(fvars, strict=False)
        except:
            with tempfile.NamedTemporaryFile("w", suffix=".json", prefix="vlyc", delete=False) as fp:
                fp.write(fvars)
            self.error.emit("Could not parse flashvars. See %s" % fp.name)
            return False
        args = data["args"]
        # extract info
        self.urlmap = dict(
            [
                (
                    int(i["itag"]),
                    "&signature=".join((i["url"], i["sig"]))
                )
                for i in [sdict_parser(i, unq=2) for i in args["url_encoded_fmt_stream_map"].split(",")]
            ]
        )
        self.title = args["title"]
        self.uploader = page.get_element_by_id("watch7-user-header")[1].text
        self.description = page.get_element_by_id("eow-description").text
        # Done
        self.done = True
        return True
    
    def get_subs(self):
        """ get the subtitles """
        self.submap = subtitles.getTracks(self.video_id)
    
    def resolve_libyo(self):
        """ ask libyo to resolve. """
        info = resolve.resolve3(self.video_id)
        if not info:
            self.error.emit("Could not find out about video %s using libyo" % self.video_id)
            return False
        self.title = info["title"]
        self.description = info["description"]
        self.uploader = info["uploader"]
        self.urlmap = info["fmt_url_map"]
        self.done = True
        return True


class YoutubeHandler(QtCore.QObject):
    """
    The YouTube Resolving Handler (to be run inside a thread)
    """
    #/+++++++++++++++++++++++++++++++++++++++++++
    # Constants
    #+++++++++++++++++++++++++++++++++++++++++++/
    watch_regexp = yt_url.regexp
    invalid_message = "URL does not seem to be a valid YouTube Video URL:\r\n%s"
    resolve_message = "Could not resolve Video: %s\r\n(Are you sure your Internet connection is Up?)"
    logger = logging.getLogger("vlyc.YoutubeThread")
    main_q_lookup = list(profiles.profiles["mixed-avc"][0].values())
    pref_q_lookup = [22, 18, 5]
    use_libyo = False
    
    #/+++++++++++++++++++++++++++++++++++++++++++
    # Initialization
    #+++++++++++++++++++++++++++++++++++++++++++/
    def __init__(self):
        super(YoutubeHandler, self).__init__()
        self.video = None
        self.qa_map = None
        self.subtitle_file = None
    
    #/+++++++++++++++++++++++++++++++++++++++++++
    # Signals
    #+++++++++++++++++++++++++++++++++++++++++++/
    newVideo = QtCore.Signal("PyQt_PyObject")
    setUrl   = QtCore.Signal(str)
    setSub   = QtCore.Signal(str)
    fmtList  = QtCore.Signal("QStringList", int)
    subList  = QtCore.Signal("QStringList")
    # status
    started  = QtCore.Signal()
    finished = QtCore.Signal()
    failed   = QtCore.Signal(str)
    
    #/+++++++++++++++++++++++++++++++++++++++++++
    # Slots / Functions
    #+++++++++++++++++++++++++++++++++++++++++++/
    @QtCore.Slot(str)
    def fromUrl(self, url):
        """ Load a Youtube Video by its watch url """
        self.logger.info("Initializing Video from URL: %s" % url)
        self.started.emit()
        try:
            video_id = yt_url.getIdFromUrl(url)
        except:
            self.logger.debug("url error", exc_info=True)
            self.failed.emit(self.invalid_message % url)
            return
        self.run(video_id)
    
    @QtCore.Slot(str)
    def fromId(self, video_id):
        """ Load a YouTube Video by it's ID """
        self.logger.info("Initializing Video from ID: %s" % video_id)
        self.started.emit()
        self.run(video_id)
    
    def run(self, video_id):
        """ Do the Actual Work """
        self.video = Resolve(video_id)
        
        # get the video
        self.video.error.connect(self.failed)
        
        if self.use_libyo:
            self.video.resolve_libyo()
        else:
            self.video.resolve()
        
        if not self.video.done:
            return
        
        self.newVideo.emit(self.video)
        
        #Create Quality List
        self.logger.debug("Assembling Format List")
        self.qa_map = collections.OrderedDict()
        for f in self.main_q_lookup:
            if (f in self.video.urlmap):
                self.qa_map[profiles.descriptions[f]] = f
        #Determine Initial Quality
        self.logger.debug("Determining fitting Quality Level")
        for f in self.pref_q_lookup:
            if (f in self.qa_map.values()):
                fmt = f
                break
        else:
            self.logger.warn("No Preferred Quality Available. Choosing First Entry: %s",
                             list(self.qa_map.keys())[0])
            fmt = list(self.qa_map.values())[0]
        #Emit Signal
        self.fmtList.emit(list(self.qa_map.keys()), list(self.qa_map.values()).index(fmt))
        self.setUrl.emit(self.video.urlmap[fmt])
        
        # get the subs
        self.logger.debug("Initializing Subs")
        self.cleanupSubtitles()
        self.video.get_subs()
        self.subList.emit([t.lang_original for t in self.video.submap])
        
        # done
        self.finished.emit()

    @QtCore.Slot(str)
    def setQuality(self, descr):
        """ Set the Quality Level """
        self.setUrl.emit(self.video.urlmap[self.qa_map[descr]])

    @QtCore.Slot(int)
    def setSubtitleTrack(self, i):
        """
        Select a Subtitle Track
        @arg    int     i       Track Number
        """
        self.cleanupSubtitles()
        track = self.video.submap[i]
        self.logger.debug("Fetching Subtitle Track [%i] %s" % (i, track.lang_original))
        file = tempfile.NamedTemporaryFile("wb", prefix="vlyc", suffix=".srt", delete=False)
        file.writable = file.seekable   = file.readable   = lambda: True
        handle = io.TextIOWrapper(file, encoding="utf8")
        handle.write(track.getSRT())
        handle.close()
        file.close()
        self.subtitle_file = file.name
        #Emit signal
        self.setSub.emit(self.subtitle_file)

    def cleanupSubtitles(self):
        """
        [Internal] Cleanup Old Subtitles File
        @called initSubs, [terminated]
        """
        if (self.subtitle_file) and os.path.exists(self.subtitle_file):
            os.remove(self.subtitle_file)
        self.subtitle_file = None

    @QtCore.Slot()
    def reannounceSubtitles(self):
        """ Re-Emit the setSub Signal """
        if (self.subtitle_file):
            self.setSub.emit(self.subtitle_file)
