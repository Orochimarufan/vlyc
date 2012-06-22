"""
/*****************************************************************************
 * widgets.py : Custom widgets for the main interface
 ****************************************************************************
 * Copyright (C) 2006-2008 the VideoLAN team
 * $Id: 97b8bc6236887d60b7f820c330747acbe5730271 $
 *
 * Authors: Clément Stenac <zorglub@videolan.org>
 *          Jean-Baptiste Kempf <jb@videolan.org>
 *          Rafaël Carré <funman@videolanorg>
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
from __future__ import absolute_import,unicode_literals
from PyQt4 import QtCore,QtGui
from .util import secstotimestr, AutoEnum
from .input_slider import SoundSlider
from . import const

class ClickableQLabel(QtGui.QLabel):
    def mouseDoubleClickEvent(self, event):
        self.emit(QtCore.SIGNAL("doubleClicked(void)"));

class VideoWidget(QtGui.QFrame):
    def __init__(self, parent):
        super(VideoWidget, self).__init__(parent)
        self._layout = QtGui.QHBoxLayout(self);
        self._layout.setContentsMargins(0, 0, 0, 0);
        self._stable = None;
        self.logger = const.root_logger.getChild("VideoWidget")
    def request(self,i_x,i_y,i_width,i_height,b_keep_size):
        self.logger.debug("Video was requested %i, %i"%(i_x,i_y));
        if (self._stable):
            self.logger.debug("Embedded Video already in use");
            return 0;
        if (b_keep_size):
            i_width = self.size().width();
            i_height = self.size().height();
#115    /* The owner of the video window needs a stable handle (WinId). Reparenting
#116     * in Qt4-X11 changes the WinId of the widget, so we need to create another
#117     * dummy widget that stays within the reparentable widget. */
        self._stable = QtGui.QWidget();
        self._plt = QtGui.QPalette()
        self._plt.setColor(QtGui.QPalette.Window,QtCore.Qt.black);
        self._stable.setPalette(self._plt);
        self._stable.setAutoFillBackground(True);
        self._layout.addWidget(self._stable);
#123    /* Indicates that the widget wants to draw directly onto the screen.
#124       Widgets with this attribute set do not participate in composition
#125       management */
#126    /* This is currently disabled on X11 as it does not seem to improve
#127     * performance, but causes the video widget to be transparent... */
        #self._stable.setAttribute(QtCore.Qt.WA_PainOnScreen);
        #self._sync()
        return self._stable.winId();
    def setSizing(self,i_w,i_h):
        self.resize(i_w,i_h);
        if (self.size().width()==i_w and self.size().height()==i_h):
            self.updateGeometry();
        #self._sync())
    def release(self):
        self.logger.debug("Video is not needed anymore");
        if (self._stable):
            self._layout.removeWidget(self._stable);
            self._stable.deleteLater();
            self._stable = None;
        self.updateGeometry();
    
    mM = QtCore.pyqtSignal(int,int)
    
    def mouseMoveEvent(self,e):
        self.mM.emit(e.x(),e.y())

class TimeLabel(ClickableQLabel):
    Display = AutoEnum("DisplayType", 
                "Disabled", 
                "Elapsed", 
                "Remaining", 
                "Both")
    def __init__(self,displayType):
        super(TimeLabel,self).__init__();
        self.bufTimer = QtCore.QTimer(self);
        self.buffering = False;
        self.showBuffering = False;
        self.bufVal = -1;
        self.displayType = displayType;
        self.b_remainingTime = False;
        if (displayType & self.Display.Elapsed):
            self.b_remainingTime = False #self.getSettings().value("MainWindow/ShowRemainingTime",False);
        if (displayType == self.Display.Elapsed):
            self.setText(" --:-- ");
            self.setToolTip(QtCore.QCoreApplication.translate("TimeLabel","Elapsed time"));
        elif (displayType == self.Display.Remaining):
            self.setText(" --:-- ");
            self.setToolTip(QtCore.QCoreApplication.translate("TimeLabel","Total/Remaining Time\nClick to toggle between Total and Remaining Time"));
        elif (displayType == self.Display.Both):
            self.setText(" --:--/--:-- ");
            self.setToolTip(QtCore.QCoreApplication.translate("TimeLabel","Click to toggle between elapsed and remaining time"));
        self.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter);
        self.bufTimer.setSingleShot(True);
        self.setStyleSheet("padding-left: 4px; padding-right: 4px;");
    def setDisplayPosition(self,f_pos,i_t=None,i_length=None):
        # setDisplayPosition(float pos)
        if (i_t is None and i_length is None):
            if (f_pos == -1.0 or self.cachedLength == 0):
                self.setText(" --:--/--:-- ");
                return;
            time = f_pos * self.cachedLength
            psz_time = secstotimestr(self.cachedLength-time if (self.b_remainingTime and self.cachedLength) else time);
            timestr = "{0}{1}/{2}".format(
                                          "-" if (self.b_remainingTime and i_length) else "",
                                          psz_time,
                                          "--:--" if (not i_length and time) else self.psz_length);
            self.setText(timestr);
            return;
        # setDisplayPosition(float pos, int t, int length)
        self.showBuffering = False;
        self.bufTimer.stop();
        if (f_pos == -1.0):
            self.setMinimumSize(0, 0);
            if (self.displayType==self.Display.Both):
                self.setText("--:--/--:--");
            else:
                self.setText("--:--");
            return;
        time = i_t/1000;
        length = i_length/1000;
        if i_length>0:
            self.psz_length = secstotimestr(length);
        else:
            self.psz_length = None
        psz_time = secstotimestr(length - time if (self.b_remainingTime and i_length) else time);
        minsize = QtCore.QSize(0,0)
        if (i_length>0):
            margins = self.contentsMargins();
            minsize += QtCore.QSize(self.fontMetrics().size(0,self.psz_length,0,None).width(),
                                    self.sizeHint().height());
            minsize += QtCore.QSize(margins.left()+margins.right()+8,0);
            if (self.b_remainingTime):
                minsize += QtCore.QSize(self.fontMetrics().size(0,"-",0,None).width(),0);
        if (self.displayType==self.Display.Elapsed):
            self.setMinimumSize(minsize);
            self.setText(psz_time);
        elif (self.displayType==self.Display.Remaining):
            if (self.b_remainingTime):
                self.setMinimumSize(minsize);
                self.setText("-"+psz_time);
            else:
                self.setMinimumSize(0, 0);
                self.setText(self.psz_length);
        elif (self.displayType==self.Display.Both):
            timestr = "{0}{1}/{2}".format(
                                          "-" if (self.b_remainingTime and i_length) else "",
                                          psz_time,
                                          "--:--" if (not self.psz_length) else self.psz_length);
            self.setText(timestr);
        self.cachedLength = i_length;
    def toggleTimeDisplay(self):
        self.b_remainingTime = not self.b_remainingTime;
        #self.getSettings().setValue("MainWindow/ShowRemainingTime",self.b_remainingTime);
    def updateBuffering(self,f_buffered=None):
        if (f_buffered is not None):
            self.bufVal = f_buffered;
            if (not self.buffering or self.bufVal==0):
                self.showBuffering = False;
                self.buffering = True;
                self.bufTimer.start(200);
            elif (self.bufVal==1):
                self.showBuffering = self.buffering = False;
                self.bufTimer.stop();
        else:
            self.showBuffering = True;
        self.update();
    def paintEvent(self, event):
        if (self.showBuffering):
            r = self.rect();
            r.setLeft(r.width()*self.bufVal);
            p = QtGui.QPainter(self);
            p.setOpacity(0.4);
            p.fillRect(r,self.palette().color(QtGui.QPalette.Highlight));
        super(TimeLabel,self).paintEvent(event)
    def mousePressEvent(self, event):
        if (self.displayType==self.Display.Elapsed): return;
        self.toggleTimeDisplay();
        event.accept();
    def mouseDoubleClickEvent(self, event):
        if (self.displayType!=self.Display.Both): return;
        event.accept();
        self.toggleTimeDisplay();
        self.emit(QtCore.SIGNAL("doubleClicked(void)"));

class SoundWidget(QtGui.QWidget):
    #public:
        #SoundWidget(QWidget parent, Application app, bool b_shiny, bool b_special=False)
        #virtual ~SoundWidget()
        #void setMuted(bool muted)
    #protected:
        #virtual bool eventFilter(QObject sender, QEvent event)
    #private:
        #Application        app
        #QLabel             volMuteLabel
        #QAbstractSlider    volumeSlider
        #QFrame             volumeControlWidget
        #QMenu              volumeMenu
        #bool               b_is_muted
        #bool               b_ignore_valuechanged
    #protected slots:
        #userUpdateVolume(int)
        #libUpdateVolume(void)
        #updateMuteStatus(void)
        #refreshLabels(void)
        #showVolumeMenu(QPoint pos)
        #valueChangedFilter(int)
    #signals
        #valueReallyChanged(int)
        #volumeChanged(int)
        #muteChanged(bool)
    def __init__(self, parent, b_shiny, b_special=False):
        super(SoundWidget, self).__init__(parent);
        self.logger = const.root_logger.getChild("SoundWidget");
        self.b_is_muted = False;
        self.b_ignore_valuechanged = False;
        
        #We need a layout for this widget
        layout = QtGui.QHBoxLayout(self);
        layout.setSpacing(0); layout.setMargin(0);
        
        #We need a label for the pix
        self.volMuteLabel = QtGui.QLabel();
        self.volMuteLabel.setPixmap(QtGui.QPixmap(":/toolbar/volume-medium"));
        
        #We might need a subLayout too
        subLayout = None;
        
        self.volMuteLabel.installEventFilter(self);
        
        if (not b_special):
            #Normal view, click on icon mutes
            self.volumeMenu = self.volumeControlWidget = None;
            #And add the label
            layout.addWidget(self.volMuteLabel);
        else:
            #Special view, click on button shows the slider
            b_shiny = False;
            
            self.volumeControlWidget = QtGui.QFrame();
            subLayout = QtGui.QVBoxLayout(self.volumeControlWidget);
            subLayout.setContentsMargins(4, 4, 4, 4);
            self.volumeMenu = QtGui.QMenu(self);
            
            widgetAction = QtGui.QWidgetAction(self.volumeControlWidget);
            widgetAction.setDefaultWidget(self.volumeControlWidget);
            self.volumeMenu.addAction(widgetAction);
            
            #And add the label
        
        #Slider creation: shiny or clean
        if (b_shiny):
            self.volumeSlider = SoundSlider(self, 
                                            const.VOLUME_STEP, 
                                            False, 
                                            const.QT_SLIDER_COLORS);
        else:
            self.volumeSlider = QtGui.QSlider(None);
            self.volumeSlider.setAttribute(QtCore.Qt.WA_MacSmallSize);
            self.volumeSlider.setOrientation(QtCore.Qt.Vertical if b_special else QtCore.Qt.Horizontal);
            self.volumeSlider.setMaximum(const.VOLUME_MAX);
        self.volumeSlider.setFocusPolicy(QtCore.Qt.NoFocus);
        if (b_special):
            subLayout.addWidget(self.volumeSlider);
        else:
            layout.addWidget(self.volumeSlider, 0, QtCore.Qt.AlignBottom);
        
        #Set the volume from the config
        #self.libUpdateVolume();
        #Force the update at build time in order to have a muted icon if needed
        #self.updateMuteStatus();
        
        #Volume control connection
        self.volumeSlider.setTracking(True);
        self.connect(self.volumeSlider, QtCore.SIGNAL("valueChanged(int)"), self.valueChangedFilter);
        self.connect(self, QtCore.SIGNAL("valueReallyChanged(int)"), self.userUpdateVolume);
        self.connect(self, QtCore.SIGNAL("muteChanged(bool)"), self.updateMuteStatus)
    
    #Python GC handles __del__/~SoundWidget
    
    def refreshLabels(self):
        i_sliderVolume = self.volumeSlider.value();
        
        if (self.b_is_muted):
            self.volMuteLabel.setPixmap(QtGui.QPixmap(":/toolbar/volume-muted"));
            self.volMuteLabel.setToolTip(QtCore.QCoreApplication.translate("SoundWidget", "UnMute"));
            return;
        
        if (i_sliderVolume<const.VOLUME_MAX/3):
            self.volMuteLabel.setPixmap(QtGui.QPixmap(":/toolbar/volume-low"));
        elif (i_sliderVolume>(const.VOLUME_MAX*2/3)):
            self.volMuteLabel.setPixmap(QtGui.QPixmap(":/toolbar/volume-high"));
        else:
            self.volMuteLabel.setPixmap(QtGui.QPixmap(":/toolbar/volume-medium"));
        
        self.volMuteLabel.setToolTip(QtCore.QCoreApplication.translate("SoundWidget", "Mute"));
    
    def userUpdateVolume(self, i_sliderVolume):
        """ volumeSlider Changed Value event slot """
        #Only if volume is set by user action on slider
        self.setMuted(False);
        self.emit(QtCore.SIGNAL("volumeChanged(int)"), i_sliderVolume)
        self.refreshLabels();
    
    def libUpdateVolume(self, vol):
        """ libvlc changed value event slot"""
        if (vol - self.volumeSlider.value() != 0):
            self.b_ignore_valuechanged = True;
            self.volumeSlider.setValue(vol);
            self.b_ignore_valuechanged = False;
        self.refreshLabels()
    
    def valueChangedFilter(self, i_val):
        """ valueChanged is also emitted if the lib calls setValue() """
        if (not self.b_ignore_valuechanged):
            self.emit(QtCore.SIGNAL("valueReallyChanged(int)"), i_val);
    
    def updateMuteStatus(self, b_mute):
        """ libvlc mute/unmute event slot"""
        self.b_is_muted = b_mute;
        if (hasattr(self.volumeSlider, "setMuted")):
            self.volumeSlider.setMuted(self.b_is_muted);
        self.refreshLabels();
    
    def showVolumeMenu(self, pos):
        self.volumeMenu.setFixedHeight(self.volumeMenu.sizeHint().height());
        self.volumeMenu.exec_(QtGui.QCursor.pos() - pos - QtCore.QPoint( 0, self.volumeMenu.height()/2 )
                                + QtCore.QPoint( self.width(), self.height() /2));
    
    def setMuted(self, b_mute):
        self.b_is_muted = b_mute;
        self.emit(QtCore.SIGNAL("muteChanged(bool)"), b_mute)
    
    def eventFilter(self, sender, event):
        if (event.type() == QtCore.QEvent.MouseButtonPress) and (event.button() == QtCore.Qt.LeftButton):
            if(self.volumeSlider.orientation()==QtCore.Qt.Vertical):
                self.showVolumeMenu(event.pos());
            else:
                self.setMuted(not self.b_is_muted);
            event.accept();
            return True;
        event.ignore();
        return False;
    

class PlayButton(QtGui.QToolButton):
    #private slots:
        #updateButtonIcons(bool)
    def updateButtonIcons(self, b_playing):
        self.setIcon(QtGui.QIcon(
            ":/toolbar/pause_b" if b_playing else ":/toolbar/play_b"));
        self.setToolTip(QtCore.QCoreApplication.translate("PlayButton", 
            "Pause the playback" if b_playing else "Play"));

class LoopButton(QtGui.QToolButton):
    #private slots:
        #updateButtonicons(int)
    LoopMode = AutoEnum("LoopMode", "NORMAL", "REPEAT_ONE", "REPEAT_ALL");
    def updateButtonIcons(self, value):
        self.setChecked(value != self.LoopMode.NORMAL);
        self.setIcon(QtGui.QIcon(
            ":/toolbar/repeat_one" if value == self.LoopMode.REPEAT_ONE else \
            ":/toolbar/repeat_all"));

