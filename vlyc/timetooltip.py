"""
/*****************************************************************************
 * vlyc :: timetooltip.py : TimeTooltip to hover over the SeekBar
 ****************************************************************************
 * Copyright © 2011 VideoLAN
 * $Id: af1036849d6fb7023915ae4e29b2ee9824fe2d88 $
 *
 * Authors: Ludovic Fauvet <etix@l0cal.com>
 *          Orochimarufan <orochimarufan.x3@gmail.com> [Python]
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
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.
 *****************************************************************************/
"""

from __future__ import absolute_import, unicode_literals
from PyQt4 import QtCore, QtGui
from .const import TIP_HEIGHT
from sys import platform


class TimeTooltip(QtGui.QWidget):
    SIG = """
public:
    explicit TimeTooltip( QWidget *parent = 0 )
    void setTip( const QPoint& pos, const QString& time, const QString& text )
    virtual void show()
protected:
    virtual void paintEvent( QPaintEvent * )
private:
    void adjustPosition()
    void buildPath()
    QPoint mTarget
    QString mTime
    QString mText
    QString mDisplayedText
    QFont mFont
    QRect mBox
    QPainterPath mPainterPath
    QBitmap mMask
    int mTipX
    bool mInitialized
    """
    
    def __init__(self, parent=0):
        super(TimeTooltip, self).__init__(parent)
        self.mInitialized = False
        
        self.setWindowFlags(QtCore.Qt.Window |\
                            QtCore.Qt.WindowStaysOnTopHint |\
                            QtCore.Qt.FramelessWindowHint |\
                            QtCore.Qt.X11BypassWindowManagerHint)
        self.setAttribute(QtCore.Qt.WA_OpaquePaintEvent)
        if (platform == "win32"):
            self.setAttribute(98) # Not in PyQt4? QtCore.Qt.WA_ShowWindowWithoutActivating
        self.mFont = QtGui.QFont("Verdana", max(self.font().pointSize() - 5, 7))
        self.mTipX = -1
        self.mTarget = None
        self.mTime = None
        self.mText = None
        self.mBox = None
    
    def adjustPosition(self):
        #Get the bounding box required to print the text and add some padding
        metrics = QtGui.QFontMetrics(self.mFont)
        textbox = metrics.boundingRect(self.mDisplayedText)
        textbox.adjust(-2, -2, 2, 2)
        textbox.moveTo(0, 0)
        
        #Resize the widget to fit our needs
        size = QtCore.QSize(textbox.width() + 1, textbox.height() + TIP_HEIGHT + 1)
        
        #The desired label position is just above the target
        position = QtCore.QPoint((self.mTarget.x() - size.width() / 2),
                                 (self.mTarget.y() - size.height() + TIP_HEIGHT / 2))
        
        #Keep the tooltip on the same screen if possible
        screen = QtGui.QApplication.desktop().screenGeometry(self.mTarget)
        position.setX(max(screen.left(), min(position.x(), \
            screen.left() + screen.width() - size.width())))
        position.setY(max(screen.top(), min(position.y(), \
            screen.top() + screen.height() - size.height())))
        
        self.move(position)
        
        tipX = self.mTarget.x() - position.x()
        if (self.mBox != textbox or self.mTipX != tipX):
            self.mBox = textbox
            self.mTipX = tipX
            
            self.resize(size)
            self.buildPath()
            self.setMask(self.mMask)
    
    def buildPath(self):
        """
        Prepare the painter path for future use so
        we only have to generate the text at runtime.
        """
        #Draw the text box
        self.mPainterPath = QtGui.QPainterPath()
        self.mPainterPath.addRect(QtCore.QRectF(self.mBox))
        
        #Draw the Tip
        polygon = QtGui.QPolygonF()
        polygon << QtCore.QPointF(float(max(0, self.mTipX - 3)), float(self.mBox.height()))\
                << QtCore.QPointF(self.mTipX, float(self.mBox.height() + TIP_HEIGHT))\
                << QtCore.QPointF(float(min(self.mTipX + 3, self.mBox.width())), float(self.mBox.height()))
        self.mPainterPath.addPolygon(polygon)
        
        #Store the simplified version of the path
        self.mPainterPath = self.mPainterPath.simplified()
        
        #Create the mask used to erase the background
        #Note: this is a binary bitmap (black & white)
        self.mMask = QtGui.QBitmap(self.size())
        painter = QtGui.QPainter(self.mMask)
        painter.fillRect(self.mMask.rect(), QtCore.Qt.white)
        painter.setPen(QtCore.Qt.black)
        painter.setBrush(QtCore.Qt.black)
        painter.drawPath(self.mPainterPath)
        painter.end()
    
    def setTip(self, target, time, text=""):
        self.mInitialized = True
        self.mDisplayedText = time
        if (text):
            self.mDisplayedText += " - %s" % text
        
        if (target != self.mTarget or len(time) != len(self.mTime) or text != self.mText):
            self.mTarget = target
            self.mText = text
            self.mTime = time
            self.adjustPosition()
        
        self.update()
    
    def show(self):
        self.setVisible(self.mInitialized)
    
    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHints(QtGui.QPainter.HighQualityAntialiasing | QtGui.QPainter.TextAntialiasing)
        
        p.setPen(QtCore.Qt.black)
        p.setBrush(QtGui.qApp.palette().base())
        p.drawPath(self.mPainterPath)
        
        p.setFont(self.mFont)
        p.setPen(QtGui.QPen(QtGui.qApp.palette().text(), 1))
        p.drawText(self.mBox, QtCore.Qt.AlignCenter, self.mDisplayedText)
        
        p.end()
