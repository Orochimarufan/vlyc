"""
/*****************************************************************************
 * vlyc :: __init__.py : VLYC Package Init, Version Info
 ****************************************************************************
 * Copyright (C) 2012-2013 Orochimarufan
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

version_info = (0, 1, 8)
codename = "Twoflower"
version = "0.1.8 Twoflower"
date = (2013, 1, 12)

# import Qt
# PySide is broken right now, QStyle.drawComplexControl() gets wrong QStyleOptionComplex Subclass
#import sys
#try:
#    from PySide import QtCore, QtGui
#except ImportError:
import sip
sip.setapi("QString", 2)
sip.setapi("QVariant", 2)
from PyQt4 import QtCore
QtCore.Signal = QtCore.pyqtSignal
QtCore.Slot = QtCore.pyqtSlot
QtCore.Property = QtCore.pyqtProperty
#else:
#    sys.modules['PyQt4'] = sys.modules['PySide']
#    QtCore.pyqtSignal = QtCore.Signal
#    QtCore.pyqtSlot = QtCore.Slot
#    QtCore.pyqtProperty = QtCore.Property
