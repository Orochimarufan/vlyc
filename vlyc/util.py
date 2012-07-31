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
if __debug__:
    import sys
    import traceback
from PyQt4 import QtCore

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

class _Singleton(type):
    """Singleton MetaClass."""
    
    def __init__(cls,name,bases,dct):
        super(_Singleton,cls).__init__(name,bases,dct)
        cls._Singleton_Instance = None
        if __debug__:
            cls._Singleton_Frame = None
    
    def __call__(cls,*args,**kwds):
        if cls._Singleton_Instance is None:
            cls.__create__(*args,**kwds)
        return cls._Singleton_Instance
    
    def __create__(cls,*args,**kwds):
        if __debug__:
            cls._Singleton_Frame = sys._getframe(2) #if everythin's right, the user's code is 2 frames away.
        cls._Singleton_Instance = super(_Singleton,cls).__call__(*args,**kwds)
    
    def Instance(cls):
        if cls._Singleton_Instance is None:
            raise RuntimeError("Singleton '%s' was not initialized."%cls.__name__)
        return cls._Singleton_Instance
    
    def Init(cls,*args,**kwds):
        if cls._Singleton_Instance is not None:
            if __debug__:
                raise RuntimeError("Singleton '%s' already initialized\nFirst Initialization at '%s' Line %i:\n%s"%
                    (cls.__name__,cls._Singleton_Frame.f_code.co_filename,cls._Singleton_Frame.f_lineno,
                    "\n".join(traceback.format_stack(cls._Singleton_Frame))))
            raise RuntimeError("Singleton '%s' already initialized")
        else:
            cls.__create__(*args,**kwds)
            return cls._Singleton_Instance
    
    def _DELETE_(cls):
        cls._Singleton_Instance = None

Singleton = WithMeta(_Singleton)

class _QSingleton(QtCore.pyqtWrapperType,_Singleton):
    #PyQt's Meta Wrapper doesn't hand down __init__.
    def __init__(cls,name,bases,dct):
        super(_QSingleton,cls).__init__(name,bases,dct)
        cls._Singleton_Instance = None
        if __debug__:
            cls._Singleton_Frame = None

QSingleton = WithMeta(_QSingleton)
