'''
/*****************************************************************************
 * controller.py : Controller for the main interface
 ****************************************************************************
 * Copyright (C) 2006-2009 the VideoLAN team
 * $Id: b47d1e2d85071b9e1d9796c87e2c67f8f29dfc82 $
 *
 * Authors: Jean-Baptiste Kempf <jb@videolan.org>
 *          Ilkka Ollakka <ileoo@videolan.org>
 *          Orochimarufan <orochimarufan.x3@gmail.com> [Python]
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * ( at your option ) any later version.
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
'''

from __future__ import absolute_import,unicode_literals;

from PyQt4 import QtGui,QtCore;

from . import const
from . import util
from . import widgets
from . import libvlc
#from .actions_manager import actionType_e

import sys


widgetType_e = util.Enum("widgetType_e",
        # Buttons
#        PLAY_BUTTON=ACTION.PLAY_ACTION,
#        STOP_BUTTON=ACTION.STOP_ACTION,
#        FULLSCREEN_BUTTON=ACTION.FULLSCREEN_ACTION,
        # Special Widgets
        TIME_LABEL=0x20,
        VOLUME_SLIDER=0x21,
        SEEK_SLIDER=0x22,
        # Spacers
        SPACER=0x40,
        SPACER_EXTEND=0x41,
        # Custom Actions
#        OPENYT_BUTTON=ACTION.OPEN_YOUTUBE_ACTION,
)
widgetType_e.BUTTON_MAX = 0x20;
widgetType_e.SPECIAL_MAX = 0x40;
widgetType_e.SPACER_MAX = 0x50;
widgetType_e.WIDGET_MAX = 0x60;

widgetType_e.export();
#actionType_e.export();
ACTION= None


