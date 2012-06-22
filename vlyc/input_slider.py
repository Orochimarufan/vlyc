"""
/*****************************************************************************
 * input_slider.py : VolumeSlider and SeekSlider
 ****************************************************************************
 * Copyright (C) 2006-2011 the VideoLAN team
 * $Id: 6b16767b1a4a44b0e596e10cf6830e100329999b $
 *
 * Authors: Clément Stenac <zorglub@videolan.org>
 *          Jean-Baptiste Kempf <jb@videolan.org>
 *          Ludovic Fauvet <etix@videolan.org>
 *          Orochimarufan <orochimarufan.x3@gmail.com> (Python)
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

from __future__ import absolute_import, unicode_literals, division
from PyQt4 import QtCore, QtGui
from .const import SOUNDMAX, SOUNDMIN, SOUNDW, SOUNDH, VOLUME_MAX
from .const import SEEK_MINIMUM, SEEK_MAXIMUM, SEEK_STEP
from .const import SEEK_FADEDURATION, SEEK_FADEOUTDELAY
from .const import SEEK_CHAPTERSSPOTSIZE, root_logger
from .util import secstotimestr
from .timetooltip import TimeTooltip
 
class SoundSlider(QtGui.QAbstractSlider):
    """
    SoundSlider inherited from QAbstractSlider
    
    /* This work is derived from Amarok's work under GPLv2+
       - Mark Kretschmann
       - Gábor Lehel
     */
    """
#public:
    #SoundSlider(QWidget parent, int i_step, bool b_softamp, char psz_colors)
    #void setMuted(bool b_mute)
#protected:
    paddingL = 3; #const static int
    paddingR = 2; #const static int
    #void paintEvent(QPaintEvent event)
    #void wheelEvent(QWheelEvent event)
    #void mousePressEvent(QMouseEvent event)
    #void mouseMoveEvent(QMouseEvent event)
    #void mouseReleaseEvent(QMouseEvent event)
#private:
    #bool isSliding
    #bool b_mouseOutside
    #int i_oldvalue
    #float f_step
    #bool b_isMuted
    #QPixmap pixGradient
    #QPixmap pixGradient2
    #QPixmap pixOutside
    #QPainter painter
    #QColor background
    #QColor foreground
    #QFont textfont
    #QRect textrect
    #void changeValue(int x)
    def __init__(self, parent, i_step, b_softamp, psz_colors):
        super(SoundSlider, self).__init__(parent);
        
        self.f_step = i_step*100 / VOLUME_MAX;
        self.setRange(SOUNDMIN, 2*SOUNDMAX if b_softamp else SOUNDMAX);
        self.setMouseTracking(True);
        self.isSliding = False;
        self.b_mouseOutside = True;
        self.b_isMuted = False;
        
        self.pixOutside = QtGui.QPixmap(":/toolbar/volslide-outside");
        
        temp = QtGui.QPixmap(":/toolbar/volslide-inside");
        mask = temp.createHeuristicMask();
        
        self.setFixedSize(self.pixOutside.size());
        
        self.pixGradient = QtGui.QPixmap(mask.size());
        self.pixGradient2 = QtGui.QPixmap(mask.size());
        
        #Gradient Building from the preferences
        gradient = QtGui.QLinearGradient(self.paddingL, 2, SOUNDW + self.paddingL, 2);
        gradient2 = QtGui.QLinearGradient(self.paddingL, 2, SOUNDW + self.paddingL, 2);
        
        colorList = psz_colors.split(";");
        del psz_colors;
        
        #Fill with 255 if list is too short
        while "" in colorList: colorList.remove("");
        if (len(colorList)<12):
            for i in range(12-len(colorList)):
                colorList.append("255");
        
        self.background = self.palette().color(QtGui.QPalette.Active, QtGui.QPalette.Background);
        self.foreground = self.palette().color(QtGui.QPalette.Active, QtGui.QPalette.WindowText);
        self.foreground.setHsv( self.foreground.hue(), 
                               (self.background.saturation()+self.foreground.saturation())/2, 
                               (self.background.value()+self.foreground.value())/2)
        
        self.textfont = QtGui.QFont();
        self.textfont.setPixelSize(9);
        self.textrect = QtCore.QRect();
        self.textrect.setRect(0, 0, 34, 15);
        
        #HELPERS
        c = lambda i: int(colorList[i]);
        add_color = lambda range, c1, c2, c3: gradient.setColorAt(range, QtGui.QColor(c(c1), c(c2), c(c3)));
        def desaturate(c): c.setHsvF(c.hueF(), 0.2, 0.5, 1.0); return c;
        add_desaturated_color = lambda range, c1, c2, c3: gradient2.setColorAt(range, desaturate(QtGui.QColor(c(c1), c(c2), c(c3))));
        def add_colors(range, c1, c2, c3):
            add_color(range, c1, c2, c3);
            add_desaturated_color(range, c1, c2, c3);
        
        f_mid_point = 100.0/self.maximum();
        add_colors(0.0, 0, 1, 2);
        add_colors(f_mid_point - 0.05, 3, 4, 5);
        add_colors(f_mid_point + 0.05, 6, 7, 8);
        add_colors(1.0, 9, 10, 11);
        
        self.painter = QtGui.QPainter();
        
        self.painter.begin(self.pixGradient);
        self.painter.setPen(QtCore.Qt.NoPen);
        self.painter.setBrush(gradient);
        self.painter.drawRect(self.pixGradient.rect());
        self.painter.end();
        
        self.painter.begin(self.pixGradient2);
        self.painter.setPen(QtCore.Qt.NoPen);
        self.painter.setBrush(gradient2);
        self.painter.drawRect(self.pixGradient.rect());
        self.painter.end();
        
        self.pixGradient.setMask(mask);
        self.pixGradient2.setMask(mask);
    
    def wheelEvent(self, event):
        newvalue = self.value() + event.delta() / (8*15) * self.f_step;
        self.setValue(min(max(self.minimum(), newvalue), self.minimum()));
        self.emit(QtCore.SIGNAL("sliderReleased(void)"));
        self.emit(QtCore.SIGNAL("sliderMoved(int)"), self.value());
    
    def mousePressEvent(self, event):
        if (event.button()!=QtCore.Qt.RightButton):
            #We enter the sliding mode
            self.isSliding = True;
            self.i_oldvalue = self.value();
            self.emit(QtCore.SIGNAL("sliderPressed(void)"));
            self.changeValue(event.x()-self.paddingL);
            self.emit(QtCore.SIGNAL("sliderMoved(int)"), self.value());
    
    def mouseReleaseEvent(self, event):
        if (event.button()!=QtCore.Qt.RightButton):
            if (not self.b_mouseOutside and self.value() != self.i_oldvalue):
                self.emit(QtCore.SIGNAL("sliderReleased(void)"));
                self.setValue(self.value()); #XXX: Why?
                self.emit(QtCore.SIGNAL("sliderMoved(int)"), self.value());
            self.isSliding = False;
            self.b_mouseOutside = False;
    
    def mouseMoveEvent(self, event):
        if (self.isSliding):
            rect = QtCore.QRect(self.paddingL-15, -1, SOUNDW+15*2, SOUNDH+5);
            if (not rect.contains(event.pos())):
                #We are outside
                if (not self.b_mouseOutside):
                    self.setValue(self.i_oldvalue);
                    self.b_mouseOutside = True;
            else:
                #We are inside
                self.b_mouseOutside = False;
                self.changeValue(event.x() - self.paddingL);
                self.emit(QtCore.SIGNAL("sliderMoved(int)"), self.value());
        else:
            i = ( (event.x()-self.paddingL) * self.maximum() +40 ) / SOUNDW;
            i = min(max(0, i), self.maximum());
            self.setToolTip("%i %%"%i);
    
    def changeValue(self, x):
        self.setValue((x*self.maximum()+40)/SOUNDW);
    
    def setMuted(self, b_mute):
        self.b_isMuted = b_mute;
        self.update();
    
    def paintEvent(self, event):
        if (self.b_isMuted):
            paintGradient = self.pixGradient2;
        else:
            paintGradient = self.pixGradient;
        
        self.painter.begin(self);
        
        offset = int((SOUNDW*self.value()+100)/self.maximum()) + self.paddingL;
        
        boundsG = QtCore.QRect(0, 0, offset, paintGradient.height());
        self.painter.drawPixmap(boundsG, paintGradient, boundsG);
        
        boundsO = QtCore.QRect(0, 0, self.pixOutside.width(), self.pixOutside.height());
        self.painter.drawPixmap(boundsO, self.pixOutside, boundsO);
        
        self.painter.setPen(self.foreground);
        self.painter.setFont(self.textfont);
        self.painter.drawText(self.textrect, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter, 
                              "%i%%"%self.value());
        
        self.painter.end();
        event.accept();

class SeekSlider(QtGui.QSlider):
    """
    Input Slider derived from QSlider
    """
    SIG = """
