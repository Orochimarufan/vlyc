"""
/*****************************************************************************
 * vlyc :: fullscreen.py : Fullscreen handling
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

from PyQt4 import QtCore, QtGui
from . import const
from . import util

class Controller(QtGui.QFrame):#type("FullscreenController", (QtGui.QFrame, ), dict(FullscreenControllerWidget.__dict__))):
    def __init__(self,parent):
        super(Controller,self).__init__(parent)

        self.logger = const.root_logger.getChild("FullscreenController") #@UndefinedVariable

        self.i_mouse_last_x      = -1;
        self.i_mouse_last_y      = -1;
        self.b_mouse_over        = False;
        self.i_mouse_last_move_x = -1;
        self.i_mouse_last_move_y = -1;
        self.b_fullscreen        = False;
        self.i_hide_timeout      = 5000;
        self.i_screennumber      = -1;

        self.setWindowFlags(QtCore.Qt.ToolTip);

        self.setFrameShape(QtGui.QFrame.StyledPanel);
        self.setFrameStyle(QtGui.QFrame.Sunken);
        self.setSizePolicy(QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Minimum);

        self.controlLayout = QtGui.QVBoxLayout(self);
        self.controlLayout.setContentsMargins(0, 0, 0, 0);

        self.inputLayout = self.createUiInput();
        self.controlLayout.addLayout(self.inputLayout);

        self.fscLayout = self.createUiFscToolbar();
        self.controlLayout.addLayout(self.fscLayout);

        self.p_hideTimer = QtCore.QTimer(self);
        self.p_hideTimer.setSingleShot(True);
        self.connect(self.p_hideTimer, QtCore.SIGNAL("timeout()"),
                     self.hideFSC);

        self.previousPosition = self.getSettings().value("FullScreen/pos",QtCore.QPoint(0,0));
        self.screenRes = self.getSettings().value("FullScreen/screen",None);
        self.isWideFSC = (self.getSettings().value("FullScreen/wide",False) not in ("false", False, "False"));
        self.halfSize = self.getSettings().value("FullScreen/size",QtCore.QSize(const.FSC_WIDTH,const.FSC_HEIGHT));

        self.setMinimumSize(self.halfSize)
        #self.i_screennumber = 0;

    def setFullscreen(self, b_fs):
        const.root_logger.getChild("FullscreenController").debug("Setting Fullscreen: %s"%b_fs) #@UndefinedVariable
        self.b_fullscreen = b_fs
        vw = self.parentWidget()
        vw.setMouseTracking(b_fs)
        if b_fs:
            vw.mM.connect(self.mouseChanged)
        else:
            vw.mM.disconnect(self.mouseChanged)
            self.hideFSC()

    def targetScreen(self):
        if (self.i_screennumber==-1 or self.i_screennumber>QtGui.QApplication.desktop().numScreens()):
            return QtGui.QApplication.desktop().screenNumber(self.parentWidget());
        return self.i_screennumber;

    def restoreFSC(self):
        if (not self.isWideFSC):
            # restore Half-bar and re-center it if needed
            self.setMinimumWidth(self.halfSize.width());
            self.adjustSize();

            currentRes = QtGui.QApplication.desktop().screenGeometry(self.targetScreen());

            if (currentRes == self.screenRes and \
                QtGui.QApplication.desktop().screen().geometry().contains(self.previousPosition,True)):
                # Restore to the last known position
                self.move(self.previousPosition);
            else:
                # FSC is out of screen or screen Resolution changed
                self.logger.debug("Recentering the Fullscreen Controller");
                self.centerFSC(self.targetScreen());
                self.screenRes = currentRes;
                self.previousPosition = self.pos();
        else:
            # Dock at the bottom of the screen
            self.updateFullWidthGeometry(self.targetScreen());

    def savePosition(self):
        self.getSettings().setValue("FullScreen/pos",self.previousPosition)
        self.getSettings().setValue("Fullscreen/screen",self.screenRes)
        self.getSettings().setValue("FullScreen/wide",self.isWideFSC)
        self.getSettings().setValue("FullScreen/size",self.halfSize)

    def centerFSC(self, number):
        currentRes = QtGui.QApplication.desktop().screenGeometry(number);

        # screen has changed, calculate a new position
        pos = QtCore.QPoint(currentRes.x() + (currentRes.width()/2) - (self.width()/2),
                            currentRes.y() + currentRes.height() - self.height() );
        self.move(pos);

    def showFSC(self):
        """ Show Fullscreen Controller """
        self.restoreFSC();
        self.show();

    def hideFSC(self):
        self.hide()

    def planHideFSC(self):
        """ Plan to hide fullscreen Controller """
        i_timeout = self.i_hide_timeout;

        self.p_hideTimer.start(i_timeout);

    def updateFullWidthGeometry(self, number):
        screenGeometry = QtGui.QApplication.desktop().screenGeometry(number);
        self.setMinimumWidth(screenGeometry.width());
        self.setGeometry(screenGeometry.x(), screenGeometry.y() + screenGeometry.height() - self.height(), screenGeometry.width(), self.height());
        self.adjustSize();

    def toggleFullWidth(self):
        self.isWideFSC = not self.isWideFSC;
        self.restoreFSC();

    Event = util.Enum("Event",
        Hide = QtCore.QEvent.registerEventType(),
        Show = QtCore.QEvent.registerEventType(),
        Toggle = QtCore.QEvent.registerEventType(),
        PlanHide = QtCore.QEvent.registerEventType() )

    def customEvent(self, event):
        """
        Event Handling
        events: show, hide, show timer for hiding
        """
        if (event.type()==self.Event.Toggle):
            # Hotkey toggle
            if (self.b_fullscreen):
                if (self.isHidden()):
                    self.p_hideTimer.stop();
                    self.showFSC();
                else:
                    self.hideFSC();
        elif (event.type()==self.Event.Show):
            # Event called to show the FSC on mouseChanged
            if (self.b_fullscreen):
                self.showFSC();
        elif (event.type()==self.Event.PlanHide):
            # Start the timer to hide later, called usually with above case
            if (not self.b_mouse_over):
                self.planHideFSC();
        elif (event.type()==self.Event.Hide):
            # Hide
            self.hideFSC();

    def mouseMoveEvent(self, event):
        """
        On mouse move
        moving with FSC
        """
        if (event.buttons()==QtCore.Qt.LeftButton):
            if (self.i_mouse_last_x==-1 or self.i_mouse_last_y==-1):
                return;

            i_moveX = event.globalX() - self.i_mouse_last_x;
            i_moveY = event.globalY() - self.i_mouse_last_y;

            self.move(self.x()+i_moveX, self.y()+i_moveY);

            self.i_mouse_last_x = event.globalX();
            self.i_mouse_last_y = event.globalY();

    def mousePressEvent(self, event):
        """
        On mouse press
        store position of cursor
        """
        if (self.isWideFSC): return;
        self.i_mouse_last_x = event.globalX();
        self.i_mouse_last_y = event.globalY();
        event.accept();

    def mouseReleaseEvent(self, event):
        if (self.isWideFSC): return;
        self.i_mouse_last_x = -1;
        self.i_mouse_last_y = -1;
        event.accept();

        # Save the new FSC position
        self.previousPosition = self.pos();

    def enterEvent(self, event):
        """ On mouse go above FSC """
        self.b_mouse_over = True;
        self.p_hideTimer.stop();
#if HAVE_TRANSPARENCY
#    p_slowHideTimer->stop();
#    setWindowOpacity( f_opacity );
#endif
        event.accept();

    def leaveEvent(self, event):
        """ On mouse leave from FSC """
        self.b_mouse_over = False;
        self.planHideFSC();
        event.accept();

    def keyPressEvent(self, event):
        """ When you get pressed key, emit a signal """
        self.emit(QtCore.SIGNAL("keyPressed(QKeyEvent)"),event);

    def fullscreenChanged(self, b_fs, i_timeout):
        if (b_fs and not self.b_fullscreen):
            # Entering fullscreen, registering callback
            self.logger.debug("Entering fullscreen");
            self.b_fullscreen = True;
            self.i_hide_timeout = i_timeout;
            #TDOD: callback?
        elif (not b_fs and self.b_fullscreen):
            # Quitting Fullscreen, unregistering callback
            self.logger.debug("Leaving fullscreen");
            self.b_fullscreen = False;
            self.i_hide_timeout = i_timeout;
            #TODO: callback?
            QtGui.qApp.postEvent(self, QtCore.QEvent(self.Event.Hide));

    def mouseChanged(self, i_mousex, i_mousey):
        """ Mouse Change Callback (show/hide the controller on mouse movement) """
        b_toShow = False;
        if (self.i_mouse_last_move_x==-1 or self.i_mouse_last_move_y==-1 or \
            abs(self.i_mouse_last_move_x-i_mousex)>2 or \
            abs(self.i_mouse_last_move_y-i_mousey)>2):
            self.i_mouse_last_move_x = i_mousex;
            self.i_mouse_last_move_y = i_mousey;
            b_toShow = True;
        #const.root_logger.getChild("FSC").debug("Showing FSC: %s"%b_toShow)
        if (b_toShow):
            # Show Event
            QtGui.qApp.postEvent(self, QtCore.QEvent(self.Event.Show));
            # Plan Hide Event
            QtGui.qApp.postEvent(self, QtCore.QEvent(self.Event.PlanHide));
