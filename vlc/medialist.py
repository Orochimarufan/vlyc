"""
/*****************************************************************************
 * medialist.py : libvlc MediaList(Player) re-implementation
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

from __future__ import unicode_literals, absolute_import
import logging
import threading
from . import libvlc
from . import vlcevent

logger = logging.getLogger("vlc.medialist")

class MediaList(object):
    logger = logger.getChild("MediaList")
    def __init__(self, p_inst):
        self.p_libvlc_instance = p_inst
        self.p_libvlc_event_manager = vlcevent.PyEventManager(p_inst)
        self.b_read_only = False
        #No Event Registration Needed (as of now)
        self.object_lock = threading.Lock()
        self.items = list()
        self.p_md = None
        #--------------------------------------
        #Not really necessary
        self.refcount_lock = threading.Lock()
        self.i_refcount = 1
    def retain(self):
        self.refcount_lock.aquire()
        self.i_refcount+=1
        self.refcount_lock.release()
    def release(self):
        self.refcount_lock.aquire()
        self.i_refcount-=1
        if self.i_refcount<0:
            self.logger.warn("Refcount<0!")
        self.refcount_lock.release()
    #add_file_content(psz_uri) : How to implement?
    def set_media(self,p_md):
        with self.object_lock:
            if self.p_md is not None:
                self.p_md.release()
                p_md.retain()
                self.p_md=p_md
    def media(self):
        """
         * If this media_list comes is a media's subitems,
         * This holds the corresponding media.
         * This md is also seen as the information holder for the media_list.
         * Indeed a media_list can have meta information through this
         * media.
        """
        with self.object_lock:
            if self.p_md:
                return self.p_md
    def count(self):
        """ Lock should be held when entering """
        return len(self.items)
    def add_media(self,p_md):
        """ Lock should be held when entering """
        if not self.b_read_only:
            p_md.retain()
            self.notify_item_addition(p_md,self.count(),False)
            self.items.append(p_md)
            self.notify_item_addition(p_md,self.count()-1,True)
            return True
        return False
    def insert_media(self,p_md,index):
        """ Lock should be held when entering """
        if not self.b_read_only:
            p_md.retain()
            self.notify_item_addition(p_md,index,False)
            self.items.insert(index,p_md)
            self.notify_item_addition(p_md,index,True)
            return True
        return False
    def remove_index(self,index):
        """ Lock should be held when entering """
        if not self.b_read_only:
            p_md = self.items[index]
            self.notify_item_deletion(p_md,index,False)
            self.items.pop(index)
            self.notify_item_deletion(p_md,index,True)
            p_md.release()
            return True
        return False
    def item_at_index(self,index):
        """ Lock should be held when entering """
        p_md = self.items[index]
        p_md.retain()
        return p_md
    def index_of_item(self,p_searched_md):
        """
        Lock should be held when entering
        Warning: Returns first matching item
        """
        return self.items.index(p_searched_md)
    def is_readonly(self):
        return self.b_read_only
    def lock(self):
        return self.object_lock.aquire()
    def unlock(self):
        return self.object_lock.release()
    def event_manager(self):
        """ Event Manager is immutable, so lock neednt be held """
        return self.p_libvlc_event_manager
    
    #Private
    def notify_item_addition(self,p_md,index,finished):
        event = vlcevent.VlcEvent()
        if finished:
            event.type = vlcevent.mlEvent.ItemAdded
            event.u.media_list_item_added.item = p_md
            event.u.media_list_item_added.index = index
        else:
            event.type = vlcevent.mlEvent.WillAddItem
            event.u.media_list_will_add_item.item = p_md
            event.u.media_list_will_add_item.index = index
        self.p_libvlc_event_manager.fire(event)
    def notify_item_deletion(self,p_md,index,finished):
        event = vlcevent.VlcEvent()
        if finished:
            event.type = vlcevent.mlEvent.ItemDeleted
            event.u.media_list_item_deleted.item = p_md
            event.u.media_list_item_deleted.index = index
        else:
            event.type = vlcevent.mlEvent.WillDeleteItem
            event.u.media_list_will_delete_item.item = p_md
            event.u.media_list_will_delete_item.index = index
        self.p_libvlc_event_manager.send(event)

class MediaListPlayer(object):
    def __init__(self):
        pass
    def lock(self):
        self.object_lock.aquire()
        self.mp_callback_lock.aquire()
    def unlock(self):
        self.mp_callback_lock.release()
        self.object_lock.release()
    def assert_locked(self):
        pass
    