#!/usr/bin/python3
"""
/*****************************************************************************
 * vlyc2.py : libVLC Youtube Player
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
import sys
import os
import logging
import io
import re
import collections
import tempfile
from sip import setapi
setapi("QString", 2)
setapi("QVariant",2)
from PyQt4 import QtCore, QtGui
from vlc import player, vlcevent, util

#VLYC
from vlyc import const
const.root_logger = logging.getLogger("vlyc.gui") #FIXME: find a better way to do it
from vlyc import vlc_res, input_slider, widgets, fullscreen

#LibYo
from libyo.youtube import resolve,subtitles #@UnresolvedImport
from libyo.youtube.resolve import profiles #@UnresolvedImport
from libyo.util.util import sdict_parser #@UnresolvedImport
from libyo.argparse import LibyoArgumentParser #@UnresolvedImport
from libyo.compat.uni import u as unicode, nativestring #@UnresolvedImport
from libyo.version import Version

_unused = [vlc_res]; del _unused

__VERSION__ = (0,1,2)
VERSION = Version("vlyc",*__VERSION__)

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

        self.subtitle_combo = QtGui.QComboBox(self.root_widget)
        self.subtitle_combo.setObjectName("subtitle_combo")
        self.subtitle_combo.setFocusPolicy(QtCore.Qt.NoFocus)
        self.control_layout.addWidget(self.subtitle_combo)

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

class FullscreenController(fullscreen.Controller):
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
        self.play_b.setShortcut(" ")
        layout.addWidget(self.play_b)

        self.stop_b = QtGui.QToolButton()
        self.stop_b.setObjectName("fscStopButton")
        self.stop_b.setIcon(QtGui.QIcon(":/toolbar/stop_b"))
        layout.addWidget(self.stop_b)

        layout.addStretch(100)

        self.fullscreen = QtGui.QToolButton()
        self.fullscreen.setObjectName("fscFullscreenButton")
        self.fullscreen.setIcon(QtGui.QIcon(":/toolbar/defullscreen"))
        self.fullscreen.setShortcut("Esc")
        layout.addWidget(self.fullscreen)

        layout.addSpacing(20)

        self.sound_w = widgets.SoundWidget(None, True)
        self.sound_w.setObjectName("fscSoundWidget")
        layout.addWidget(self.sound_w)

        return layout

class YoutubeHandler(QtCore.QObject):
    """
    The YouTube Resolving Handler (to be run inside a thread)
    """
    #/+++++++++++++++++++++++++++++++++++++++++++
    # Constants
    #+++++++++++++++++++++++++++++++++++++++++++/
    watch_regexp = re.compile(r"^.+youtube\..{2,3}\/watch\?(.+)$")
    invalid_message= "URL does not seem to be a valid YouTube Video URL:\r\n%s"
    resolve_message= "Could not resolve Video: %s\r\n(Are you sure your Internet connection is Up?)"
    logger = logging.getLogger("vlyc.YoutubeThread")
    main_q_lookup = list(profiles.profiles["mixed-avc"][0].values())
    pref_q_lookup = [18,5]
    #/+++++++++++++++++++++++++++++++++++++++++++
    # Initialization
    #+++++++++++++++++++++++++++++++++++++++++++/
    def __init__(self):
        super(YoutubeHandler,self).__init__()
        self.video_info = None
        self.qa_map = None
        self.subtitle_file = None
        self.subtitle_tracks = None
    #/+++++++++++++++++++++++++++++++++++++++++++
    # Signals
    #+++++++++++++++++++++++++++++++++++++++++++/
    newVideoInf = QtCore.pyqtSignal("PyQt_PyObject")
    videoUrlSet = QtCore.pyqtSignal("QString")
    subsfileSet = QtCore.pyqtSignal("QString")
    resolveBegn = QtCore.pyqtSignal()
    resolveDone = QtCore.pyqtSignal()
    resolveFail = QtCore.pyqtSignal("QString")
    qualityList = QtCore.pyqtSignal("QStringList",int)
    newSubsList = QtCore.pyqtSignal("QStringList")
    #/+++++++++++++++++++++++++++++++++++++++++++
    # Slots / Functions
    #+++++++++++++++++++++++++++++++++++++++++++/
    @QtCore.pyqtSlot("QString")
    def initYoutube(self, url):
        """
        Load a Youtube Video
        @called [SLOT]
        @arg    str     url     the Video's Watch URL
        @emits [resolveBegn],[resolveDone],[resolveFail]
        @calls initVideo,initSubtitles
        """
        self.logger.info("Initializing Video: %s"%url)
        self.resolveBegn.emit()
        #Parse the Watch URL
        match = self.watch_regexp.match(url)
        if not match:
            self.resolveFail.emit(self.invalid_message%url)
        params = sdict_parser(match.group(1))
        if "v" not in params:
            self.resolveFail.emit(self.invalid_message%url)
        video_id = params["v"]
        #Initialize Video
        self.initVideo(video_id)
        #Initialize Subtitles
        self.initSubtitles(video_id)
        #Done
        self.resolveDone.emit()

    #/-------------------------------------------
    # Video URL Handling
    #-------------------------------------------/
    def initVideo(self,video_id):
        """
        [Internal] Resolve a Video
        @called initYoutube
        @arg    str     video_id    Video ID
        @emits  [resolveFail],[qualityList],[videoUrlSet],[newVideoInf]
        """
        #Get the Video URL
        self.logger.debug("Resolving Video: %s"%video_id)
        video_info = resolve.resolve3(video_id)
        if not video_info:
            self.resolveFail(self.resolve_message%video_id)
        self.video_info = video_info
        self.newVideoInf.emit(video_info)
        #Create Quality List
        self.logger.debug("Assembling Format List")
        self.qa_map = collections.OrderedDict()
        for f in self.main_q_lookup:
            if f in video_info.urlmap:
                self.qa_map[profiles.descriptions[f]]=f
        #Determine Initial Quality
        self.logger.debug("Determining fitting Quality Level")
        for f in self.pref_q_lookup:
            if f in video_info.urlmap:
                fmt = f
                break;
        else:
            self.logger.warn("No Preferred Quality Available. Choosing First Entry: %s",list(self.qa_map.keys())[0])
            fmt = list(self.qa_map.values())[0]
        #Emit Signal
        f = list(self.qa_map.values()).index(fmt)
        self.qualityList.emit(list(self.qa_map.keys()),f)
        self.videoUrlSet.emit(self.video_info.fmt_url(fmt))

    @QtCore.pyqtSlot("QString")
    def setQuality(self,descr):
        """
        Set the Quality Level
        @called [SLOT],initVideo
        @arg    str|int descr       the Quality Description or index
        @emits  [videoUrlSet]
        """
        fmt = self.qa_map[descr]
        self.videoUrlSet.emit(self.video_info.fmt_url(fmt))

    #/-------------------------------------------
    # Subtitle Handling
    #-------------------------------------------/
    def initSubtitles(self,video_id):
        """
        [internal] Initialize Subtitles
        @called initVideo
        @args   str     video_id
        @emits  [newSubsList]
        """
        self.logger.debug("Initializing Subtitles for Video '%s'"%self.video_info.title)
        self.subtitle_tracks = subtitles.getTracks(video_id)
        self.newSubsList.emit([t.lang_original for t in self.subtitle_tracks])

    @QtCore.pyqtSlot(int)
    def setSubtitleTrack(self,i):
        """
        Select a Subtitle Track
        @called [SLOT]
        @arg    int     i       Track Number
        @emits  [subsfileSet]
        @calls  cleanupSubtitles
        """
        self.cleanupSubtitles()
        track           = self.subtitle_tracks[i]
        self.logger.debug("Fetching Subtitle Track [%i] %s",i,track.lang_original)
        file            = tempfile.NamedTemporaryFile("wb",prefix="vlycsub",suffix=".srt",delete=False)
        file.writable   = \
        file.seekable   = \
        file.readable   = lambda: True
        handle          = io.TextIOWrapper(file,encoding="utf8")
        handle.write(track.getSRT())
        handle.close()
        file.close()
        self.subtitle_file = file.name
        #Emit signal
        self.subsfileSet.emit(self.subtitle_file)

    def cleanupSubtitles(self):
        """
        [Internal] Cleanup Old Subtitles File
        @called initSubs, [terminated]
        """
        if self.subtitle_file:
            os.remove(self.subtitle_file)
        self.subtitle_file = None

class VlycApplication(QtGui.QApplication):
    """
    A VLYC Player Application
    """
    window_title_1 = """VideoLan Youtube Client"""
    window_title_2 = """{0} -- VLYC"""

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
                                          type=util.vlcstring, action="append", default=None,
                                          help="Pass all remaining args to libvlc directly. For help, try '%(prog)s --- --help'. Not all listed Arguments will work as expected! Use on your own account")

    def argument_parser_execute(self):
        self.args = self.argument_parser.parse_args(self.arguments()[1:])

    def main(self):
        #/---------------------------------------
        # Parse CommandLine Parameters
        #---------------------------------------/
        self.argument_parser_execute()

        #/---------------------------------------
        # Do Version Checks
        #---------------------------------------/
        if not Version.PythonVersion.minVersion(3,2):
            QtGui.QMessageBox.warn(None,"Python Version Alert",
                    """The Python Version you are using is not supported by this Application: %s
                    The Consistency of the Software can not be guaranteed.
                    Please consider upgrading to Python v3.2 or higher (http://python.org)"""\
                                   %Version.PythonVersion.format())
        self.logger.info("Python Version: %s"%Version.PythonVersion.format())
        if not Version.LibyoVersion.minVersion(0,9,10,"b"):
            QtGui.QMessageBox.critical(None,"LibYo Version Alert",
                    """The libyo library version you are using is not supported by this Application: %s
                    The Software cannot run properly.
                    Please upgrade to libyo v0.9.10b or higher (http://github.com/Orochimarufan/libyo)"""\
                                    %Version.LibyoVersion.format())
            return 1
        self.logger.info("libyo Version: %s"%Version.LibyoVersion.format())
        if player.libvlc_hexversion()<0x020000:
            QtGui.QMessageBox.warn(None,"libvlc Version Alert",
                    """The libvlc library version you are using is not supported by this Application: %s
                    The software may not be able to run properly.
                    Please consider upgrading to libvlc 2.0.0 or higher (http://videolan.org)"""\
                                    %Version("libvlc",player.libvlc_version()).format())
        self.logger.info("libvlc Version: %s"%player.libvlc_versionstring())

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
        self.yt_sub_tracks = []
        self.subfile = None
        self.rdg = None
        self._yt_title = None
        self._yt_uploa = None

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
        self.connect(self.main_window.subtitle_combo, QtCore.SIGNAL("currentIndexChanged(int)"), self.ChangeSubTrack)
        self.main_window.fullscreen_button.clicked.connect(self.toggleFullscreen)

        #/---------------------------------------
        # Set up Youtube Thread
        #---------------------------------------/
        self.youtube_thread = QtCore.QThread()
        self.init_yt()
        self.youtube_thread.start()

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
            if evt.type not in (vlcevent.mpEvent.TimeChanged,
                                vlcevent.mpEvent.PositionChanged):
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
        # Collect threads
        #---------------------------------------/
        self.youtube_thread.terminate()

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
        self.logger_ui.debug("Setting up UI for Video: "+nativestring(media.get_meta(0)))
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
        if self.subfile:
            self.player.video_set_subtitle_file(util.vlcstring(self.subfile.name))
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
        else:
            if self.rdg and self.rdg.isVisible():
                self.rdg.hide()

    def reset_ui(self):
        self.main_window.time_label.setDisplayPosition(-1.0, 0, self.length)
        self.main_window.seeker.setPosition(-1.0, None, self.length)

    #/-------------------------------------------
    # youtube
    #-------------------------------------------/
    _yt_sig_init = QtCore.pyqtSignal("QString")
    _yt_sig_qual = QtCore.pyqtSignal("QString")
    _yt_sig_subs = QtCore.pyqtSignal(int)
    def init_yt(self):
        self.youtube = YoutubeHandler()
        self.youtube_thread.started.connect(lambda: self.youtube.logger.info("YoutubeThread started"))
        self.youtube_thread.terminated.connect(self.youtube.cleanupSubtitles)
        self._yt_sig_init.connect(self.youtube.initYoutube)
        self._yt_sig_qual.connect(self.youtube.setQuality)
        self._yt_sig_subs.connect(self.youtube.setSubtitleTrack)
        self.youtube.newVideoInf.connect(self.set_info)
        self.youtube.videoUrlSet.connect(self.set_url)
        self.youtube.subsfileSet.connect(self.set_sub)
        self.youtube.resolveBegn.connect(self.rdg_show)
        self.youtube.resolveDone.connect(self.rdg_hide)
        self.youtube.resolveFail.connect(self.rdg_fail)
        self.youtube.qualityList.connect(self.set_qlist)
        self.youtube.newSubsList.connect(self.set_slist)
        self.youtube.moveToThread(self.youtube_thread)
    #Thread Delegations
    def open_vid(self):
        url, ok = QtGui.QInputDialog.getText(self.main_window,"Open YouTube URL","Enter a YouTube Vide URL")
        if ok:
            self._yt_sig_init.emit(url)
    def ChangeQuality(self,str_qa):
        if not self.uilock:
            self._yt_sig_qual.emit(str_qa)
    def ChangeSubTrack(self,i_pos):
        if self.uilock: return
        if i_pos == 0:
            self.player.video_set_spu(0)
        else:
            i_pos -= 1
            self._yt_sig_subs.emit(i_pos)
    def clnupYt(self):
        self.main_window.subtitle_combo.clear()
        self.main_window.quality_combo.clear()
    #Thread callbacks
    def set_info(self,info):
        self._yt_title = util.vlcstring(info.title)
        self._yt_uploa = util.vlcstring(info.uploader)
    def set_url(self,newurl):
        preservepos = self.player.get_state()!=self.player.State.Stopped
        if preservepos:
            pos = self.player.get_position()
        media = player.getInstance().media_new_location(util.vlcstring(newurl))
        media.set_meta(0,self._yt_title)
        media.set_meta(1,self._yt_uploa)
        self.player.set_media(media)
        self.play()
        if preservepos:
            self.player.set_position(pos)
    def set_sub(self,path):
        self.player.video_set_subtitle_file(util.vlcstring(path))
    def rdg_show(self):
        if not self.rdg:
            self.rdg = QtGui.QMessageBox(self.main_window)
            self.rdg.setText("Loading Youtube Video. Please Wait")
            self.rdg.setStandardButtons(QtGui.QMessageBox.NoButton)
        self.rdg.show()
    def rdg_hide(self):
        self.rdg.hide()
    def rdg_fail(self,msg):
        self.rdg.hide()
        QtGui.QMessageBox.critical(self.main_window,"YouTube Error",msg)
    def set_qlist(self,qlist,index):
        self.uilock = True
        self.main_window.quality_combo.clear()
        self.main_window.quality_combo.addItems(qlist)
        self.main_window.quality_combo.setCurrentIndex(index)
        self.uilock = False
    def set_slist(self,slist):
        self.uilock = True
        self.main_window.subtitle_combo.clear()
        self.main_window.subtitle_combo.addItems(["No Subtitles"]+slist)
        self.uilock = False

    #/-------------------------------------------
    # open any video
    #-------------------------------------------/
    def open_generic(self, mrl):
        self.clnupYt()
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
    logging.basicConfig(level=logging.DEBUG,format="[%(relativeCreated)09d] %(levelname)-6s %(name)s:\r\n\t%(msg)s")
    app.main()
