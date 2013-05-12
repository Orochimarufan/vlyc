"""
/*****************************************************************************
 * vlc :: util.py : Utilities
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

#/--------------------------------------------------------------------------------\
#| Enum                                                                           |
#+--------------------------------------------------------------------------------+
#| Provides C-Style Enums                                                         |
#\--------------------------------------------------------------------------------/
import sys


class Enum(object):
    def __init__(self, name, _inherits=None, _dict=None, **vals):
        # import the _dict
        if _dict is not None:
            if not vals:
                vals = _dict
            else:
                vals.update(_dict)
        
        # do inheritance
        if (_inherits):
            self.__vals__ = dict(_inherits.__vals__)
            self.__vals__.update(vals)
        else:
            self.__vals__ = vals
        
        self.__name__ = name
        
        # export values into Instance dict
        self.export(self.__dict__)
    
    def __str__(self):
        return "Enum %s: %s" % (self.__name__, ", ".join(self.__vals__.keys()))
    
    def __repr__(self):
        return "Enum('%s', %s)" % (self.__name__, ", ".join(
                ["%s=%s" % (n, str(v)) for n, v in sorted(self.__vals__.items(), key=lambda i: i[1])]))
    
    def __contains__(self, other):
        return other in self.__vals__.values()
    
    def __instancecheck__(self, other):
        return other in self
    
    def export(self, ns=None):
        """ Export Enum values to another Namespace (like in C) """
        if (ns is None):
            ns = sys._getframe(0).f_back.f_locals
        for n, v in self.__vals__.items():
            ns[n] = v
    
    def get(self, name, default=None):
        return self.__vals__.get(name, default)
    
    def values(self):
        return self.__vals__.values()
    
    def items(self):
        return self.__vals__.items()
    
    def keys(self):
        return self.__vals__.keys()
    
    def name(self, i):
        for n, v in self.items():
            if (v == i):
                return n
        return str(i)


class AutoEnum(Enum):
    def __init__(self, name, *vals, _inherits=None, _startat=None, _dict=None, **vals3):
        vals2 = dict()
        
        # find the highest number in the inherited Enum and start there,
        # if no startat was given
        if _startat is None:
            if _inherits is not None:
                _startat = max(_inherits.values()) + 1
            else:
                _startat = 0
        
        # insert positionals
        for i in range(len(vals)):
            vals2[vals[i]] = i + _startat
        # insert keywords
        vals2.update(vals3)
        # insert _dict
        if _dict is not None:
            vals2.update(_dict)
        
        super(AutoEnum, self).__init__(name, _inherits=_inherits, _dict=vals2)

#convert a libvlc Enum to our one
vlcenum = lambda enum: Enum(enum.__name__, **dict([(n, v) for v, n in enum._enum_names_.items()]))


#/--------------------------------------------------------------------------------\
#| Py3k Stuff                                                                     |
#+--------------------------------------------------------------------------------+
#| Some Defs for Python2 / Python3 differences                                    |
#\--------------------------------------------------------------------------------/
def _typeconv(n, t, *a):
    """ Helper to create Type converters """
    def typeconv(d):
        if (not isinstance(d, t)):
            d = t(d, *a)
        return d
    typeconv.__name__ = n
    return typeconv

if (sys.hexversion > 0x3000000):
    _Ints       = int
    _Strings    = str
    vlcstring   = _typeconv("vlcstring", bytes, "UTF-8")
    pystring    = _typeconv("pystring", str, "UTF-8")
else:
    _Ints       = int, long #@UndefinedVariable
    _Strings    = unicode, str #@UndefinedVariable
    vlcstring   = _typeconv(str("vlcstring"), str, "utf8")
    pystring    = _typeconv(str("pystring"), unicode, "utf8") #@UndefinedVariable
