#!/usr/bin/python3
"""
/*****************************************************************************
 * vlyc2.py : VLC Youtube Player
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

from __future__ import absolute_import, unicode_literals, print_function, division
from sip import setapi
setapi("QString", 2)
from PyQt4 import QtCore, QtGui
import logging, re, sys, os
from vlyc import const
const.root_logger = logging.getLogger("vlyc.gui")
from vlyc import player, vlc_res, input_slider, widgets #@UnresolvedImport
from vlyc.controller import FullscreenControllerWidget
from libyo.youtube import resolve#,subtitles #@UnresolvedImport
from libyo.youtube.resolve import profiles #@UnresolvedImport
from libyo.util.util import sdict_parser #@UnresolvedImport
from libyo.argparse import LibyoArgumentParser #@UnresolvedImport
from libyo.compat.uni import u as unicode, nativestring #@UnresolvedImport
from collections import OrderedDict

_unused = [vlc_res]; del _unused

class MainWindow(QtGui.QMainWindow):
    def setupUi(self):
        #/---------------------------------------
        # Main Window
        #---------------------------------------/
        self.setObjectName("MainWindow")
        self.resize(700, 500)

        self.root_widget = QtGui.QWidget(self)
        self.root_widget.setObjectName("root_widget")

        self.root_layout = QtGui.QVBoxLayout(self.root_widget)
        self.root_layout.setObjectName("root_layout")

        #/---------------------------------------
        # Video Widget
        #---------------------------------------/
        self.video_widget = widgets.VideoWidget(self.root_widget)
        self.video_widget.setObjectName("video_widget")
        self.video_widget.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        palette = self.video_widget.palette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(0,0,0))
        self.video_widget.setPalette(palette)
        self.video_widget.setAutoFillBackground(True)
        self.root_layout.addWidget(self.video_widget)

        #/---------------------------------------
        # Time Toolbar
        #---------------------------------------/
        self.time_layout = QtGui.QHBoxLayout()
        self.time_layout.setObjectName("time_layout")

        self.seeker = input_slider.SeekSlider(QtCore.Qt.Horizontal, self.root_widget, self.getSettings().value("MainWindow/classic_slider",False))
        self.seeker.setObjectName("seeker")
        self.time_layout.addWidget(self.seeker)

        self.time_label = widgets.TimeLabel(widgets.TimeLabel.Display.Both) #@UndefinedVariable
        self.time_label.setObjectName("time_label")
        self.time_layout.addWidget(self.time_label)

        self.root_layout.addLayout(self.time_layout)

        #/---------------------------------------
        # Control Toolbar
        #---------------------------------------/
        self.control_layout = QtGui.QHBoxLayout()
        self.control_layout.setObjectName("control_layout")

        self.play_button = widgets.PlayButton(self.root_widget)
        self.play_button.setObjectName("play_button")
        self.play_button.setIcon(QtGui.QIcon(":/toolbar/play_b"))
        self.play_button.setShortcut(" ")
        self.play_button.setFocusPolicy(QtCore.Qt.NoFocus)
        #self.play_button.setFixedSize(self.play_button.width(), self.play_button.height())
        self.control_layout.addWidget(self.play_button)

        self.stop_button = QtGui.QToolButton(self.root_widget)
        self.stop_button.setObjectName("stop_button")
        self.stop_button.setIcon(QtGui.QIcon(":/toolbar/stop_b"))
        self.stop_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.control_layout.addWidget(self.stop_button)

        self.control_layout.addStretch(120)

        self.fullscreen_button = QtGui.QToolButton(self.root_widget)
        self.fullscreen_button.setObjectName("fullscreen_button")
        self.fullscreen_button.setIcon(QtGui.QIcon(":/toolbar/fullscreen"))
        self.fullscreen_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.control_layout.addWidget(self.fullscreen_button)

        self.quality_combo = QtGui.QComboBox(self.root_widget)
        self.quality_combo.setObjectName("quality_combo")
        self.quality_combo.setFocusPolicy(QtCore.Qt.NoFocus)
        self.control_layout.addWidget(self.quality_combo)

        self.sound_widget = widgets.SoundWidget(self.root_widget, self.getSettings().value("MainWindow/shiny_sound",True))
        self.sound_widget.setObjectName("sound_widget")
        self.sound_widget.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.sound_widget.setFocusPolicy(QtCore.Qt.NoFocus)
        self.control_layout.addWidget(self.sound_widget)

        self.root_layout.addLayout(self.control_layout)
        self.setCentralWidget(self.root_widget)

        #/---------------------------------------
        # Menu Bar
        #---------------------------------------/
        self.menubar = QtGui.QMenuBar(self)
        self.menubar.setObjectName("menubar")
        #self.menubar.setGeomatry(0,0,700,25)

        self.file_menu = self.menubar.addMenu("&File")
        self.file_menu.setObjectName("file_menu")

        self.file_open_menu = self.file_menu.addMenu("&Open")
        self.file_open_menu.setObjectName("file_open_menu")

        self.file_open_youtube_action = self.file_open_menu.addAction("&YouTube Video")
        self.file_open_youtube_action.setObjectName("file_open_youtube_action")
        self.file_open_youtube_action.setShortcut("Ctrl+Y")

        self.file_open_file_action = self.file_open_menu.addAction("&File")
        self.file_open_file_action.setObjectName("file_open_file_action")
        self.file_open_file_action.setShortcut("Ctrl+O")

        self.file_open_stream_action = self.file_open_menu.addAction("&Network Stream")
        self.file_open_stream_action.setObjectName("file_open_stream_action")
        self.file_open_stream_action.setShortcut("Ctrl+N")

        self.file_menu.addSeparator()

        self.file_quit_action = self.file_menu.addAction("&Quit")
        self.file_quit_action.setObjectName("file_quit_action")
        self.file_quit_action.setShortcut("Ctrl+Q")

        self.setMenuBar(self.menubar)

        #/---------------------------------------
        # Status Bar
        #---------------------------------------/
        self.statusbar = QtGui.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")

        self.setStatusBar(self.statusbar)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi()
        self.resize(self.getSettings().value("MainWindow/size",self.size()))
        self.move(self.getSettings().value("MainWindow/position",self.pos()))

    def savePosition(self):
        const.root_logger.debug("MainWindow: saving position") #@UndefinedVariable
        self.getSettings().setValue("MainWindow/position",self.pos())
        self.getSettings().setValue("MainWindow/size",self.size())

class FullscreenController(type("FullscreenController", (QtGui.QFrame, ), dict(FullscreenControllerWidget.__dict__))):
    """
    Quick Fix for non-availability of the Full VLC-qt4 Controller Interface
    """
    def __init__(self,parent):
        QtGui.QFrame.__init__(self,parent) #No super magic because of our monkey-patching (see the class def line ;))

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

    def createUiInput(self):
        layout = QtGui.QHBoxLayout()

        self.seeker = input_slider.SeekSlider(QtCore.Qt.Horizontal, None, True)
        self.seeker.setObjectName("fscSeeker")
        layout.addWidget(self.seeker)

        self.time_label = widgets.TimeLabel(widgets.TimeLabel.Display.Both) #@UndefinedVariable
        self.time_label.setObjectName("fscTimeLabel")
        layout.addWidget(self.time_label)

        return layout

    def createUiFscToolbar(self):
        layout = QtGui.QHBoxLayout()

        self.play_b = widgets.PlayButton()
        self.play_b.setObjectName("fscPlayButton")
        layout.addWidget(self.play_b)

        self.stop_b = QtGui.QToolButton()
        self.stop_b.setObjectName("fscStopButton")
        self.stop_b.setIcon(QtGui.QIcon(":/toolbar/stop_b"))
        layout.addWidget(self.stop_b)

        layout.addSpacing(50)

        self.fullscreen = QtGui.QToolButton()
        self.fullscreen.setObjectName("fscFullscreenButton")
        self.fullscreen.setIcon(QtGui.QIcon(":/toolbar/defullscreen"))
        layout.addWidget(self.fullscreen)

        layout.addStretch(100)

        self.sound_w = widgets.SoundWidget(None, True)
        self.sound_w.setObjectName("fscSoundWidget")
        layout.addWidget(self.sound_w)

        return layout

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

    __del__ = None

    def savePosition(self):
        self.getSettings().setValue("FullScreen/pos",self.previousPosition)
        self.getSettings().setValue("Fullscreen/screen",self.screenRes)
        self.getSettings().setValue("FullScreen/wide",self.isWideFSC)
        self.getSettings().setValue("FullScreen/size",self.halfSize)

class VlycApplication(QtGui.QApplication):
    """
    A VLYC Player Application
    """
    youtube_regexp = re.compile(r"^.+youtube\..{2,3}\/watch\?(.+)$")
    youtube_message= """URL does not seem to be a valid YouTube Video URL:\r\n{0}"""
    resolve_message= """Could not resolve Video: {0}\r\n(Are you sure your Internet connection is Up?)"""
    window_title_1 = """VideoLan Youtube Client"""
    window_title_2 = """{0} -- VLYC"""
    main_q_lookup = list(profiles.profiles["mixed-avc"][0].values())
    pref_q_lookup = [18,5]

    logger          = logging.getLogger("vlyc")
    logger_ui       = logger.getChild("ui")
    logger_youtube  = logger.getChild("youtube")
    logger_player   = logger.getChild("player")
    logger_event    = logger.getChild("evtmgr")

    def __init__(self, argv=None):
        if argv is None:
            argv = sys.argv;
        super(VlycApplication, self).__init__(argv)

        self.setOrganizationDomain("fanirc.net")
        self.setOrganizationName("Orochimarufan")
        self.setApplicationName("VLYC")

        self.argument_parser = LibyoArgumentParser(prog = self.arguments()[0], usage = "%(prog)s [MRL] [--- ARG [...]]")
        self.argument_parser.add_argument(metavar="MRL", nargs="?", dest="init_mrl", type=unicode,
                                          help="Play this file/MRL at startup")
        self.argument_parser.add_argument("--fullscreen",action="store_true",
                                          help="Start in Fullscreen Mode (only if MRL is given)")
        self.argument_parser.add_argument("--quit",action="store_true", dest="quit_after",
                                          help="Quit after playing MRL")
        self.argument_parser.add_argument("---", metavar="", nargs="A...?", dest="vlcargs",
                                          type=player.vlcstring, action="append", default=None,
                                          help="Pass all remaining args to libvlc directly. For help, try '%(prog)s --- --help'. Not all listed Arguments will work as expected! Use on your own account")

    def argument_parser_execute(self):
        self.args = self.argument_parser.parse_args(self.arguments()[1:])

    def main(self):
        #/---------------------------------------
        # Parse CommandLine Parameters
        #---------------------------------------/
        self.argument_parser_execute()

        #/---------------------------------------
        # Load Settings
        #---------------------------------------/
        self.settings = QtCore.QSettings()
        const.QT_SLIDER_COLORS = self.settings.value("SeekSlider/Colors", const.QT_SLIDER_COLORS)
        const.FSC_HEIGHT = self.settings.value("Fullscreen/Height", const.FSC_HEIGHT)
        const.FSC_WIDTH = self.settings.value("Fullscreen/Width", const.FSC_WIDTH)
        const.VOLUME_STEP = self.settings.value("SoundWidget/Step", const.VOLUME_STEP)
        QtCore.QObject.getSettings = lambda o: self.settings #TODO: is that the right way to do it?

        #/---------------------------------------
        # Initialize Player and GUI
        #---------------------------------------/
        self.main_window = MainWindow()
        if self.args.vlcargs is not None:
            if not player.initInstance(self.args.vlcargs):
                return 0 #Help and version will not create an instance and should exit!
        self.player = player.Player()
        self.main_window.setWindowTitle(self.window_title_1)
        self.player.mediaChanged.connect(self.newMedia)

        #/---------------------------------------
        # Initialize Attributes
        #---------------------------------------/
        self.uilock = False
        self.length = -1
        self.b_fullscreen = False
        self.fs_controller = None

        #/---------------------------------------
        # MenuBar Actions
        #---------------------------------------/
        self.main_window.file_quit_action.triggered.connect(self.quit)
        self.main_window.file_open_youtube_action.triggered.connect(self.open_vid)
        self.main_window.file_open_file_action.triggered.connect(self.open_file)
        self.main_window.file_open_stream_action.triggered.connect(self.open_mrl)

        #/---------------------------------------
        # Time Toolbar Actions
        #---------------------------------------/
        self.connect(self.main_window.seeker, QtCore.SIGNAL("sliderDragged(float)"), self.player.set_position)
        self.player.positionChanged.connect(self.posChange)
        self.player.timeChanged.connect(self.timeChange)
        self.player.stateChanged.connect(self.stateChange)
        self.player.buffering.connect(self.main_window.time_label.updateBuffering)
        self.player.buffering.connect(self.main_window.seeker.updateBuffering)

        #/---------------------------------------
        # Control Toolbar Actions
        #---------------------------------------/
        self.main_window.play_button.clicked.connect(self.toggle_pause)
        self.main_window.stop_button.clicked.connect(self.stop)
        self.connect(self.main_window.sound_widget, QtCore.SIGNAL("volumeChanged(int)"), self.player.audio_set_volume)
        self.connect(self.main_window.sound_widget, QtCore.SIGNAL("muteChanged(bool)"), self.player.audio_set_mute)
        self.main_window.sound_widget.libUpdateVolume(self.player.audio_get_volume())
        self.main_window.sound_widget.updateMuteStatus(self.player.audio_get_mute())
        #self.main_window.quality_combo.currentIndexChanged.connect(self.ChangeQuality) #Not working because of signal overloads
        self.connect(self.main_window.quality_combo, QtCore.SIGNAL("currentIndexChanged(const QString&)"), self.ChangeQuality)
        self.main_window.fullscreen_button.clicked.connect(self.toggleFullscreen)

        #/---------------------------------------
        # libvlc Player embedding
        #---------------------------------------/
        if not self.player.get_xwindow():
            self.connectPlayer(self.main_window.video_widget.request(self.main_window.video_widget.x(),
                            self.main_window.video_widget.y(), self.main_window.video_widget.width(),
                            self.main_window.video_widget.height(), True))

        self.timer = QtCore.QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.force_update)

        self.player.lengthChanged.connect(self.lenChange)

        #DEBUG
        def debug(evt):
            if evt.type not in (self.player.mpManager.mpEvent.TimeChanged,
                                self.player.mpManager.mpEvent.PositionChanged):
                self.logger_event.getChild("LibVLC").debug(evt.type)
        #self.player.mpManager.set_debug(debug)

        #/---------------------------------------
        # Enter Main EventLoop
        #---------------------------------------/
        self.main_window.show()
        # Play first file if given on commandline
        if self.args.init_mrl is not None:
            self.player.open(self.args.init_mrl)
            self.play()
            if self.args.fullscreen:
                self.setFullscreen(True)
            if self.args.quit_after:
                self.connect(self,QtCore.SIGNAL("ended()"),self.quit)
        self.logger.debug("Entering Main Loop")
        self.exec_()
        self.logger.debug("Terminating")

        #/---------------------------------------
        # Save Settings
        #---------------------------------------/
        self.main_window.savePosition()
        if self.fs_controller: self.fs_controller.savePosition()
        self.settings.sync()

    #/-------------------------------------------
    # Event Slots
    #-------------------------------------------/
    def connectPlayer(self, winid):
        self.logger_ui.debug("Embedding Video Player: %i"%winid)
        if sys.platform == "linux2": # for Linux using the X Server
            self.player.set_xwindow(winid)
        elif sys.platform == "win32": # for Windows
            self.player.set_hwnd(winid)
        elif sys.platform == "darwin": # for MacOS
            self.player.set_agl(winid)

    def newMedia(self,media):
        media.parse()
        self.main_window.setWindowTitle(self.window_title_2.format(nativestring(media.get_meta(0))))
        self.length = media.get_duration()

    def lenChange(self, i):
        self.logger_event.debug("lenChange(%i)"%i)
        self.length = i

    def posChange(self, f_pos):
        if self.b_fullscreen and self.fs_controller:
            self.fs_controller.seeker.setPosition(f_pos, None, self.length)
        else:
            self.main_window.seeker.setPosition(f_pos, None, self.length)

    def timeChange(self, i_time):
        if self.b_fullscreen and self.fs_controller:
            self.fs_controller.time_label.setDisplayPosition((-1.0 if self.length==-1 else 1.0), i_time, self.length)
        else:
            self.main_window.time_label.setDisplayPosition((-1.0 if self.length==-1 else 1.0), i_time, self.length)

    def toggle_pause(self):
        if not self.player.is_playing():
            if self.play():
                self.open_vid()
        else:
            self.player.pause()

    def play(self):
        x = self.player.play()
        self.timer.start()
        self.main_window.sound_widget.libUpdateVolume(self.player.audio_get_volume())
        self.main_window.sound_widget.updateMuteStatus(self.player.audio_get_mute())
        return x
    def stop(self):
        self.player.stop()
        self.timer.stop()
        self.reset_ui()
        self.setFullscreen(False)

    def stateChange(self, i_state):
        #self.logger_event.debug("stateChanged(%i:%s)"%(i_state, self.player.State.name(i_state)))
        b_playing = i_state in (self.player.State.Playing, self.player.State.Buffering)
        self.main_window.play_button.updateButtonIcons(b_playing)
        if b_playing:
            self.length = self.player.get_length()
        if self.fs_controller:
            self.fs_controller.play_b.updateButtonIcons(b_playing)

    def force_update(self):
        if not self.player.is_playing():
            if self.player.get_state() in (self.player.State.Ended, self.player.State.Stopped):
                self.main_window.play_button.updateButtonIcons(False)
                if self.player.get_state()==self.player.State.Ended: #FIXME: by event?
                    self.stop()
                    self.emit(QtCore.SIGNAL("ended()"))
            self.timer.stop()

    def reset_ui(self):
        self.main_window.time_label.setDisplayPosition(-1.0, 0, self.length)
        self.main_window.seeker.setPosition(-1.0, None, self.length)

    #/-------------------------------------------
    # Open a youtube Video
    #-------------------------------------------/
    def open_vid(self):
        self.logger_ui.debug("Opening youtube video")
        url, ok = QtGui.QInputDialog.getText(self.main_window,"Open YouTube URL","Enter a YouTube Vide URL")
        if not ok:
            return
        x = self.youtube_init_video(url)
        if x:
            QtGui.QMessageBox.critical(self.main_window,"Youtube Video Error",x,"Dismiss")
        else:
            self.play()

    def youtube_init_video(self, video_url):
        # Get VideoId
        self.logger_youtube.debug("New Video: "+video_url)
        match = self.youtube_regexp.match(video_url)
        if not match:
            return self.youtube_message.format(video_url)
        self.logger_youtube.debug("Search String: %s"%match.group(1))
        params = sdict_parser(match.group(1))
        self.logger_youtube.debug("Parameters: %s"%str(params))
        if "v" not in params:
            return self.youtube_message.format(video_url)
        vid = params["v"]
        # Resolve Video
        self.logger_youtube.debug("Resolving Video: "+vid)
        video_info = resolve.resolve3(vid)
        if not video_info:
            return self.resolve_message.format(vid)
        self.video_info = video_info
        # Create Quality List
        self.logger_youtube.debug("Assembling Format List")
        self.qa_map = OrderedDict()
        for f in self.main_q_lookup:
            if f in video_info.urlmap:
                self.qa_map[profiles.descriptions[f]]=f
        # Determine Initial Quality
        self.logger_youtube.debug("Determining fitting Quality Level")
        for f in self.pref_q_lookup:
            if f in video_info.urlmap:
                fmt = f
                break;
        else:
            fmt = self.qa_map.values()[0]
        # Update UI
        self.logger_player.debug("Setting up UI for Video: "+video_info.title)
        self.uilock=True
        #self.main_window.setWindowTitle(self.window_title_2.format(video_info.title)) #now implemented in newMedia()
        # Populate Quality ComboBox
        self.main_window.quality_combo.clear()
        self.main_window.quality_combo.addItems(list(self.qa_map.keys()))
        self.main_window.quality_combo.setCurrentIndex(
            self.main_window.quality_combo.findText(profiles.descriptions[fmt], flags=QtCore.Qt.MatchExactly))
        self.uilock=False
        # Set Quality Level
        self.youtube_set_fmt(fmt)

    def youtube_set_fmt(self,fmt):
        self.logger_youtube.debug("Setting FMT: %i"%fmt)
        self.fmt = fmt
        url = self.video_info.fmt_url(fmt)
        media = player.getInstance().media_new_location(player.vlcstring(url))
        media.set_meta(0, player.vlcstring(self.video_info.title))
        media.set_meta(1, player.vlcstring(self.video_info.uploader))
        self.player.set_media(media)

    def youtube_change_fmt(self,fmt):
        pos = self.player.get_position()
        self.logger_youtube.debug("Changing FMT: %i; pos=%i"%(fmt,pos))
        self.youtube_set_fmt(fmt)
        self.play()
        self.player.set_position(pos)

    def ChangeQuality(self,str_qa):
        if not self.uilock:
            fmt = self.qa_map[str_qa]
            self.youtube_change_fmt(fmt)

    #/-------------------------------------------
    # open any video
    #-------------------------------------------/
    def open_generic(self, mrl):
        self.player.open(mrl)
        self.play()

    def open_file(self):
        self.logger_ui.debug("Opening File")
        path = QtGui.QFileDialog.getOpenFileName(self.main_window, "Open Video File", self.settings.value("MainWindow/openFileLastLocation", None))
        if not path:
            return
        self.settings.setValue("MainWindow/openFileLastLocation", os.path.dirname(path))
        self.open_generic(path)

    def open_mrl(self):
        self.logger_ui.debug("Opening Generic MRL")
        mrl, ok = QtGui.QInputDialog.getText(self.main_window,"Open MRL","Enter a MRL/Path")
        if not ok: return
        self.open_generic(mrl)

    #/-------------------------------------------
    # Fullscreen Handling
    #-------------------------------------------/
    def setFullscreenVideo(self, b_fs):
        if self.b_fullscreen != b_fs:
            if b_fs:
                #Enable Fusllscreen
                self.b_fullscreen=True
                self.main_window.video_widget.setParent(None)
                self.main_window.video_widget.showFullScreen()
            else:
                #Disable Fullscreen
                self.b_fullscreen = False
                self.main_window.video_widget.setWindowState(
                    self.main_window.video_widget.windowState() & ~QtCore.Qt.WindowFullScreen)
                self.main_window.root_layout.insertWidget(0, self.main_window.video_widget)

    def setFullscreenControls(self, b_show):
        if b_show and not self.fs_controller:
            FullscreenController.getSettings = lambda unused: self.settings
            self.fs_controller = FullscreenController(self.main_window.video_widget)
            self.fs_controller.play_b.clicked.connect(self.toggle_pause)
            self.fs_controller.stop_b.clicked.connect(self.stop)
            self.connect(self.fs_controller.sound_w, QtCore.SIGNAL("volumeChanged(int)"), self.player.audio_set_volume)
            self.connect(self.fs_controller.sound_w, QtCore.SIGNAL("muteChanged(bool)"), self.player.audio_set_mute)
            self.fs_controller.sound_w.libUpdateVolume(self.player.audio_get_volume())
            self.fs_controller.sound_w.updateMuteStatus(self.player.audio_get_mute())
            self.fs_controller.play_b.updateButtonIcons(self.player.is_playing())
            self.connect(self.fs_controller.seeker, QtCore.SIGNAL("sliderDragged(float)"), self.player.set_position)
            self.fs_controller.fullscreen.clicked.connect(lambda: self.setFullscreen(False))
            self.fs_controller.getSettings = lambda: self.settings
            del FullscreenController.getSettings
        if self.fs_controller:
            if b_show:
                self.fs_controller.sound_w.libUpdateVolume(self.player.audio_get_volume())
                self.fs_controller.sound_w.updateMuteStatus(self.player.audio_get_mute())
                self.fs_controller.play_b.updateButtonIcons(self.player.is_playing())
                self.fs_controller.seeker.setPosition(self.player.get_position(),None,self.length)
                self.fs_controller.time_label.setDisplayPosition((-1.0 if self.length==-1 else 1.0), self.player.get_time(), self.length)
            else:
                self.main_window.sound_widget.libUpdateVolume(self.player.audio_get_volume())
                self.main_window.sound_widget.updateMuteStatus(self.player.audio_get_mute())
                self.main_window.play_button.updateButtonIcons(self.player.is_playing())
                self.main_window.seeker.setPosition(self.player.get_position(),None,self.length)
                self.main_window.time_label.setDisplayPosition((-1.0 if self.length==-1 else 1.0), self.player.get_time(), self.length)
            self.fs_controller.setFullscreen(b_show)

    def setFullscreen(self, b_fs):
        if b_fs == self.b_fullscreen: return
        self.setFullscreenVideo(b_fs)
        self.setFullscreenControls(b_fs)

    def toggleFullscreen(self):
        self.setFullscreen(not self.b_fullscreen)

if __name__=="__main__":
    app = VlycApplication(sys.argv)
    logging.basicConfig(level=logging.DEBUG,format="[%(msecs)09.3f] %(levelname)-6s %(name)s:\r\n\t%(msg)s")
    app.main()
