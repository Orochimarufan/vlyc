"""
/*****************************************************************************
 * vlyc :: main.py : libVLC Youtube Player Application
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

import sys
import os
import logging

import sip
sip.setapi("QString",2)

from PyQt4 import QtCore
from PyQt4 import QtGui

from libyo.argparse import LibyoArgumentParser
from libyo.version import Version

from vlc import player
from vlc import util
from vlc import vlcevent

from . import const
const.root_logger = logging.getLogger("vlyc.gui")
from . import VERSION_STRING, CODENAME, VERSION
from . import settings

from .ui import MainWindow
from .ui import FullscreenController
from .ui import AboutDialog

from .youtube import YoutubeHandler

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
        self.setApplicationVersion(VERSION_STRING)

        self.argument_parser = LibyoArgumentParser(prog = self.arguments()[0], usage = "%(prog)s [MRL] [--- ARG [...]]")
        self.argument_parser.add_argument(metavar="MRL", nargs="?", dest="init_mrl", type=util.vlcstring,
                                          help="Play this file/MRL at startup")
        self.argument_parser.add_argument("--fullscreen",action="store_true",
                                          help="Start in Fullscreen Mode (only if MRL is given)")
        self.argument_parser.add_argument("--quit",action="store_true", dest="quit_after",
                                          help="Quit after playing MRL")
        self.argument_parser.add_argument("---", metavar="", nargs="A...?", dest="vlcargs",
                                          type=util.vlcstring, action="append", default=None,
                                          help="Pass all remaining args to libvlc directly. For help, try '%(prog)s --- --help'. Not all listed Arguments will work as expected! Use on your own account")

    def argument_parser_execute(self):
        #self.logger.debug("Args: %s"%self.arguments())
        self.args = self.argument_parser.parse_args(self.arguments()[1:])

    def main(self):
        #/---------------------------------------
        # Parse CommandLine Parameters
        #---------------------------------------/
        self.argument_parser_execute()

        #/---------------------------------------
        # Do Version Checks
        #---------------------------------------/
        if not Version.PythonVersion.minVersion(3,2): #For whatever reason he doesnt like Version.xVersion @UndefinedVariable
            QtGui.QMessageBox.warning(None,"Python Version Alert",
                    """The Python Version you are using is not supported by this Application: %s
                    The Consistency of the Software can not be guaranteed.
                    Please consider upgrading to Python v3.2 or higher (http://python.org)"""\
                                   %Version.PythonVersion.format()) #@UndefinedVariable
        self.logger.info("Python Version: %s"%Version.PythonVersion.format()) #@UndefinedVariable
        if not Version.LibyoVersion.minVersion(0,9,10,"b"): #@UndefinedVariable
            QtGui.QMessageBox.critical(None,"LibYo Version Alert",
                    """The libyo library version you are using is not supported by this Application: %s
                    The Software cannot run properly.
                    Please upgrade to libyo v0.9.10b or higher (http://github.com/Orochimarufan/libyo)"""\
                                    %Version.LibyoVersion.format()) #@UndefinedVariable
            return 1
        self.logger.info("libyo Version: %s"%Version.LibyoVersion.format()) #@UndefinedVariable
        if player.libvlc_hexversion()<0x020000:
            QtGui.QMessageBox.warning(None,"libvlc Version Alert",
                    """The libvlc library version you are using is not supported by this Application: %s
                    The software may not be able to run properly.
                    Please consider upgrading to libvlc 2.0.0 or higher (http://videolan.org)"""\
                                    %Version("libvlc",player.libvlc_version()).format())
        self.logger.info("libvlc Version: %s"%player.libvlc_versionstring())
        
        self.logger.info("VideoLan Youtube Client %s '%s'"%(".".join(map(str,VERSION)),CODENAME))

        #/---------------------------------------
        # Load Settings
        #---------------------------------------/
        self.settings = settings.Settings.Init()
        const.QT_SLIDER_COLORS = self.settings.value("SeekSlider/Colors", const.QT_SLIDER_COLORS)
        const.FSC_HEIGHT = self.settings.value("FullScreen/Height", const.FSC_HEIGHT)
        const.FSC_WIDTH = self.settings.value("FullScreen/Width", const.FSC_WIDTH)
        const.VOLUME_STEP = self.settings.value("SoundWidget/Step", const.VOLUME_STEP)
        YoutubeHandler.pref_q_lookup = map(int,self.settings["Youtube":"PreferredQualities":[22,18,5]])

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
        self.player.MediaPlayer.video_set_mouse_input(False)
        self.player.MediaPlayer.video_set_key_input(False)

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
        self._yt_is_video = False
        self.about_dlg = None

        #/---------------------------------------
        # MenuBar Actions
        #---------------------------------------/
        self.main_window.file_quit_action.triggered.connect(self.quit)
        self.main_window.file_open_youtube_action.triggered.connect(self.open_vid)
        self.main_window.file_open_file_action.triggered.connect(self.open_file)
        self.main_window.file_open_stream_action.triggered.connect(self.open_mrl)
        self.main_window.help_about_action.triggered.connect(self.show_about)

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
        # Shortcuts
        #---------------------------------------/
        self.shortcut_esc = QtGui.QShortcut("Esc",self.main_window.video_widget)
        self.shortcut_esc.activated.connect(lambda: self.setFullscreen(False))
        self.shortcut_f11 = QtGui.QShortcut("F11",self.main_window)
        self.shortcut_f11.activated.connect(self.toggleFullscreen)
        self.shortcut_f11.setContext(2) #App-wide
        self.main_window.video_widget.MouseDoubleClick.connect(self.toggleFullscreen)

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

        #TODO: Get rid of the timer business IAAP
        self.timer = QtCore.QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.force_update)

        self.player.lengthChanged.connect(self.lenChange)

        #DEBUG
        def debug(evt):
            if evt.type not in (vlcevent.MediaPlayerEvent.TimeChanged, #PyDev doesn't like my Enums @UndefinedVariable
                                vlcevent.MediaPlayerEvent.PositionChanged): #@UndefinedVariable
                self.logger_event.getChild("LibVLC").debug(evt.type)
        #self.player.mpManager.set_debug(debug)

        #/---------------------------------------
        # Enter Main EventLoop
        #---------------------------------------/
        self.main_window.show()
        # Play first file if given on commandline
        if self.args.init_mrl is not None:
            self.logger.info("Opening '%s'"%self.args.init_mrl)
            if YoutubeHandler.watch_regexp.match(str(self.args.init_mrl,"UTF-8")):
                #we got a youtube url
                self._yt_sig_init.emit(str(self.args.init_mrl,"utf8"))
            else:
                #try to open it
                self.player.open(self.args.init_mrl)
                self.play()
            if self.args.fullscreen:
                self.setFullscreen(True)
            if self.args.quit_after:
                self.connect(self,QtCore.SIGNAL("ended()"),self.quit)
        self.logger.debug("Entering Main Loop")
        self.exec_()
        self.logger.info("Terminating")

        #/---------------------------------------
        # Collect threads
        #---------------------------------------/
        self.logger.debug("Waiting for Threads to finish...")
        self.youtube_thread.quit()
        self.youtube_thread.wait()

        #/---------------------------------------
        # Save Settings
        #---------------------------------------/
        self.main_window.savePosition()
        if self.fs_controller: self.fs_controller.savePosition()
        self.settings.sync()
		
        return 0

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
        self.logger_ui.debug("Setting up UI for Video: "+util.pystring(media.get_meta(0)))
        self.main_window.setWindowTitle(self.window_title_2.format(util.pystring(media.get_meta(0))))
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
        #self.main_window.sound_widget.libUpdateVolume(self.player.audio_get_volume())
        #self.main_window.sound_widget.updateMuteStatus(self.player.audio_get_mute())
        if self._yt_is_video:
            self._yt_sig_anns.emit()
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
            self.main_window.sound_widget.libUpdateVolume(self.player.audio_get_volume())
            self.main_window.sound_widget.updateMuteStatus(self.player.audio_get_mute())
            if self.fs_controller and self.b_fullscreen:
                self.fs_controller.sound_widget.libUpdateVolume(self.player.audio_get_volume())
                self.fs_controller.sound_widget.updateMuteStatus(self.player.audio_get_mute())
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
    
    def show_about(self):
        if not self.about_dlg:
            self.about_dlg = AboutDialog(self.main_window)
        self.about_dlg.show()

    #/-------------------------------------------
    # youtube
    #-------------------------------------------/
    _yt_sig_init = QtCore.pyqtSignal("QString")
    _yt_sig_qual = QtCore.pyqtSignal("QString")
    _yt_sig_subs = QtCore.pyqtSignal(int)
    _yt_sig_anns = QtCore.pyqtSignal()
    def init_yt(self):
        self.youtube = YoutubeHandler()
        self.youtube_thread.started.connect(lambda: self.youtube.logger.debug("YoutubeThread started"))
        self.youtube_thread.terminated.connect(self.youtube.cleanupSubtitles)
        self._yt_sig_init.connect(self.youtube.initYoutube)
        self._yt_sig_qual.connect(self.youtube.setQuality)
        self._yt_sig_subs.connect(self.youtube.setSubtitleTrack)
        self._yt_sig_anns.connect(self.youtube.reannounceSubtitles)
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
            self.player.stop()
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
        self._yt_is_video = False
        self.main_window.subtitle_combo.clear()
        self.main_window.quality_combo.clear()
    #Thread callbacks
    def set_info(self,info):
        self._yt_title = util.vlcstring(info.title)
        self._yt_uploa = util.vlcstring(info.uploader)
        if self.rdg.isVisible():
            self.rdg.setText("Opening YouTube Video:\n\"%s\""%info.title)
    def set_url(self,newurl):
        preservepos = self.player.get_state()!=self.player.State.Stopped
        self._yt_is_video = True
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
        self.rdg.setText("Opening YouTube Video...\n")
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
            if b_show:
                self.main_window.video_widget.MouseMoved.connect(self.fs_controller.mouseChanged)
            else:
                self.main_window.video_widget.MouseMoved.disconnect(self.fs_controller.mouseChanged)

    def setFullscreen(self, b_fs):
        if b_fs == self.b_fullscreen: return
        self.setFullscreenVideo(b_fs)
        self.setFullscreenControls(b_fs)

    def toggleFullscreen(self):
        self.setFullscreen(not self.b_fullscreen)

def main(argv):
    app = VlycApplication(argv)
    return app.main()

