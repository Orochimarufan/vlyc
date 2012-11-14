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
import sys
import os
import logging
import traceback
import re
import collections
import tempfile
import io
from PyQt4 import QtCore
from libyo.youtube import resolve
from libyo.youtube import subtitles
from libyo.youtube.resolve import profiles
from libyo.util.util import sdict_parser
from libyo.youtube import url as yt_url

class YoutubeHandler(QtCore.QObject):
    """
    The YouTube Resolving Handler (to be run inside a thread)
    """
    #/+++++++++++++++++++++++++++++++++++++++++++
    # Constants
    #+++++++++++++++++++++++++++++++++++++++++++/
    watch_regexp = yt_url.regexp
    invalid_message= "URL does not seem to be a valid YouTube Video URL:\r\n%s"
    resolve_message= "Could not resolve Video: %s\r\n(Are you sure your Internet connection is Up?)"
    logger = logging.getLogger("vlyc.YoutubeThread")
    main_q_lookup = list(profiles.profiles["mixed-avc"][0].values())
    pref_q_lookup = [22,18,5]
    #/+++++++++++++++++++++++++++++++++++++++++++
    # Initialization
    #+++++++++++++++++++++++++++++++++++++++++++/
    def __init__(self):
        super(YoutubeHandler,self).__init__()
        self.video_info = None
        self.qa_map = None
        self.subtitle_file = None
        self.subtitle_tracks = None
    #/+++++++++++++++++++++++++++++++++++++++++++
    # Signals
    #+++++++++++++++++++++++++++++++++++++++++++/
    newVideoInf = QtCore.pyqtSignal("PyQt_PyObject")
    videoUrlSet = QtCore.pyqtSignal("QString")
    subsfileSet = QtCore.pyqtSignal("QString")
    resolveBegn = QtCore.pyqtSignal()
    resolveDone = QtCore.pyqtSignal()
    resolveFail = QtCore.pyqtSignal("QString")
    qualityList = QtCore.pyqtSignal("QStringList",int)
    newSubsList = QtCore.pyqtSignal("QStringList")
    #/+++++++++++++++++++++++++++++++++++++++++++
    # Slots / Functions
    #+++++++++++++++++++++++++++++++++++++++++++/
    @QtCore.pyqtSlot("QString")
    def initYoutube(self, url):
        """
        Load a Youtube Video
        @called [SLOT]
        @arg    str     url     the Video's Watch URL
        @emits [resolveBegn],[resolveDone],[resolveFail]
        @calls initVideo,initSubtitles
        """
        self.logger.info("Initializing Video: %s"%url)
        self.resolveBegn.emit()
        #Parse the Watch URL
        try:
            video_id = yt_url.getIdFromUrl(url)
        except (ValueError,KeyError):
            self.logger.debug("url error",exc_info=True)
            self.resolveFail.emit(self.invalid_message%url)
            return
        #Initialize Video
        try: #We must not allow any Exceptions or the UI will block on the "Resolving Video" Dialog!
            self.initVideo(video_id)
        except:
            self.resolveFail.emit("\n".join(traceback.format_exception(*sys.exc_info())))
        #Initialize Subtitles
        try:
            self.initSubtitles(video_id)
        except:
            self.logger.warn("Subtitles Exception",exc_info=sys.exc_info())
        #Done
        self.resolveDone.emit()

    #/-------------------------------------------
    # Video URL Handling
    #-------------------------------------------/
    def initVideo(self,video_id):
        """
        [Internal] Resolve a Video
        @called initYoutube
        @arg    str     video_id    Video ID
        @emits  [resolveFail],[qualityList],[videoUrlSet],[newVideoInf]
        """
        #Get the Video URL
        self.logger.debug("Resolving Video: %s"%video_id)
        video_info = resolve.resolve3(video_id)
        if not video_info:
            self.resolveFail(self.resolve_message%video_id)
        self.video_info = video_info
        self.newVideoInf.emit(video_info)
        #Create Quality List
        self.logger.debug("Assembling Format List")
        self.qa_map = collections.OrderedDict()
        for f in self.main_q_lookup:
            if f in video_info.urlmap:
                self.qa_map[profiles.descriptions[f]]=f
        #Determine Initial Quality
        self.logger.debug("Determining fitting Quality Level")
        for f in self.pref_q_lookup:
            if f in video_info.urlmap:
                fmt = f
                break;
        else:
            self.logger.warn("No Preferred Quality Available. Choosing First Entry: %s",list(self.qa_map.keys())[0])
            fmt = list(self.qa_map.values())[0]
        #Emit Signal
        f = list(self.qa_map.values()).index(fmt)
        self.qualityList.emit(list(self.qa_map.keys()),f)
        self.videoUrlSet.emit(self.video_info.fmt_url(fmt))

    @QtCore.pyqtSlot("QString")
    def setQuality(self,descr):
        """
        Set the Quality Level
        @called [SLOT],initVideo
        @arg    str|int descr       the Quality Description or index
        @emits  [videoUrlSet]
        """
        fmt = self.qa_map[descr]
        self.videoUrlSet.emit(self.video_info.fmt_url(fmt))

    #/-------------------------------------------
    # Subtitle Handling
    #-------------------------------------------/
    def initSubtitles(self,video_id):
        """
        [internal] Initialize Subtitles
        @called initVideo
        @args   str     video_id
        @emits  [newSubsList]
        """
        self.logger.debug("Initializing Subtitles for Video '%s'"%self.video_info.title)
        self.cleanupSubtitles()
        self.subtitle_tracks = subtitles.getTracks(video_id)
        self.newSubsList.emit([t.lang_original for t in self.subtitle_tracks])

    @QtCore.pyqtSlot(int)
    def setSubtitleTrack(self,i):
        """
        Select a Subtitle Track
        @called [SLOT]
        @arg    int     i       Track Number
        @emits  [subsfileSet]
        @calls  cleanupSubtitles
        """
        self.cleanupSubtitles()
        track           = self.subtitle_tracks[i]
        self.logger.debug("Fetching Subtitle Track [%i] %s"%(i,track.lang_original))
        file            = tempfile.NamedTemporaryFile("wb",prefix="vlycsub",suffix=".srt",delete=False)
        file.writable   = \
        file.seekable   = \
        file.readable   = lambda: True
        handle          = io.TextIOWrapper(file,encoding="utf8")
        handle.write(track.getSRT())
        handle.close()
        file.close()
        self.subtitle_file = file.name
        #Emit signal
        self.subsfileSet.emit(self.subtitle_file)

    def cleanupSubtitles(self):
        """
        [Internal] Cleanup Old Subtitles File
        @called initSubs, [terminated]
        """
        if self.subtitle_file:
            os.remove(self.subtitle_file)
        self.subtitle_file = None

    def reannounceSubtitles(self):
        """
        Re-Emit the subsfileSet Signal
        @called [SLOT]
        """
        if self.subtitle_file:
            self.subsfileSet.emit(self.subtitle_file)