public:
    SeekSlider( Qt::Orientation q, QWidget *_parent = 0, bool _classic = false );
    ~SeekSlider();
    void setChapters( SeekPoints * );
protected:
    void mouseMoveEvent( QMouseEvent *event );
    void mousePressEvent( QMouseEvent* event );
    void mouseReleaseEvent( QMouseEvent *event );
    void wheelEvent( QWheelEvent *event );
    void enterEvent( QEvent * );
    void leaveEvent( QEvent * );
    void hideEvent( QHideEvent * );
    bool eventFilter( QObject *obj, QEvent *event );
    QSize sizeHint();
    bool isAnimationRunning();
    qreal handleOpacity();
    void setHandleOpacity( qreal opacity );
    int handleLength();
private:
    bool isSliding;        /* Whether we are currently sliding by user action */
    bool isJumping;              /* if we requested a jump to another chapter */
    int inputLength;                           /* InputLength that can change */
    char psz_length[MSTRTIME_MAX_SIZE];               /* Used for the ToolTip */
    QTimer *seekLimitTimer;
    TimeTooltip *mTimeTooltip;
    float f_buffering;
    SeekPoints* chapters;
    bool b_classic;
    int mHandleLength;
    /* Colors & gradients */
    QSize gradientsTargetSize;
    QLinearGradient backgroundGradient;
    QLinearGradient foregroundGradient;
    QLinearGradient handleGradient;
    QColor tickpointForeground;
    QColor shadowDark;
    QColor shadowLight;
    /* Handle's animation */
    qreal mHandleOpacity;
    QPropertyAnimation *animHandle;
    QTimer *hideHandleTimer;
