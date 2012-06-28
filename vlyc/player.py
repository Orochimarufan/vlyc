"""
/*****************************************************************************
 * player.py : VLC Interface
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
import ctypes
from . import libvlc
from .util import Enum
from PyQt4 import QtCore
import logging
logger_lib = logging.getLogger("libvlc")

if sys.hexversion>=0x3000000:
    vlcstring = lambda s: bytes(s, "utf8")
    natstring = lambda s: str(s,"utf8")
    _strings = (str)
else:
    vlcstring = lambda s: str(s)
    natstring = lambda s: str(s)
    _strings = (str, unicode)

_vlcenum = lambda enum: Enum(enum.__name__, **dict([(n, v) for v,n in enum._enum_names_.items()]))

def libvlc_version():
   return tuple([int(i) for i in libvlc_versionstring().split(" ")[0].split(".")])
def libvlc_hexversion():
   return int("{0:02x}{1:02x}{2:02x}".format(*libvlc_version()),16)
def libvlc_codename():
   return libvlc_versionstring().split(" ",2)[1]
def libvlc_versionstring():
   return natstring(libvlc.libvlc_get_version())

Signal = QtCore.pyqtSignal

class EventUnion(ctypes.Union):
    _fields_ = [
        ('meta_type',    ctypes.c_uint    ),
        ('new_child',    ctypes.c_uint    ),
        ('new_duration', ctypes.c_longlong),
        ('new_status',   ctypes.c_int     ),
        ('media',        ctypes.c_void_p  ),
        ('new_state',    ctypes.c_uint    ),
        # Media instance
        ('new_position', ctypes.c_float   ),
        ('new_time',     ctypes.c_longlong),
        ('new_title',    ctypes.c_int     ),
        ('new_seekable', ctypes.c_longlong),
        ('new_pausable', ctypes.c_longlong),
        ('new_cache',    ctypes.c_float   ),
        # FIXME: Skipped MediaList and MediaListView...
        ('filename',     ctypes.c_char_p  ),
        ('new_length',   ctypes.c_longlong),
        ('media_event',  libvlc.MediaEvent),
    ]

class VlcEvent(libvlc._Cstruct):
    _fields_ = [
        ('type',   ctypes.c_int   ),
        ('object', ctypes.c_void_p),
        ('u',      EventUnion     ),
    ]

class EventManager(object):
    """
    python-vlc's one just doesn't do it
    """
    Event = _vlcenum(libvlc.EventType)
    miEvent = Enum("media_event_e", 
                 MetaChanged        = Event.MediaMetaChanged,           #?
                 SubItemAdded       = Event.MediaSubItemAdded,          #?
                 DurationChanged    = Event.MediaDurationChanged,       #?
                 ParsedChanged      = Event.MediaParsedChanged,         #?
                 Freed              = Event.MediaFreed,                 #?
                 StateChanged       = Event.MediaStateChanged,          #?
                 )
    mpEvent = Enum("media_player_event_e", 
                 MediaChanged       = Event.MediaPlayerMediaChanged,    #None
                 NothingSpecial     = Event.MediaPlayerNothingSpecial,  #None
                 Opening            = Event.MediaPlayerOpening,         #None
                 Buffering          = Event.MediaPlayerBuffering,       #new_cache      [int]
                 Playing            = Event.MediaPlayerPlaying,         #None
                 Paused             = Event.MediaPlayerPaused,          #None
                 Stopped            = Event.MediaPlayerStopped,         #None
                 Forward            = Event.MediaPlayerForward,         #?
                 Backward           = Event.MediaPlayerBackward,        #?
                 EndReached         = Event.MediaPlayerEndReached,      #None
                 EncounteredError   = Event.MediaPlayerEncounteredError,#?
                 TimeChanged        = Event.MediaPlayerTimeChanged,     #new_time       [int]
                 PositionChanged    = Event.MediaPlayerPositionChanged, #new_position   [float]
                 SeekableChanged    = Event.MediaPlayerSeekableChanged, #
                 PausableChanged    = Event.MediaPlayerPausableChanged, 
                 TitleChanged       = Event.MediaPlayerTitleChanged, 
                 SnapshotTaken      = Event.MediaPlayerSnapshotTaken,   #[psz_]filename [char*]
                 LengthChanged      = Event.MediaPlayerLengthChanged,   #new_length     [longlong]
                 Vout               = Event.MediaPlayerVout,            #new_count      [int]
                 )
    mlEvent = Enum("media_list_event_e", 
                 ItemAdded          = Event.MediaListItemAdded,         #?
                 WillAddItem        = Event.MediaListWillAddItem,       #?
                 ItemDeleted        = Event.MediaListItemDeleted,       #?
                 WillDeleteItem     = Event.MediaListWillDeleteItem,    #?
                 )
    lvEvent = Enum("media_list_view_event_e", 
                 ItemAdded          = Event.MediaListViewItemAdded,     #?
                 WillAddItem        = Event.MediaListViewWillAddItem,   #?
                 ItemDeleted        = Event.MediaListViewItemDeleted,   #?
                 WillDeleteItem     = Event.MediaListViewWillDeleteItem,#?
                 )
    lpEvent = Enum("media_list_player_event_e", 
                 Played             = Event.MediaListPlayerPlayed,      #?
                 NextItemSet        = Event.MediaListPlayerNextItemSet, #?
                 Stopped            = Event.MediaListPlayerStopped,     #?
                 )
    mdEvent = Enum("media_discoverer_event_e", 
                 Started            = Event.MediaDiscovererStarted,     #?
                 Ended              = Event.MediaDiscovererEnded,       #?
                 )
    vlmEvent = Enum("video_lan_manager_event_e", 
                 MediaAdded         = Event.VlmMediaAdded,              #?
                 MediaRemoved       = Event.VlmMediaRemoved,            #?
                 MediaChanged       = Event.VlmMediaChanged,            #?
                 MediaInstanceStarted       = Event.VlmMediaInstanceStarted,        #?
                 MediaInstanceStopped       = Event.VlmMediaInstanceStopped,        #?
                 MediaInstanceStatusInit    = Event.VlmMediaInstanceStatusInit,     #?
                 MediaInstanceStatusOpening = Event.VlmMediaInstanceStatusOpening,  #?
                 MediaInstanceStatusPlaying = Event.VlmMediaInstanceStatusPlaying,  #?
                 MediaInstanceStatusPause   = Event.VlmMediaInstanceStatusPause,    #?
                 MediaInstanceStatusEnd     = Event.VlmMediaInstanceStatusEnd,      #?
                 mediaInstanceStatusError   = Event.VlmMediaInstanceStatusError,    #?
                 )
    
    def __init__(self, player, is_player=True):
        self._callbacks = dict()
        self._haveEvent = list()
        self._debug = None
        if is_player:
            self._vlcmanager = player.event_manager()
        else:
            self._vlcmanager = player
        d = ctypes.CFUNCTYPE(None, ctypes.POINTER(VlcEvent), ctypes.c_void_p)
        self._handler = d( lambda event, user_data: self._dispatch(event.contents) )
    
    def _dispatch(self, event):
        evt = event.type
        if self._debug is not None:
            self._debug(event)
        if evt is None:
            logger_lib.getChild("EventManager").warn("Got NULL Event")
            return
        if evt not in self._callbacks:
            logger_lib.getChild("EventManager").warn("Unrequested Event: %i"%evt)#SHOULD NOT HAPPEN
            return
        for cb in self._callbacks[evt]:
            cb(event)
    
    def connect(self, evt, slot):
        if evt not in self._callbacks:
            self._callbacks[evt]=list()
        self._callbacks[evt].append(slot)
        if evt not in self._haveEvent:
            self._attach(evt)
    
    def disconnect(self, evt, slot):
        self._callbacks[evt].remove(slot)
        if len(self._callbacks[evt])<1:
            self._detach(evt)
    
    def set_debug(self, func):
        self._debug = func
    
    def _attach(self, evt):
        r = libvlc.dll.libvlc_event_attach(self._vlcmanager, evt, self._handler, None)
        if r!=0: logger_lib.getChild("EventManager").error("Could not attach event: %i"%evt)
        self._haveEvent.append(evt)
    def _detach(self, evt):
        r = libvlc.dll.libvlc_event_detach(self._vlcmanager, evt, self._handler, None)
        if r!=0: logger_lib.getChild("EventManager").warn("Could not detach event: %i"%evt)
        self._haveEvent.remove(evt)

_instance = None
def initInstance(argv=None):
    global _instance
    if _instance:
        raise libvlc.VLCException("libvlc already initialized!")
    _instance = libvlc.Instance(*argv)
    return not not _instance
def getInstance():
    global _instance
    if not _instance:
        #_instance = libvlc.Instance()
        _instance = libvlc.libvlc_new(0,None)
    return _instance
    
class Player(QtCore.QObject):
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
        my_function = lambda e: print(e.u.new_time,end="\r")
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
    
    State = _vlcenum(libvlc.State)
    
    #signals
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
    
    #constructor
    def __init__(self):
        super(Player, self).__init__()
        
        self.MediaPlayer = getInstance().media_player_new()
        self.ListPlayer = getInstance().media_list_player_new()
        self.ListPlayer.set_media_player(self.MediaPlayer)
        self.Media = None
        self.MediaList = None
        
        self._mediaListOverride = False
        
        #Events
        manager = EventManager(libvlc.libvlc_media_player_event_manager(self.MediaPlayer), False)
        manager2 = EventManager(libvlc.libvlc_media_list_player_event_manager(self.ListPlayer), False)
        
        #State Events
        manager.connect(manager.Event.MediaPlayerNothingSpecial, lambda e: self.stateChanged.emit(self.State.NothingSpecial))
        manager.connect(manager.Event.MediaPlayerOpening, lambda e: self.stateChanged.emit(self.State.Opening))
        manager.connect(manager.Event.MediaPlayerBuffering, lambda e: self.stateChanged.emit(self.State.Buffering))
        manager.connect(manager.Event.MediaPlayerPaused, lambda e: self.stateChanged.emit(self.State.Paused))
        manager.connect(manager.Event.MediaPlayerPlaying, lambda e: self.stateChanged.emit(self.State.Playing))
        manager.connect(manager.Event.MediaPlayerStopped, lambda e: self.stateChanged.emit(self.State.Stopped))
        manager.connect(manager.Event.MediaPlayerEndReached, lambda e: self.stateChanged.emit(self.State.Ended))
        manager.connect(manager.Event.MediaPlayerEncounteredError, lambda e: self.stateChanged.emit(self.State.Error))
        manager.connect(manager.Event.MediaPlayerEndReached, self.endReached.emit)
        manager.connect(manager.Event.MediaPlayerEncounteredError, self.error.emit)
        manager.connect(manager.Event.MediaPlayerBuffering, lambda e: self.buffering.emit(e.u.new_cache))
        
        #Others
        manager.connect(manager.Event.MediaPlayerMediaChanged, lambda e: self.mediaChanged.emit(libvlc.Media(e.u.media)))
        manager.connect(manager.Event.MediaPlayerPositionChanged, lambda e: self.positionChanged.emit(e.u.new_position))
        manager.connect(manager.Event.MediaPlayerTimeChanged, lambda e: self.timeChanged.emit(e.u.new_time))
        manager.connect(manager.Event.MediaPlayerBackward, self.wentBackward.emit)
        manager.connect(manager.Event.MediaPlayerForward, self.wentForward.emit)
        manager.connect(manager.Event.MediaPlayerSeekableChanged, lambda e: self.seekableChanged.emit(e.u.new_seekable))
        manager.connect(manager.Event.MediaPlayerPausableChanged, lambda e: self.pausableChanged.emit(e.u.new_pausable))
        
        #Internal
        #def doMediaChange(e):
        #    self.Media = libvlc.libvlc_media_player_get_media(e.object)
        #manager.connect(manager.mpEvent.MediaChanged, doMediaChange)
        
        self.mpManager = manager
        self.lpManager = manager2
    
    #attribute lookup
    def __getattr__(self, name):
        try:
            return getattr(self.ListPlayer, name)
        except AttributeError:
            return getattr(self.MediaPlayer, name)

    #slots
    def open_media(self, mrl):
        if ":" in mrl and mrl.index(":")>1:
            media = getInstance().media_new_location(vlcstring(mrl))
        else:
            media = getInstance().media_new_path(vlcstring(mrl))
        return media
    
    def open(self, mrl):
        media = self.open_media(mrl)
        self.MediaPlayer.set_media(media)
        self._mediaListOverride = True
    
    def play(self):
        if self.MediaList is None or self._mediaListOverride:
            self.MediaPlayer.play()
        else:
            self.ListPlayer.play()
    def pause(self):
        if self.MediaList is None or self._mediaListOverride:
            self.MediaPlayer.pause()
        else:
            self.ListPlayer.pause()
    
    def stop(self):
        #if self.ListPlayer.is_playing():
        #    self.ListPlayer.stop()
        #else:
        self.MediaPlayer.stop()
            
    set_media_player = None #We dont want people to do that
    event_manager   = None #That neither. use the mpManager and lpManager instead
    
    def add_media(self, media):
        if isinstance(media, _strings):
            media = self.open(media)
        if self.MediaList == None:
            logger_lib.warn("No MediaList loaded! Adding Media to new List")
            self.MediaList = self.Instance.media_list_new()
            self.ListPlayer.set_media_list(self.MediaList)
        self.MediaList.add_media(media)
        self._mediaListOverride = False
    
    def set_media_list(self, media_list):
        self.MediaList = media_list
        self.ListPlayer.set_media_list(media_list)
    
    def is_playing(self):
        return self.ListPlayer.is_playing() or self.MediaPlayer.is_playing()
