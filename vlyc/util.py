"""
/*****************************************************************************
 * util.py : Utilities for VLYC
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

import sys

class Enum(object):
    def __init__(self,name,**vals):
        self.__vals__ = vals
        self.__name__ = name
        self.export(self.__dict__)
    def __str__(self):
        return "Enum %s: %s"%(self.__name__,", ".join(self.__vals__.keys()))
    def __repr__(self):
        return "Enum('%s', %s)"%(self.__name__,", ".join(["%s=%s"%(n,str(v)) for n,v in self.__vals__.items()]))
    def __contains__(self,other):
        return other in self.__vals__.values()
    def __instancecheck__(self,other):
        return other in self
    def export(self,ns=None):
        """ Export Enum values to another Namespace (like in C) """
        if ns is None:
            ns = sys._getframe(0).f_back.f_locals
        for n,v in self.__vals__.items():
            ns[n]=v
    def get(self,name,default=None):
        return self.__vals__.get(name,default)
    def values(self):
        return self.__vals__.values()
    def items(self):
        return self.__vals__.items()
    def keys(self):
        return self.__vals__.keys()
    def name(self, i):
        for n, v in self.items():
            if v==i: return n
        return str(i)

class AutoEnum(Enum):
    def __init__(self,name,*vals,**vals3):
        vals2 = dict()
        for i in range(len(vals)):
            vals2[vals[i]]=i
        vals2.update(vals3)
        super(AutoEnum,self).__init__(name,**vals2)

class OnObject(object):
    """
    Decorator:
        class C(object): pass
        @OnObject(C)
        def my_func(self):
            print("something");
        C().my_func() -> something
    """
    def __init__(self, target):
        self.target = target;
    def __call__(self, fnc):
        setattr(self.target,fnc.__name__,fnc);

def secstotimestr(i_secs,b_hrs=False):
    mins = i_secs//60; secs = i_secs%60
    if b_hrs:
        hrs = mins//60; mins%=60
        return "{0:02.0f}:{1:02.0f}:{2:02.0f}".format(hrs,mins,secs)
    else:
        return "{0:02.0f}:{1:02.0f}".format(mins,secs)
