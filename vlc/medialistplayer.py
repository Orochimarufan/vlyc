#!/usr/bin/python
#/*****************************************************************************
# * vlyc::medialistplayer
# ****************************************************************************
# * Copyright (C) 2012-2013 Orochimarufan
# *
# * Authors:  Orochimarufan <orochimarufan.x3@gmail.com>
# *
# * This program is free software: you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation, either version 3 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program.  If not, see <http://www.gnu.org/licenses/>.
# *****************************************************************************/
# $created 18 Feb 2013 $

from __future__ import unicode_literals, absolute_import

import logging

from . import vlcevent
from . import libvlc
from . import util

logger = logging.getLogger(__name__)


class MediaListPlayer(object):
    Event = vlcevent.MediaListPlayerEvent
    PlaybackMode = util.AutoEnum("PlaybackMode", "single", _inherits=util.vlcenum(libvlc.PlaybackMode))
    
    __logger = logger.getChild(__name__)
    
    def __init__(self, instance):
        self.m_instance = instance
        
        self.m_eventmanager = vlcevent.PyEventManager()
        self.m_eventmanager.register_event_types(self.Event)
        
        self.m_medialist = None
        
        self.m_mediaplayer = None
        
        instance.retain()
        
        self.m_playback_mode = self.PlaybackMode.single
    
    def get_event_manager(self):
        return self.m_eventmanager
    
    def set_media_list(self, p_ml):
        if self.m_medialist is not None:
            if hasattr(self.m_medialist, "release"):
                self.m_medialist.release()
        if hasattr(p_ml, "retain"):
            p_ml.retain()
        
        self.m_medialist = p_ml
    
    def media_list(self):
        return self.m_medialist
    
    def set_media_player(self, p_mp):
        if self.m_mediaplayer is not None:
            self._mplayer_em().disconnect(vlcevent.MediaPlayerEvent.EndReached, self._on_end_reached)
            if hasattr(self.m_mediaplayer, "release"):
                self.m_mediaplayer.release()
        if hasattr(p_mp, "retain"):
            p_mp.retain()
        
        self.m_mediaplayer = p_mp
        
        self._mplayer_em().connect(vlcevent.MediaPlayerEvent.EndReached, self._on_end_reached)
    
    def set_playback_mode(self, e_mode):
        if not isinstance(e_mode, self.PlaybackMode):
            return -1
        self.m_playback_mode = e_mode
        return 0
    
    def play(self):
        self.m_mediaplayer.play()
    
    def pause(self):
        self.m_mediaplayer.pause()
    
    def stop(self):
        self.m_mediaplayer.stop()
    
    # private
    def _on_end_reached(self):
        next_media = self._next()
        if next_media is not None:
            event = vlcevent.VlcEvent()
            event.type = self.Event.NextItemSet
            event.u.media_list_player_next_item_set.item = next_media
            self.m_eventmanager.send(event)
            self.m_mediaplayer.set_media(next_media)
            self.m_mediaplayer.play()
        else:
            event = vlcevent.VlcEvent()
            event.type = self.Event.Stopped
            self.m_eventmanager.send(event)
        
    def _mlist_em(self):
        return self.m_medialist.get_event_manager()
    
    def _mplayer_em(self):
        return self.m_mediaplayer.get_event_manager()
    
    def _next(self, noloop=False):
        if self.m_playback_mode != self.PlaybackMode.repeat or noloop:
            if self.m_playback_mode == self.PlaybackMode.single:
                return None
            i = self.m_medialist.index_of_item(self.m_mediaplayer.media()) + 1
            if i >= self.m_medialist.count():
                if self.m_playback_mode == self.PlaybackMode.loop:
                    return self.m_medialist.item_at_index(0)
                else:
                    return None
            else:
                return self.m_medialist.item_at_index(i)
        else:
            return self.m_mediaplayer.media()
