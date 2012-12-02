"""
/*****************************************************************************
 * vlc :: playerex.py : VLC Interface
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
import threading
import random
from . import player
from . import libvlc
from . import vlcevent
from . import util

logger = logging.getLogger("vlc.playerex")

PlaybackMode = util.vlcenum(libvlc.PlaybackMode)

LPlayerEvent = util.Enum("LPlayerEvent", _inherits=vlcevent.lpEvent,
                         Ended=0x1000, PrepareNextItem=0x1001)


#Helps
def _retainItem(item):
    if (hasattr(item, "retain")):
        item.retain()
    return item


def _releaseItem(item):
    if (hasattr(item, "release")):
        item.release()
    return item


class MediaEx(object):
    """
    A Data Container that dynamically creates Media Objects
    """
    
    __logger = logger.getChild("MediaEx")
    
    def __init__(self, instance, mrl):
        self.Instance = instance
        self.mrl    = mrl
        self.meta   = dict()
        self.user_data = None
    
    @property
    def media(self):
        """ Simple Media object generation """
        if (":" in self.mrl and self.mrl.index(":") > 1):
            media = self.Instance.media_new_location(util.vlcstring(self.mrl))
        else:
            media = self.Instance.media_new_path(util.vlcstring(self.mrl))
        #Apply meta
        for k, v in self.meta.items():
            media.set_meta(k, util.vlcstring(v))
        return media
    
    def __getitem__(self, meta):
        return self.meta[meta]
    
    def __setitem__(self, meta, value):
        self.meta[meta] = value
    
    def __delitem__(self, meta):
        del self.meta[meta]
    
    def set_meta(self, meta, value):
        if (value is None):
            if (meta in self.meta):
                del self[meta]
            return
        self[meta] = value
    
    def get_meta(self, meta):
        return self[meta]
    
    def set_user_data(self, data):
        self.user_data = data
    
    def get_user_data(self):
        return self.user_data
    
    def get_mrl(self):
        return self.mrl
    
    def get_instance(self):
        return self.Instance


class DLock:
    def acquire(self):
        return
    
    def release(self):
        return
    
    def __enter__(self):
        return
    
    def __exit__(self, *a):
        return


class MediaListL(list):
    """
    Container to hold multiple
    MediaEx and/or Media objects
    """
    
    __logger = logger.getChild("MediaListL")
    
    def __init__(self):
        self.p_lock = threading.RLock()
        self.p_event_manager = vlcevent.PyEventManager()
    
    #Append
    def append(self, media):
        with self.p_lock:
            super(MediaListL, self).append(_retainItem(media))
    
    def add_media(self, media):
        super(MediaListL, self).append(_retainItem(media))
    
    #Insert
    def insert(self, index, media):
        with self.p_lock:
            super(MediaListL, self).insert(index, _retainItem(media))
    
    def insert_media(self, media, index):
        super(MediaListL, self).insert(index, _retainItem(media))
    
    #Public locking
    def lock(self):
        self.p_lock.acquire()
    
    def unlock(self):
        self.p_lock.release()
    
    #Length
    def __len__(self):
        with self.p_lock:
            return super(MediaListL, self).__len__()
    
    def count(self):
        return super(MediaListL, self).__len__()
    
    #Get
    def __getitem__(self, index):
        with self.p_lock:
            return _retainItem(super(MediaListL, self).__getitem__(index))
    
    def item_at_index(self, index):
        return _retainItem(super(MediaListL, self).__getitem__(index))
    
    #Remove
    def __delitem__(self, index):
        with self.p_lock:
            _releaseItem(super(MediaListL, self).__getitem__(index))
            super(MediaListL, self).__delitem__(index)
        
    def remove_index(self, index):
        _releaseItem(super(MediaListL, self).__getitem__(index))
        super(MediaListL, self).__delitem__(index)
    
    #Index
    def index(self, media):
        with self.p_lock:
            return super(MediaListL, self).index(media)
    
    def index_of_item(self, media):
        return super(MediaListL, self).index(media)
    
    def event_manager(self):
        return self.p_event_manager
    get_event_manager = event_manager


class LPlayer1(player.Player):
    """
    Adds Capabilities of MediaListPlayer to Player.
    
    This class does not use libvlc.MediaListPlayer internally. to do that, use the CPlayer class!
    
    This class is used to playback player.MediaListL objects. NOT libvlc.MediaList ones!
    """
    
    __logger = logger.getChild("LPlayer")
    
    nextItem = player.Signal("PyQt_PyObject")
    
    #/-------------------------------------------------------
    # Constructor
    #-------------------------------------------------------/
    def __init__(self, instance=None):
        super(LPlayer1, self).__init__(instance)
        
        self.MediaList          = None
        
        self.p_items            = None
        self.e_playback_mode    = PlaybackMode.default
        
        self.ListPlayerManager   = vlcevent.PyEventManager()
        self.ListPlayerManager.register_event_type(LPlayerEvent.NextItemSet)
        self.ListPlayerManager.register_event_type(LPlayerEvent.PrepareNextItem)
        
        self.np_index = -1
        self.np_item = None
        self.np_media = None
    
    #/-------------------------------------------------------
    # VLC Event Callbacks
    #-------------------------------------------------------/
    def vlcevent_end(self, event):
        super(LPlayer1, self).vlcevent_end(event)
        if (self.MediaList.count() > self.np_index):
            self.set_relative_playlist_position_and_play(1)
        else:
            event = vlcevent.VlcEvent()
            event.type = LPlayerEvent.Ended
            self.ListPlayerManager.send(event)
    
    def mlistevent_deleted(self, event):
        pass #Nothing
    
    #/-------------------------------------------------------
    # Private
    #-------------------------------------------------------/
    def install_playlist_observer(self):
        self.MediaListManager = self.MediaList.get_event_manager()
        #Install Work
    
    def uninstall_playlist_observer(self):
        #Uninstall Work
        self.MediaListManager = None
    # We don't need the player_observer stuff since we got the player internal.
    
    #/-------------------------------------------------------
    # Methods / Slots
    #-------------------------------------------------------/
    def set_media_list(self, p_ml):
        """ Set the used MediaList or MediaListL """
        if (self.MediaList):
            self.uninstall_playlist_observer()
            _releaseItem(self.MediaList)
        self.MediaList = _retainItem(p_ml)
        self.install_playlist_observer()
    
    def play(self):
        """ Play """
        if (not self.np_media):
            self.set_relative_playlist_position_and_play(1)
        else:
            self.MediaPlayer.play()
    
    def pause(self):
        """ Pause """
        self.MediaPlayer.pause()
    
    def is_playing(self):
        return self.MediaPlayer.get_state() in \
            (self.State.Opening, self.State.Buffering, self.State.Playing)
    
    # get_state is taken directly from the MediaPlayer
    
    def play_item_at_index(self, index):
        item = self.MediaList[index]
        self.set_current_playing(index, item)
        self.MediaPlayer.play()
    
    def set_current_playing(self, index, item):
        self.np_index = index
        self.np_item  = item
        if (isinstance(item, MediaEx)):
            self.np_media = item.media
        else:
            self.np_media = item
        self.MediaPlayer.set_media(self.np_media)
        event = vlcevent.VlcEvent()
        event.type = LPlayerEvent.NextItemSet
        event.u.media = self.np_media._as_parameter_
        self.ListPlayerManager.send(event)
    
    def play_item(self, item):
        self.MediaList.lock()
        if (item not in self.MediaList):
            return -1
        self.set_current_playing(self.MediaList.index_of_item(item), item)
        self.MediaList.unlock()
        self.MediaPlayer.play()
    
    def play_random(self):
        self.MediaList.lock()
        i = random.randrange(self.MediaList.count())
        self.MediaList.unlock()
        self.play_item_at_index(i)
    
    def stop(self):
        self.MediaPlayer.stop()
        self.np_index = -1
        self.np_item = None
        self.np_media = None
    
    def set_relative_playlist_position_and_play(self, rpos):
        i = self.np_index + rpos
        self.play_item_at_index(i)
    
    def next(self): #@ReservedAssignment
        self.set_relative_playlist_position_and_play(1)
    
    def previous(self):
        self.set_relative_playlist_position_and_play(-1)
    
    def set_playback_mode(self, mode):
        self.e_playback_mode = mode
    
    def set_media(self, media):
        l = MediaListL()
        l.add_media(media)
        self.set_media_list(l)
    
    def add_media(self, media):
        self.MediaList.lock()
        self.MediaList.add_media(media)
        self.MediaList.unlock()