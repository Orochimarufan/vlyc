"""
/*****************************************************************************
 * vlcevent.py : VLC Event Handling Wrapper Re-Implementation
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
import ctypes
from collections import defaultdict
from . import libvlc
from . import util

logger = logging.getLogger("vlc.vlcevent")

#Event Contents
class _eu_media_list_item_changed(ctypes.Structure):
    _fields_ = [("item",ctypes.c_void_p),
                ("index",ctypes.c_long)]

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
        # MediaList
        ('media_list_item_added',       _eu_media_list_item_changed),
        ('media_list_will_add_item',    _eu_media_list_item_changed),
        ('media_list_item_deleted',     _eu_media_list_item_changed),
        ('media_list_will_delete_item', _eu_media_list_item_changed),
        # FIXME: SkippedMediaListView...
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
    
class BaseEventManager(object):
    """
    A Simple Event Manager
    """
    
    logger = logger.getChild("EventManager")
    
    def __init__(self):
        super(BaseEventManager,self).__init__()
        self.p_debug = None
        self.p_callbacks = defaultdict(list)
    
    def send(self,event):
        evt = event.type
        if self.p_debug is not None:
            self.p_debug(event)
        for cb in self.p_callbacks[evt]:
            cb(event)
    
    def connect(self,evt,cb):
        """
        Connect a Callback to an event
        
        @arg int    evt    event id
        @arg func   cb     callback
        
        Callback Signature:
            callback([object self,] VlcEvent event)
        """
        self.p_callbacks[evt].append(cb)
    
    def disconnect(self,evt,cb):
        """
        Disconnect a Callback from an event
        
        @arg int    evt    event id
        @arg func   cb     callback
        """
        self.p_callbacks[evt].remove(cb)
    
    def set_debug(self, func):
        """ The Debug Handler Will Receive all Events. None = Disabled """
        self.p_debug = func
    
    # event_attach
    # mainly for compatibility with libvlc_wrapper's one
    class ExtendedEventHandler(object):
        def __init__(self, callback, args, kwds):
            self.callback = callback
            self.args = args
            self.kwds = kwds
        def matches(self, callback, args, kwds):
            return self.callback == callback and self.args == args and self.kwds == kwds
        def __call__(self,event):
            return self.callback(event,*self.args,**self.kwds)
    
    def event_attach(self, eventtype, callback, *args, **kwds):
        """
        Connect an Extended Callback to an event
        
        @arg int    eventtype    event id
        @arg func   callback     callback
        @args    ARGS            args to pass to callback after event
        @kwds    KWDS            kwds to pass to callback after event
        
        Callback Signature:
            callback([object self,] VlcEvent event, ARGS *args, KWDS *kwds)
        
        DO NOT USE THIS IF YOU DO NOT NEED ADDITIONAL ARGUMENTS!
        USE connect(evt,cb) INSTEAD! ITS FASTER.
        """
        self.connect (eventtype, self.ExtendedEventHandler(callback, args, kwds))
    
    def event_detach(self, eventtype, callback, *args, **kwds):
        """
        Disconnect an Extended Callback from an event
        
        @arg int    eventtype    event id
        @arg func   callback     callback
        @args    ARGS            [OPT] args passed to event_attach
        @kwds    KWDS            [OPT] kwds passed to event_attach
        
        remove the specified Extended Callback
        
        Warning:
            if neither ARGS nor KWDS are specified, all extended callbacks connected to
            eventtype and referring to the specified function will be removed!
        """
        if not args and not kwds:
            self.logger.warn("event_detach: No args given. removing all callback%ss from event %s"%(callback,Event.name(eventtype)))
            for cb in self.p_callbacks[eventtype]:
                if isinstance(cb, self.ExtendedEventHandler) and cb.callback == callback:
                    self.disconnect(eventtype, cb)

class PyEventManager(BaseEventManager):
    __logger = logger.getChild("PyEventManager")
    def __init__(self):
        super(PyEventManager,self).__init__()
        self.regEvents = []
    def register_event_type(self, evt):
        self.regEvents.append(evt)
    def register_event_types(self, evtlist):
        self.regEvents.extend(evtlist)
    def send(self, event):
        if len(self.regEvents)>0 and event.type not in self.regEvents:
            self.__logger.warn("Event Manager does not know about Event: %s (send)"%Event.name(event.type))
        super(PyEventManager,self).send(event)
    def connect(self, evt, cb):
        if len(self.regEvents)>0 and evt not in self.regEvents:
            self.__logger.warn("Event Manager does not know about Event: %s"%Event.name(evt))
        super(PyEventManager,self).connect(evt,cb)

class VlcEventManager(BaseEventManager):
    def __init__(self, player):
        """
        Event Manager for libvlc Objects.
        Usage:
            libvlc_<type>_event_manager(libvlc_<type> object)
            <LibvlcWrapperObject>.get_event_manager()
        """
        if isinstance(player,util._Ints):
            # PTR
            self.c_man_p = ctypes.c_void_p(player)
        elif isinstance(player, libvlc.EventManager):
            # libvlc_wrapper EventManager
            self.c_man_p = player._as_parameter_
        else:
            # libvlc_wrapper Player/Media/etc object
            self.c_man_p = player.event_manager()._as_parameter_
        
        super(VlcEventManager,self).__init__()
        self._haveEvent = list()
        d = ctypes.CFUNCTYPE(None, ctypes.POINTER(VlcEvent), ctypes.c_void_p)
        self._handler = d( lambda event, user_data: self._dispatch(event.contents) )
        self._as_parameter_ = self.c_man_p
    
    def _dispatch(self, event):
        if event.type is None:
            self.logger.warn("Got NULL Event")
            return
        if event.type not in self._haveEvent:
            self.logger.warn("Unrequested Event: %i"%event.type)
            return
        self.send(event)
    
    def _attach(self, evt):
        r = libvlc.dll.libvlc_event_attach(self.c_man_p, evt, self._handler, None)
        if r!=0: logger.getChild("EventManager").error("Could not attach event: %i"%evt)
        self._haveEvent.append(evt)
    
    def _detach(self, evt):
        r = libvlc.dll.libvlc_event_detach(self.c_man_p, evt, self._handler, None)
        if r!=0: logger.getChild("EventManager").warn("Could not detach event: %i"%evt)
        self._haveEvent.remove(evt)
    
    def connect(self, evt, slot):
        super(VlcEventManager,self).connect(evt,slot)
        if evt not in self._haveEvent:
            self._attach(evt)
    
    def disconnect(self, evt, slot):
        super(VlcEventManager,self).disconnect(evt,slot)
        if len(self.p_callbacks[evt])<1:
            self._detach(evt) 

#Event Mapping
Event = util.vlcenum(libvlc.EventType)
MediaEvent = util.Enum("media_event_e", 
             MetaChanged        = Event.MediaMetaChanged,           #?
             SubItemAdded       = Event.MediaSubItemAdded,          #?
             DurationChanged    = Event.MediaDurationChanged,       #?
             ParsedChanged      = Event.MediaParsedChanged,         #?
             Freed              = Event.MediaFreed,                 #?
             StateChanged       = Event.MediaStateChanged,          #?
             )
MediaPlayerEvent = util.Enum("media_player_event_e", 
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
MediaListEvent = util.Enum("media_list_event_e", 
             ItemAdded          = Event.MediaListItemAdded,         #?
             WillAddItem        = Event.MediaListWillAddItem,       #?
             ItemDeleted        = Event.MediaListItemDeleted,       #?
             WillDeleteItem     = Event.MediaListWillDeleteItem,    #?
             )
MediaListViewEvent = util.Enum("media_list_view_event_e", 
             ItemAdded          = Event.MediaListViewItemAdded,     #?
             WillAddItem        = Event.MediaListViewWillAddItem,   #?
             ItemDeleted        = Event.MediaListViewItemDeleted,   #?
             WillDeleteItem     = Event.MediaListViewWillDeleteItem,#?
             )
MediaListPlayerEvent = util.Enum("media_list_player_event_e", 
             Played             = Event.MediaListPlayerPlayed,      #?
             NextItemSet        = Event.MediaListPlayerNextItemSet, #?
             Stopped            = Event.MediaListPlayerStopped,     #?
             )
MediaDiscovererEvent = util.Enum("media_discoverer_event_e", 
             Started            = Event.MediaDiscovererStarted,     #?
             Ended              = Event.MediaDiscovererEnded,       #?
             )
VideoLanManagerEvent = util.Enum("video_lan_manager_event_e", 
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
#For Convenience
PyEventManager.Event = Event
PyEventManager.miEvent = miEvent = MediaEvent
PyEventManager.mpEvent = mpEvent = MediaPlayerEvent
PyEventManager.mlEvent = mlEvent = MediaListEvent
PyEventManager.lpEvent = lpEvent = MediaListPlayerEvent
PyEventManager.mdEvent = mdEvent = MediaDiscovererEvent

#build functions
class _fromc(object):
    """ Gets a C Function and wraps it """
    @staticmethod
    def _fromc(name,doc,cls,flags,types):
        f=ctypes.CFUNCTYPE(*types)((name,libvlc.dll),flags)
        def ec(r,f,a):
            if r is None: return r
            return cls(r)
        f.errcheck = ec
        f.__doc__ = doc
        return f
    def __init__(self,cls,flags,*types):
        self.cls = cls
        self.flags = flags
        self.types = types
    def __call__(self,func):
        return self._fromc(func.__name__, func.__doc__, self.cls, self.flags, self.types)

@_fromc(VlcEventManager, ((1,),), ctypes.c_void_p, libvlc.Media)
def libvlc_media_event_manager(p_md):
    '''Get event manager from media descriptor object.
    NOTE: this function doesn't increment reference counting.
    @param p_md: a media descriptor object.
    @return: event manager object.
    '''
@_fromc(VlcEventManager, ((1,),), ctypes.c_void_p, libvlc.MediaList)
def libvlc_media_list_event_manager(p_ml):
    '''Get libvlc_event_manager from this media list instance.
    The p_event_manager is immutable, so you don't have to hold the lock.
    @param p_ml: a media list instance.
    @return: libvlc_event_manager.
    '''
@_fromc(VlcEventManager, ((1,),), ctypes.c_void_p, libvlc.MediaListPlayer)
def libvlc_media_list_player_event_manager(p_mlp):
    '''Return the event manager of this media_list_player.
    @param p_mlp: media list player instance.
    @return: the event manager.
    '''
@_fromc(VlcEventManager, ((1,),), ctypes.c_void_p, libvlc.MediaPlayer)
def libvlc_media_player_event_manager(p_mi):
    '''Get the Event Manager from which the media player send event.
    @param p_mi: the Media Player.
    @return: the event manager associated with p_mi.
    '''
@_fromc(VlcEventManager, ((1,),), ctypes.c_void_p, libvlc.Instance)
def libvlc_vlm_get_event_manager(p_instance):
    '''Get libvlc_event_manager from a vlm media.
    The p_event_manager is immutable, so you don't have to hold the lock.
    @param p_instance: a libvlc instance.
    @return: libvlc_event_manager.
    '''
@_fromc(VlcEventManager, ((1,),), ctypes.c_void_p, libvlc.MediaDiscoverer)
def libvlc_media_discoverer_event_manager(p_mdis):
    '''Get event manager from media service discover object.
    @param p_mdis: media service discover object.
    @return: event manager object.
    '''

# Monkey patch it in!
# We cannot assign it directly because of the lacking instance-method-support in ctypes.
# hence, the lambda constructs
libvlc.Media.get_event_manager = lambda s: libvlc_media_event_manager(s)
libvlc.MediaList.get_event_manager = lambda s: libvlc_media_list_event_manager(s)
libvlc.MediaListPlayer.get_event_manager = lambda s: libvlc_media_list_player_event_manager(s)
libvlc.MediaPlayer.get_event_manager = lambda s: libvlc_media_player_event_manager(s)
libvlc.MediaDiscoverer.get_event_manager = lambda s: libvlc_media_discoverer_event_manager(s)
libvlc.Instance.vlm_get_event_manager2 = lambda s: libvlc_vlm_get_event_manager(s)
#EOF