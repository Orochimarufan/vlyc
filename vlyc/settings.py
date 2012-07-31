
from __future__ import absolute_import, unicode_literals

from PyQt4 import QtCore
from .util import QSingleton

class QSProxy(object):
    def __init__(self,qs_inst,fk):
        object.__setattr__(self,"parent",qs_inst)
        object.__setattr__(self,"fcat",fk)
    def __getitem__(self,key):
        if isinstance(key,slice):
            return self.parent.value(self.fcat+"/"+key.start, key.stop)
        return self.parent.value(self.fcat+"/"+key)
    def __getattr__(self,key):
        return self.parent.value(self.fcat+"/"+key)
    def __setitem__(self,key,value):
        return self.parent.setValue(self.fcat+"/"+key,value)
    __setattr__ = __setitem__

@QSingleton
class Settings(QtCore.QSettings):
    _cx = staticmethod(lambda c,k: "/".join((c,k)))
    def __getattr__(self, fcat):
        return QSProxy(self,fcat)
    def __getitem__(self, key):
        if isinstance(key,slice):
            return self.value(self._cx(key.start,key.stop),key.step)
        return QSProxy(self,key)
    def __setitem__(self, key, value):
        if isinstance(key,slice):
            return self.setValue(self._cx(key.start,key.stop),value)
        raise ValueError("SetItem Syntax: Settings[category:key]=value")

