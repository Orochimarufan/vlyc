"""
/*****************************************************************************
 * vlyc :: seekstyle.py : Seek slider style
 ****************************************************************************
 * Copyright (C) 2011-2012 VLC authors and VideoLAN
 *
 * Authors: Ludovic Fauvet <etix@videolan.org>
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
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.
 *****************************************************************************/
"""
from __future__ import absolute_import, unicode_literals
from PyQt4 import QtCore, QtGui
from .const import SEEK_RADIUS, SEEK_CHAPTERSSPOTSIZE, root_logger


class SeekStyle(QtGui.QCommonStyle): #TODO: Should be QWindowsStyle, but its not in PyQt4?
    SIG = """
public:
    virtual int pixelMetric(PixelMetric metric, const QStyleOption * option = 0, const QWidget * widget = 0) const
    virtual void drawComplexControl(ComplexControl cc, const QStyleOptionComplex *opt, QPainter *p, const QWidget *widget) const
    """
    
    def pixelMetric(self, metric, option=0, widget=0):
        if (metric == self.PM_SliderLength):
            return option.rect.height()
        else:
            return super(SeekStyle, self).pixelMetric(metric, option, widget)
    
    def drawComplexControl(self, cc, option, painter, widget):
        if (cc == self.CC_Slider):
            painter.setRenderHints(QtGui.QPainter.Antialiasing)
            
            if (not isinstance(option, QtGui.QStyleOptionSlider)):
                QtCore.qWarning() << "SeekStyle: Drawing an unmanaged control"
                super(SeekStyle, self).drawComplexControl(cc, option, widget)
                return
            slider = option
            
            seekSlider = widget if (isinstance(widget, SeekSlider)) else None
            
            sliderPos = -1
            
            #Get the needed subcontrols to draw the slider
            groove = self.subControlRect(self.CC_Slider, option, self.SC_SliderGroove)
            handle = self.subControlRect(self.CC_Slider, option, self.SC_SliderHandle)
            
            # TODO: better solution! For some reason the height is 0 or -1
            handle.setHeight(handle.width())
            groove.setHeight(widget.height())
            
            #Adjust the size of the groove so the handle stays centered
            groove.adjust(handle.width() / 2, 0, -handle.width() / 2, 0)
            
            #Reduce the height of the groove
            # -> see Original code for -1 explanation
            groove.adjust(0, groove.height() / 3.7, 0, -groove.height() / 3.7 - 1)
            
            #root_logger.debug("Groove: %i, %i, %i, %i Handle: %i, %i, %i, %i"%(groove.left(), groove.width(), groove.top(), groove.height(),
            #                                                             handle.left(), handle.width(), handle.top(), handle.height()))
            
            if ((option.subControls & self.SC_SliderGroove) and groove.isValid()):
                #root_logger.getChild("SeekStyle").debug("Drawing Groove")
                sliderPos = (groove.width() / slider.maximum) * slider.sliderPosition
                
                #Set the background color and gradient
                backgroundBase = slider.palette.window().color()
                backgroundGradient = QtGui.QLinearGradient(0, 0, 0, slider.rect.height())
                backgroundGradient.setColorAt(0.0, backgroundBase.darker(140))
                backgroundGradient.setColorAt(1.0, backgroundBase)
                
                #Set the foreground color and gradient
                foregroundBase = QtGui.QColor(50, 156, 255)
                foregroundGradient = QtGui.QLinearGradient(0, 0, 0, groove.height())
                foregroundGradient.setColorAt(0.0, foregroundBase)
                foregroundGradient.setColorAt(1.0, foregroundBase.darker(125))
                
                #Draw a slight 3D effect on the bottom
                painter.setPen(QtGui.QColor(23, 230, 230))
                painter.setBrush(QtCore.Qt.NoBrush)
                painter.drawRoundedRect(groove.adjusted(0, 2, 0, 0), SEEK_RADIUS, SEEK_RADIUS)
                
                #Draw background
                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(backgroundGradient)
                painter.drawRoundedRect(groove, SEEK_RADIUS, SEEK_RADIUS)
                
                #Adjusted foreground rectangle
                valueRect = groove.adjusted(1, 1, -1, 0)
                valueRect.setWidth(sliderPos)
                
                #Draw foreground
                if (slider.sliderPosition > slider.minimum and slider.sliderPosition <= slider.maximum):
                    painter.setPen(QtCore.Qt.NoPen)
                    painter.setBrush(foregroundGradient)
                    painter.drawRoundedRect(valueRect, SEEK_RADIUS, SEEK_RADIUS)
                
                #Draw buffering overlay
                if (seekSlider and seekSlider.f_buffering < 1.0):
                    innerRect = groove.adjusted(1, 1,
                                                groove.width() * (-1.0 + seekSlider.f_buffering) - 1,
                                                0)
                    overlayColor = QtGui.QColor("Orange")
                    overlayColor.setAlpha(128)
                    painter.setBrush(overlayColor)
                    painter.drawRoundedRect(innerRect, SEEK_RADIUS, SEEK_RADIUS)
            
            if (option.subControls & self.SC_SliderTickmarks):
                tempSlider = QtGui.QStyleOptionSlider(slider)
                tempSlider.subControls = self.SC_SliderTickmarks
                super(SeekSlider, self).drawComplexControl(cc, tempSlider, painter, widget)
            
            if ((option.subControls & self.SC_SliderHandle) and handle.isValid()):
                #Useful for debugging:
                #root_logger.getChild("SeekStyle").debug("Drawing Handle")
                #painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 255, 150)))
                #painter.drawRect(handle)
                
                p = slider.palette
                
                if (option.state & QtGui.QStyle.State_MouseOver or (seekSlider and seekSlider.isAnimationRunning())):
                    
                    #Draw Chapters Tickpoints
                    if (seekSlider.chapters and seekSlider.inputLength and groove.width()):
                        background = p.color(QtGui.QPalette.Active, QtGui.QPalette.Background)
                        foreground = p.color(QtGui.QPalette.Active, QtGui.QPalette.WindowText)
                        foreground.setHsv(foreground.hue(),
                                          (background.saturation() + foreground.saturation()) / 2,
                                          (background.value() + foreground.value()) / 2)
                        if (slider.orientation == QtCore.Qt.Horizontal):
                            points = seekSlider.chapters.getPoints()
                            for point in points:
                                x = groove.x() + point.time / 1000000.0 / seekSlider.inputLength * groove.width()
                                painter.setPen(foreground)
                                painter.setBrush(QtCore.Qt.NoBrush)
                                painter.drawLine(x, slider.rect.height(), x, slider.rect.height() - SEEK_CHAPTERSSPOTSIZE)
                    
                if (option.state & QtGui.QStyle.State_Enabled and sliderPos != -1):
                    hSize = QtCore.QSize(handle.height(), handle.height()) - QtCore.QSize(6, 6)
                    pos = QtCore.QPoint(handle.center().x() - (hSize.width() / 2),
                                        handle.center().y() - (hSize.height() / 2))
                    
                    shadowPos = pos - QtCore.QPoint(2, 2)
                    sSize = hSize + QtCore.QSize(4, 4)
                    
                    #Prepare the handle's gradient
                    handleGradient = QtGui.QLinearGradient(0, 0, 0, hSize.height())
                    handleGradient.setColorAt(0.0, p.window().color().lighter(120))
                    handleGradient.setColorAt(1.0, p.window().color().darker(120))
                    
                    #Prepare the handle's shadow gradient
                    shadowBase = p.shadow().color()
                    if (shadowBase.lightness() > 100):
                        shadowBase = QtGui.QColor(60, 60, 60) #Palette's shadow is too bright
                    shadowDark = shadowBase.darker(150)
                    shadowLight = shadowBase.lighter(180)
                    shadowLight.setAlpha(50)
                    
                    shadowGradient = QtGui.QRadialGradient(shadowPos.x() + (sSize.width() / 2),
                                                           shadowPos.y() + (sSize.height() / 2),
                                                           max(sSize.width(), sSize.height()) / 2)
                    shadowGradient.setColorAt(0.4, shadowDark)
                    shadowGradient.setColorAt(1.0, shadowLight)
                    
                    painter.setPen(QtCore.Qt.NoPen)
                    if (seekSlider):
                        painter.setOpacity(seekSlider.mHandleOpacity)
                    
                    #Draw the handle's shadow
                    painter.setBrush(shadowGradient)
                    painter.drawEllipse(shadowPos.x(), shadowPos.y() + 1, sSize.width(), sSize.height())
                    
                    #Finally draw the handle
                    painter.setBrush(handleGradient)
                    painter.drawEllipse(pos.x(), pos.y(), hSize.width(), hSize.height())
        else:
            #root_logger.getChild("SeekSlider").warn("drawing unmanaged ComplexControl")
            super(SeekStyle, self).drawComplexControl(cc, option, widget)
    
from .input_slider import SeekSlider #SeekStyle has to be defined already!