public slots:
    void setPosition( float, int64_t, int );
    void updateBuffering( float );
    void hideHandle();
private slots:
    void startSeekTimer();
    void updatePos();
signals:
    void sliderDragged( float );
"""
    def __init__(self, q, parent=0, classic=False):
        super(SeekSlider, self).__init__(q, parent);
        self.b_classic = classic;
        
        self.isSliding = False;
        self.f_buffering = 1.0;
        self.mHandleOpacity = 1.0;
        self.chapters = None;
        self.mHandleLength = -1;
        
        #Prepare some static colors
        p = self.palette();
        background = p.color(QtGui.QPalette.Active, QtGui.QPalette.Background);
        self.tickpointForeground = p.color(QtGui.QPalette.Active, QtGui.QPalette.WindowText);
        self.tickpointForeground.setHsv(self.tickpointForeground.hue(), 
                                        (background.saturation()+self.tickpointForeground.saturation())/2, 
                                        (background.value()+self.tickpointForeground.value())/2);
        
        #Set the background color and gradient
        backgroundBase = p.window().color();
        self.backgroundGradient = QtGui.QLinearGradient();
        self.backgroundGradient.setColorAt(0.0, backgroundBase.darker(140));
        self.backgroundGradient.setColorAt(1.0, backgroundBase);
        
        #set the foreground color and gradient
        foregroundBase = QtGui.QColor(50, 156, 255);
        self.foregroundGradient = QtGui.QLinearGradient();
        self.foregroundGradient.setColorAt(0.0, foregroundBase);
        self.foregroundGradient.setColorAt(1.0, foregroundBase.darker(140));
        
        #prepare the handle's gradient
        self.handleGradient = QtGui.QLinearGradient();
        self.handleGradient.setColorAt(0.0, p.window().color().lighter(120));
        self.handleGradient.setColorAt(1.0, p.window().color().darker(120));
        
        #prepare the handle's shadow gradient
        shadowBase = p.shadow().color();
        if (shadowBase.lightness()>100):
            #Palette's shadow is too bright
            shadowBase = QtGui.QColor(60, 60, 60);
        self.shadowDark = shadowBase.darker(150);
        self.shadowLight = shadowBase.lighter(180);
        self.shadowLight.setAlpha(50);
        
        #Timer used to fire intermediate updatePos() when sliding
        self.seekLimitTimer = QtCore.QTimer(self);
        self.seekLimitTimer.setSingleShot(True);
        
        #Tooltip bubble
        self.mTimeTooltip = TimeTooltip(self);
        self.mTimeTooltip.setMouseTracking(True);
        
        #Properties
        self.setRange(SEEK_MINIMUM, SEEK_MAXIMUM);
        self.setSingleStep(SEEK_STEP);
        self.setPageStep(SEEK_STEP*5);
        self.setMouseTracking(True);
        self.setTracking(True);
        self.setFocusPolicy(QtCore.Qt.NoFocus);
        
        #Use new/classic style
        if (not self.b_classic):
            self.setStyle(SeekStyle());
        
        #Init to 0
        self.setPosition(-1.0, 0, 0);
        self.psz_length = secstotimestr(0);
        
        self.animHandle = QtCore.QPropertyAnimation(self, "handleOpacity", self);
        self.animHandle.setDuration(SEEK_FADEDURATION);
        self.animHandle.setStartValue(0.0);
        self.animHandle.setEndValue(1.0);
        
        self.hideHandleTimer = QtCore.QTimer(self);
        self.hideHandleTimer.setSingleShot(True);
        self.hideHandleTimer.setInterval(SEEK_FADEOUTDELAY);
        
        self.connect(self, QtCore.SIGNAL("sliderMoved(int)"), self.startSeekTimer);
        self.connect(self.seekLimitTimer, QtCore.SIGNAL("timeout()"), self.updatePos);
        self.connect(self.hideHandleTimer, QtCore.SIGNAL("timeout()"), self.hideHandle);
        self.mTimeTooltip.installEventFilter(self);
    
    #Destructor is handled by Python GC
    
    def setChapters(self, chapters):
        """
        /***
         * \brief Sets the chapters seekpoints adapter
         *
         * \params SeekPoints initilized with current intf thread
         ***/
        """
        del self.chapters;
        self.chapters = chapters;
        self.chapters.setParent(self);
    
    def setPosition(self, pos, time, length):
        """
        /***
         * \brief Main public method, superseeding setValue. Disabling the slider when neeeded
         *
         * \param pos Position, between 0 and 1. -1 disables the slider
         * \param time Elapsed time. Unused
         * \param legnth Duration time.
         ***/
        """
        if (pos==-1.0):
            self.setEnabled(False);
            self.mTimeTooltip.hide();
            self.isSliding = False;
        else:
            self.setEnabled(True);
        
        if (not self.isSliding):
            self.setValue(int(pos*SEEK_MAXIMUM));
        
        self.inputLength = length;
    
    def startSeekTimer(self):
        """ only fire one update, when sliding, every 150ms """
        if (self.isSliding and not self.seekLimitTimer.isActive()):
            self.seekLimitTimer.start(150);
    
    def updatePos(self):
        """ Send new position to player """
        f_pos = self.value()/SEEK_MAXIMUM;
        self.emit(QtCore.SIGNAL("sliderDragged(float)"), f_pos);
    
    def updateBuffering(self, f_buffering):
        self.f_buffering = f_buffering;
        self.repaint();
    
    def mouseReleaseEvent(self, event):
        event.accept();
        self.isSliding = False;
        b_seekPending = self.seekLimitTimer.isActive();
        self.seekLimitTimer.stop();
        if (self.isJumping):
            self.isJumping = False;
            return;
        super(SeekSlider, self).mouseReleaseEvent(event);
        if (b_seekPending):
            self.updatePos();
    
    valueFromPosition = lambda self, x: QtGui.QStyle.sliderValueFromPosition(SEEK_MINIMUM, SEEK_MAXIMUM, x-self.handleLength()/2, self.width()-self.handleLength(), False)
    
    def mousePressEvent(self, event):
        #Right click
        if (event.button() not in (QtCore.Qt.LeftButton, QtCore.Qt.MidButton)):
            super(SeekSlider, self).mousePressEvent(event);
            return;
        
        self.isJumping = False;
        #Handle chapter clicks
        i_width = self.size().width();
        if (self.chapters and self.inputLength and i_width):
            if (self.orientation()==QtCore.Qt.Horizontal):
                #only on chapters zone
                if (event.y()<SEEK_CHAPTERSSPOTSIZE or\
                    event.y()>(self.size().height()-SEEK_CHAPTERSSPOTSIZE)):
                    points = self.chapters.getPoints();
                    i_selected=-1;
                    b_startsnonzero=False;
                    if (len(points)>0): #do we need an extra offset?
                        b_startsnonzero = (points[0].time>0)
                    i_min_diff = i_width+1;
                    for i in range(len(points)):
                        x = points[i].time/1000000.0/self.inputLength*i_width;
                        diff_x = abs(x-event-x());
                        if (diff_x<i_min_diff):
                            i_min_diff = diff_x;
                            i_selected = i +(1 if b_startsnonzero else 0);
                        else: break;
                    if (i_selected>-1 and i_min_diff<4): #bool(-1)==True!
                        self.chapters.jumpTo(i_selected);
                        event.accept();
                        self.isJumping = True;
                        return;
            else:
                pass #TODO: vertical
        
        self.isSliding = True;
        self.setValue(self.valueFromPosition(event.x()));
        self.emit(QtCore.SIGNAL("sliderMoved(int)"), self.value());
        event.accept();
    
    def mouseMoveEvent(self, event):
        if (self.isSliding):
            self.setValue(self.valueFromPosition(event.x()));
            self.emit(QtCore.SIGNAL("sliderMoved(int)"), self.value());
        #Tooltip
        if (self.inputLength>0):
            margin = self.handleLength()/2;
            posX = max(self.rect().left()+margin, min(self.rect().right()-margin, event.x()));
            chapterLabel = None;
            if (self.orientation()==QtCore.Qt.Horizontal and self.chapters is not None):
                points = self.chapters.getPoints();
                i_selected = -1;
                b_startsnonzero = False;
                if (len(points)>0):
                    b_startsnonzero = (points[0].time>0);
                for i in range(len(points)):
                    x = points[i].time/1000000.0/self.inputLength*self.size().width();
                    if (event.x()>=x):
                        i_selected=i +(1 if b_startsnonzero else 0);
                if (i_selected>=0 and i_selected<len(points)):
                    chapterLabel = points[i_selected].name;
            else:
                pass #TODO: vertical
            
            target = QtCore.QPoint(event.globalX() - (event.x() - posX), 
                                   self.mapToGlobal(QtCore.QPoint(0, 0)).y());
            self.psz_length = secstotimestr(((posX - margin)*self.inputLength)/(self.size().width()-self.handleLength())//1000);
            self.mTimeTooltip.setTip(target, self.psz_length, chapterLabel);
        event.accept();
    
    def wheelEvent(self, event):
        #Don't do anython if wa are for some reason sliding
        if (not self.isSliding()):
            self.setValue(self.value()+(event.delta()/12)); #/* 12 = 8 * 15 / 10
                #Since delta is in 1/8 of ° and mouse have steps of 15 °
                #and that our slider is in 0.1% and we want one step to be a 1%
                #increment of position */
            self.emit(QtCore.SIGNAL("sliderDragged(float)"), self.value()/SEEK_MAXIMUM);
        event.accept();
    
    def enterEvent(self, event):
        #Cancel the fade-out timer
        self.hideHandleTimer.stop();
        #Only start the fade-in if needed
        if (self.animHandle.direction() != QtCore.QAbstractAnimation.Forward):
            if (self.animHandle.state() == QtCore.QAbstractAnimation.Running):
                self.animHandle.pause();
            self.animHandle.setDirection(QtCore.QAbstractAnimation.Forward);
            self.animHandle.start();
        #Dont show the tooltip if the slider is disabled or a menu is open
        if (self.isEnabled() and self.inputLength>0 and not QtGui.qApp.activePopupWidget()):
            self.mTimeTooltip.show();
    
    def leaveEvent(self, event):
        self.hideHandleTimer.start();
        if (not self.rect().contains(self.mapFromGlobal(QtGui.QCursor.pos())) or\
            (not self.isActiveWindow() and not self.mTimeTooltip.isActiveWindow())):
            self.mTimeTooltip.hide();
    
    def hideEvent(self, event):
        self.mTimeTooltip.hide();
    
    def eventFilter(self, obj, event):
        if (obj == self.mTimeTooltip):
            if (event.type() in (QtCore.QEvent.Leave, QtCore.QEvent.MouseMove)):
                #event = QtGui.QMouseEvent(event)
                #if (not self.rect().contains(self.mapFromGlobal(event.globalPos()))):
                #    self.mTimeTooltip.hide();
                pass #TODO: Dunno how to cast QEvent to QMouseEvent in PyQt D:
            return False;
        else:
            return super(SeekSlider, self).eventFilter(obj, event);
    
    def sizeHint(self):
        if (self.b_classic):
            return super(SeekSlider, self).sizeHint();
        return (QtCore.QSize(100, 18) if self.orientation()==QtCore.Qt.Horizontal else QtCore.QSize(18, 100));
    
    def getHandleOpacity(self):
        return self.mHandleOpacity;
    
    def setHandleOpacity(self, opacity):
        self.mHandleOpacity = opacity;
        self.update();
    
    handleOpacity = QtCore.pyqtProperty("qreal", getHandleOpacity, setHandleOpacity);
    
    def handleLength(self):
        if (self.mHandleLength>0):
            return self.mHandleLength;
        option = QtGui.QStyleOptionSlider();
        self.initStyleOption(option);
        self.mHandleLength = self.style().pixelMetric(QtGui.QStyle.PM_SliderLength, option);
        return self.mHandleLength;
    
    def hideHandle(self):
        if (self.animHandle.state()==QtCore.QAbstractAnimation.Running):
            self.animHandle.pause();
        self.animHandle.setDirection(QtCore.QAbstractAnimation.Backward);
        self.animHandle.start();
    
    def isAnimationRunning(self):
        return self.animHandle.state()==QtCore.QAbstractAnimation.Running or self.hideHandleTimer.isActive();

from .seekstyle import SeekStyle #SeekSlider has to be defined already
