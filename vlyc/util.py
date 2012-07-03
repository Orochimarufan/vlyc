"""
/*****************************************************************************
 * vlyc :: util.py : Utilities for VLYC
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
from vlc.util import Enum,AutoEnum

class OnObject(object):
    """
    Decorator:
        class C(object): pass
        @OnObject(C)
        def my_func(self):
            print("something");
        C().my_func() -> something
    """
    def __init__(self, target, targetName=None):
        self.target = target;
        self.name = targetName;
    def __call__(self, fnc):
        if not self.name:
            name = fnc.__name__
        else:
            name = self.name
        setattr(self.target,name,fnc);

def secstotimestr(i_secs,b_hrs=False):
    mins = i_secs//60; secs = i_secs%60
    if b_hrs:
        hrs = mins//60; mins%=60
        return "{0:02.0f}:{1:02.0f}:{2:02.0f}".format(hrs,mins,secs)
    else:
        return "{0:02.0f}:{1:02.0f}".format(mins,secs)

class WithMeta(object):
    def __init__(self,meta):
        self.meta = meta
    def __call__(self,klass):
        return self.meta(klass.__name__,klass.__bases__,dict(klass.__dict__))
