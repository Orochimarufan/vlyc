#!/usr/bin/python
#/*****************************************************************************
# * vlc::medialist
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

logger = logging.getLogger(__name__)


class MediaList(list):
    """
    Media Interface:
        get_event_manager()
        _as_parameter_
    """
    Event = vlcevent.MediaListEvent
    
    __logger = logger.getChild(__name__)
    
    def __init__(self, instance):
        self.m_instance = instance
        
        self.m_eventmanager = vlcevent.PyEventManager()
        self.m_eventmanager.register_event_types(self.Event.values())
        
        super(MediaList, self).__init__()
        
        self.m_media = None
        self.m_readonly = False
    
    def set_media(self, p_md):
        """ set the active media """
        if hasattr(self.m_media, "release"):
            self.m_media.release()
        if hasattr(p_md, "retain"):
            p_md.retain()
        self.m_media = p_md
    
    def media(self):
        """ Get the active media """
        return self.m_media
    
    def count(self):
        """ the lenght of this MediaList """
        return len(self)
    
    def add_media(self, p_md):
        """ Append a Media to the MediaList """
        if not self._can_write():
            return -1
        self._add_media(p_md)
        return 0
    
    def _add_media(self, p_md):
        if hasattr(p_md, "retain"):
            p_md.retain()
        self._notify_item_addition(p_md, len(self), False)
        self.append(p_md)
        self._notify_item_addition(p_md, len(self) - 1, True)
    
    def insert_media(self, p_md, index):
        """ Insert a Media at a specific Index """
        if not self._can_write():
            return -1
        self._insert_media(p_md, index)
        return 0
    
    def _insert_media(self, p_md, index):
        if hasattr(p_md, "retain"):
            p_md.retain()
        self._notify_item_addition(p_md, index, False)
        self.insert(index, p_md)
        self._notify_item_addition(p_md, index, True)
    
    def remove_index(self, index):
        """ remove a index from the list """
        if not self._can_write():
            return -1
        return self._remove_index(self, index)
    
    def _remove_index(self, index):
        if index < 0 or index >= len(self):
            #TODO: printerr
            return -1
        
        p_md = self[index]
        self._notify_item_deletion(p_md, index, False)
        self.pop(index)
        self._notify_item_deletion(p_md, index, True)
        
        if hasattr(p_md, "release"):
            p_md.release()
        
        return 0
    
    def item_at_index(self, index):
        """ get the item at index """
        return self[index]
    
    def index_of_item(self, p_md):
        """ get the index of the item """
        return self.index(p_md)
    
    def is_readonly(self):
        """ whether this MediaList is read-only """
        return self.m_readonly
    
    def lock(self):
        """ stub, python lists handle it """
        pass
    
    def unlock(self):
        """ stub, python lists handle it """
        pass
    
    def get_event_manager(self):
        """ get the event manager for this MediaList """
        return self.m_eventmanager
    
    # Private
    def _notify_item_addition(self, p_md, index, event_happened):
        event = vlcevent.VlcEvent()
        
        if event_happened:
            event.type = self.Event.ItemAdded
            event.u.media_list_item_added.item = p_md
            event.u.media_list_item_added.index = index
        else:
            event.type = self.Event.WillAddItem
            event.u.media_list_will_add_item.item = p_md
            event.u.media_list_will_add_item.index = index
        
        self.m_eventmanager.send(event)
    
    def _notify_item_deletion(self, p_md, index, event_happened):
        event = vlcevent.VlcEvent()
        
        if event_happened:
            event.type = self.Event.ItemDeleted
            event.u.media_list_item_deleted.item = p_md
            event.u.media_list_item_deleted.index = index
        else:
            event.type = self.Event.WillDeleteItem
            event.u.media_list_will_delete_item.item = p_md
            event.u.media_list_will_delete_item.index = index
        
        self.m_eventmanager.send(event)
