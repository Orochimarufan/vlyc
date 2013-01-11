"""
/*****************************************************************************
 * vlyc :: settings.py : VLYC Settings class
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

from PyQt4 import QtCore
from .util import Singleton


class QSProxy(object):
    def __init__(self, qs_inst, fk):
        object.__setattr__(self, "parent", qs_inst)
        object.__setattr__(self, "fcat", fk)
    
    def __getitem__(self, key):
        if (isinstance(key, slice)):
            return self.parent.value("/".join((self.fcat, key.start)), key.stop)
        return self.parent.value("/".join((self.fcat, key)))
    
    def __getattr__(self, key):
        return self.parent.value("/".join((self.fcat, key)))
    
    def __setitem__(self, key, value):
        return self.parent.setValue("/".join((self.fcat, key)), value)
    
    __setattr__ = __setitem__


@Singleton
class Settings(object):
    _cx = staticmethod(lambda c, k: "/".join((c, k)))
    
    def __init__(self, *a, **b):
        self.qsettings = QtCore.QSettings(*a, **b)
    
    def __getattr__(self, fcat):
        try:
            return getattr(self.qsettings, fcat)
        except AttributeError:
            return QSProxy(self, fcat)
    
    def __getitem__(self, key):
        if (isinstance(key, slice)):
            return self.value(self._cx(key.start, key.stop), key.step)
        return QSProxy(self, key)
    
    def __setitem__(self, key, value):
        if (isinstance(key, slice)):
            return self.setValue(self._cx(key.start, key.stop), value)
        raise ValueError("SetItem Syntax: Settings[category:key]=value")
