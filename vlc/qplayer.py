"""
/*****************************************************************************
 * vlc :: player.py : VLC Interface
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

import logging

from PyQt4 import QtCore

from . import libvlc
from . import vlcevent
from . import util
from . import medialistplayer

logger = logging.getLogger(__name__)


def libvlc_version():
    return tuple([int(i) for i in libvlc_versionstring().split(" ")[0].split(".")])


def libvlc_hexversion():
    return int("{0:02x}{1:02x}{2:02x}".format(*libvlc_version()), 16)


def libvlc_codename():
    return libvlc_versionstring().split(" ", 2)[1]


def libvlc_versionstring():
    return util.pystring(libvlc.libvlc_get_version())

Signal = QtCore.pyqtSignal
_instance = None


def initInstance(argv=None):
    global _instance
    if (_instance):
        raise libvlc.VLCException("libvlc already initialized!")
    _instance = libvlc.Instance(*argv)
    return not not _instance


def getInstance():
    global _instance
    if (not _instance):
        #_instance = libvlc.Instance()
        _instance = libvlc.libvlc_new(0, None)
    return _instance


class Player(QtCore.QObject):
    """
    Wraps a libvlc MediaPlayer into a QObject
    
    signals:
        stateChanged(int)       -> collection of all state-Events   [State Value]
        mediaChanged(Media)     -> MediaPlayerMediaChanged          [Media(e.u.media)]
        positionChanged(float)  -> MediaPlayerPositionChanged       [e.u.new_position]
        timeChanged(int)        -> MediaPlayerTimeChanged           [e.u.new_time]
        seekableChanged(int)    -> MediaPlayerSeekableChanged       [e.u.new_seekable]
        pausableChanged(int)    -> MediaPlayerPausableChanged       [e.u.new_pausable]
        titleChanged(QString)   -> MediaPlayerTitleChanged          [e.u.new_title]
        lengthChanged(int)      -> MediaPlayerLengthChanged         [e.u.new_length]
        wentForward()           -> MediaPlayerForward               []
        wentBackward()          -> MediaPlayerBackward              []
        snapshotTaken()         -> MediaPlayerSnapshotTaken         []
        voutEvent()             -> MediaPlayerVout                  []
        endReached()            -> MediaPlayerEndReached            []
        error(Event)            -> MediaPlayerEncounteredError      [e]
    
    you can connect to libvlc events directly if you must:
        p.EventManager.connect(int event_id, callable callback)
    disconnect:
        p.EventManager.disconnect(int event_id, callable callback)
    """
    
    __logger = logger.getChild("Player")
    
    #/-------------------------------------------------------
    # MediaPlayer State Enum
    #+------------------------------------------------------+
    # See libvlc docs
    #-------------------------------------------------------/
    State = util.vlcenum(libvlc.State)
    
    #/-------------------------------------------------------
    # Signals
    #-------------------------------------------------------/
    stateChanged = Signal(int)
    error = Signal("PyQt_PyObject")
    mediaChanged = Signal("PyQt_PyObject")
    endReached = Signal()
    positionChanged = Signal(float)
    timeChanged = Signal(int)
    wentForward = Signal()
    wentBackward = Signal()
    seekableChanged = Signal(int)
    pausableChanged = Signal(int)
    titleChanged = Signal("QString")
    lengthChanged = Signal(int)
    snapshotTaken = Signal()
    voutEvent = Signal()
    buffering = Signal("float")
    
    #/-------------------------------------------------------
    # Constructor
    #-------------------------------------------------------/
    def __init__(self, instance=None):
        """
        Construct a Player instance
        
        @arg instance    libvlc instance. default: global vlyc.player instance
        """
        super(Player, self).__init__()
        
        if (instance is None):
            instance = getInstance()
        
        self.Instance = instance
        self.MediaPlayer = instance.media_player_new()
        
        #Event Handling
        manager = self.MediaPlayer.get_event_manager() #Patched in by vlcevent.py
        
        manager.connect(vlcevent.Event.MediaPlayerNothingSpecial,    self.vlcevent_nothing)
        manager.connect(vlcevent.Event.MediaPlayerOpening,           self.vlcevent_opening)
        manager.connect(vlcevent.Event.MediaPlayerBuffering,         self.vlcevent_buffering)
        manager.connect(vlcevent.Event.MediaPlayerPaused,            self.vlcevent_paused)
        manager.connect(vlcevent.Event.MediaPlayerPlaying,           self.vlcevent_playing)
        manager.connect(vlcevent.Event.MediaPlayerEndReached,        self.vlcevent_end)
        manager.connect(vlcevent.Event.MediaPlayerEncounteredError,  self.vlcevent_error)
        manager.connect(vlcevent.Event.MediaPlayerMediaChanged,      self.vlcevent_media)
        manager.connect(vlcevent.Event.MediaPlayerPositionChanged,   self.vlcevent_position)
        manager.connect(vlcevent.Event.MediaPlayerTimeChanged,       self.vlcevent_time)
        
        self.EventManager = manager
    
    #/-------------------------------------------------------
    # VLC Events
    #-------------------------------------------------------/
    def vlcevent_nothing(self, event):
        self.stateChanged.emit(self.State.NothingSpecial)
    
    def vlcevent_opening(self, event):
        self.stateChanged.emit(self.State.Opening)
    
    def vlcevent_buffering(self, event):
        self.stateChanged.emit(self.State.Buffering)
        self.buffering.emit(event.u.new_cache)
    
    def vlcevent_paused(self, event):
        self.stateChanged.emit(self.State.Paused)
    
    def vlcevent_playing(self, event):
        self.stateChanged.emit(self.State.Playing)
    
    def vlcevent_end(self, event):
        self.stateChanged.emit(self.State.Ended)
        self.endReached.emit()
    
    def vlcevent_error(self, event):
        self.stateChanged.emit(self.State.Error)
    
    def vlcevent_media(self, event):
        self.mediaChanged.emit(libvlc.Media(event.u.media))
    
    def vlcevent_position(self, event):
        self.positionChanged.emit(event.u.new_position)
    
    def vlcevent_time(self, event):
        self.timeChanged.emit(event.u.new_time)
    
    #/-------------------------------------------------------
    # Methods / Slots
    #-------------------------------------------------------/
    def open_media(self, mrl):
        mrl = util.pystring(mrl)
        if (":" in mrl and mrl.index(":") > 1):
            media = self.Instance.media_new_location(util.vlcstring(mrl))
        else:
            media = self.Instance.media_new_path(util.vlcstring(mrl))
        return media
    
    def open(self, mrl): #@ReservedAssignment
        self.set_media(self.open_media(mrl))
    
    #/-------------------------------------------------------
    # Internal
    #-------------------------------------------------------/
    def __getattr__(self, name):
        """ Redirect Other Requests to the MediaPlayer Instance """
        return getattr(self.MediaPlayer, name)


class MLPlayer(Player):
    """
    Wraps a MediaPlayer and MediaListPlayer into a QObject
    provides Signals for libvlc events
    
    signals:
        stateChanged(int)       -> collection of all state-Events   [State Value]
        mediaChanged(Media)     -> MediaPlayerMediaChanged          [Media(e.u.media)]
        positionChanged(float)  -> MediaPlayerPositionChanged       [e.u.new_position]
        timeChanged(int)        -> MediaPlayerTimeChanged           [e.u.new_time]
        seekableChanged(int)    -> MediaPlayerSeekableChanged       [e.u.new_seekable]
        pausableChanged(int)    -> MediaPlayerPausableChanged       [e.u.new_pausable]
        titleChanged(QString)   -> MediaPlayerTitleChanged          [e.u.new_title]
        lengthChanged(int)      -> MediaPlayerLengthChanged         [e.u.new_length]
        wentForward()           -> MediaPlayerForward               []
        wentBackward()          -> MediaPlayerBackward              []
        snapshotTaken()         -> MediaPlayerSnapshotTaken         []
        voutEvent()             -> MediaPlayerVout                  []
        endReached()            -> MediaPlayerEndReached            []
        error(Event)            -> MediaPlayerEncounteredError      [e]
    
    you can connect to libvlc events directly if you must:
        p = Player()
        my_function = lambda e: print(e.u.new_time, end="\r")
        p.mpManager.connect(p.mpManager.mpEvent.TimeChanged, my_function)
    or:
        p.mpManager.connect(p.mpManager.Event.MediaPlayerTimeChanged, my_function)
    or:
        p.mpManager.connect(libvlc.EventType.MediaPlayerTimeChanged.value, my_function)
    short:
        p.mpManager.connect(int event_id, callable callback)
    disconnect:
        p.mpManager.disconnect(int event_id, callable callback)
    
    to connect to the MediaListPlayer use the lpManager instead of mpManager and lpEvent instead of mpEvent
    """
    
    #signals
    nextItemSet = QtCore.Signal("PyQt_PyObject")
    stopped = QtCore.Signal()
    
    #constructor
    def __init__(self, p_inst=None):
        super(MLPlayer, self).__init__(p_inst)
        
        self.ListPlayer = medialistplayer.MediaListPlayer(self.Instance)
        self.ListPlayer.set_media_player(self.MediaPlayer)
        self.MediaList = None
        
        self.ListPlayerManager = self.ListPlayer.get_event_manager()
        self.ListPlayerManager.connect(vlcevent.MediaListPlayerEvent.Stopped, self.vlcevent_stopped)
        self.ListPlayerManager.connect(vlcevent.MediaListPlayerEvent.NextItemSet, self.vlcevent_nextItemSet)
    
    # signals
    def vlcevent_stopped(self, event):
        self.stopped.emit()
    
    def vlcevent_nextItemSet(self, event):
        self.nextItemSet.emit(event.u.media_list_player_next_item_set.item)
    
    #attribute lookup
    def __getattr__(self, name):
        try:
            return getattr(self.ListPlayer, name)
        except AttributeError:
            return getattr(self.MediaPlayer, name)
    
    #slots
    def set_media_list(self, p_ml):
        self.MediaList = p_ml
        self.ListPlayer.set_media_list(p_ml)
    
    def open(self, mrl): #@ReservedAssignment
        media = self.open_media(mrl)
        self.set_media(media)
    
    def open_add(self, mrl):
        media = self.open_media(mrl)
        self.add_media(media)
    
    def set_media(self, media):
        self.MediaList.add_media(media)
        self.ListPlayer.play_item(media)
            
    set_media_player = None #We dont want people to do that
    event_manager   = None #That neither. use the mpManager and lpManager instead