class AbstractController(QtGui.QFrame):
    def __init__(self,app,parent):
        super(AbstractController,self).__init__(parent);
        self.app = app;
        self.logger = app.logger_ui.getChild(self.__class__.__name__);

        self.mapper = QtCore.QSignalMapper(self);
        self.connect(self.mapper,QtCore.SIGNAL("mapped(int)"),self.app.ActionsManager.doAction);
        self.connect(self.app.Player, QtCore.SIGNAL("playingStateChanged(int)"), self.setStatus);
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.Expanding);

        self.buttonGroupLayout = None;

    def setStatus(self, iState):
        self.emit(self,QtCore.SIGNAL("playing(bool)"),iState = libvlc.S_PLAYING);

    def setupButton(self, button):
        sp = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed);
        sp.setHorizontalStretch(0);
        sp.setVerticalStretch(0);
        button.setSizePolicy(sp);
        button.setFixedSize(26,26);
        button.setIconSize(20,20);
        button.setFocusPolicy(QtCore.Qt.NoFocus);
    def mapWidget(self, widget, tp):
        self.connect(widget,QtCore.SIGNAL("clicked()"),self.mapper,QtCore.SLOT("map()"));
        self.mapper.setMapping(widget,tp);
    def setWidgetBar(self, widget, tp):
        self.setWidgetBar2(widget,None,None)
    def setWidgetBar2(self,widget,image,tooltip):
        widget.setToolTip(self.app.translate("Controller",tooltip));
        widget.setIcon(QtGui.QIcon(image));
    def defWidget(self, tp):
        button = QtGui.QToolButton(self);
        self.setupButton(button);
        self.mapWidget(button, tp);
        self.setWidgetBar(button, tp);
        return button;

    def createWidget(self, tp, opt):

        if (tp==PLAY_BUTTON):
            widget = widgets.PlayButton(self.app);
            self.setupButton(widget);
            self.setWidgetBar(widget, PLAY_ACTION);
            self.mapWidget(widget, PLAY_ACTION);
            self.connect(self,QtCore.SIGNAL("playing(bool)"),widget.updateButtonIcons);
        elif (tp == STOP_BUTTON):
            widget = self.defWidget(STOP_ACTION);
        elif (tp == FULLSCREEN_BUTTON):
            widget = self.defWidget(FULLSCREEN_ACTION);
        elif (tp == TIME_LABEL):
            widget = widgets.TimeLabel(self.app,widgets.TimeLabel.Display.Both);
        elif (tp == VOLUME_SLIDER):
            widget = widgets.VolumeVidget(self.app);
        elif (tp == SEEK_SLIDER):
            widget = widgets.SeekSlider(self.app);
        else:
            self.logger.warn("This should not have happened (Unknown Widget Type) %i"%tp);

    def parseAndCreate(self,ui_string,layout):
        lst = ui_string.split(":");
        for i in lst:
            lst2 = i.split("-");
            i_option = 0x0;
            try:
                i_type = int(lst2[0]);
            except ValueError:
                self.logger.warn("Parsing Error 2. Please report this.",exc_info = sys.exc_info());
                continue;
            except IndexError:
                self.logger.warn("Parsing Error 1. Please report this.",exc_info = sys.exc_info());
                continue;
            if (len(lst2)>1):
                try:
                    i_option = int(lst2[1]);
                except ValueError:
                    self.logger.warn("Parsing Error 3. Please report this.",exc_info = sys.exc_info());
            self.createAndAddWidget(layout,i_type,i_option);
        if (self.buttonGroupLayout):
            layout.addLayout(self.buttonGroupLayout);
            self.buttonGroupLayout = None;
    def createAndAddWidget(self, layout, i_type, i_option):
        if (i_type>0x20):
            # Close current buttonGroup if we have a special widget or spacer
            layout.addLayout(self.buttonGroupLayout);
            self.buttonGroupLayout = None;
        if (i_type==WIDGETS.SPACER):
            layout.addSpacing(12);
        elif (i_type==WIDGETS.SPACER_EXTEND):
            layout.addStretch(12);
        else:
            widget = self.createWidget(i_type, i_option);
            if i_type<0x20:
                # Buttons
                if (not self.buttonGroupLayout):
                    self.buttonGroupLayout = QtGui.QHBoxLayout();
                self.buttonGroupLayout.addWidget(widget);
            else:
                # Special Widgets
                layout.addWidget(widget);

class FullscreenControllerWidget(AbstractController):
    def __init__(self,app,parent):
        super(FullscreenControllerWidget,self).__init__(app,parent);

        self.i_mouse_last_x      = -1;
        self.i_mouse_last_y      = -1;
        self.b_mouse_over        = False;
        self.i_mouse_last_move_x = -1;
        self.i_mouse_last_move_y = -1;
        self.b_fullscreen        = False;
        self.i_hide_timeout      = 1;
        self.i_screennumber      = -1;

        self.setWindowFlags(QtCore.Qt.ToolTip);
        self.setMinimumSize(const.FSC_WIDTH,const.FSC_HEIGHT);
        self.isWideFSC = False;

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
        #self.i_screennumber = 0;

    def __del__(self):
        self.getSettings().setValue("FullScreen/pos",self.previousPosition);
        self.getSettings().setValue("FullScreen/screen",self.screenRes);
        self.getSettings().setValue("FullScreen/wide",self.isWideFSC);

    def restoreFSC(self):
        self.logger.debug("Wide: %s"%self.isWideFSC)
        if (not self.isWideFSC):
            # restore Half-bar and re-center it if needed
            self.setMinimumWidth(const.FSC_WIDTH);
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
#ifdef Q_WS_X11
#    // Tell kwin that we do not want a shadow around the fscontroller
#    setMask( QRegion( 0, 0, width(), height() ) );
#endif

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

    def targetScreen(self):
        if (self.i_screennumber==-1 or self.i_screennumber>QtGui.QApplication.desktop().numScreens()):
            return QtGui.QApplication.desktop().screenNumber(self.app.video_widget);
        return self.i_screennumber;

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


