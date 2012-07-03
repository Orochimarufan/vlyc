'''
Created on 10.06.2012

@author: hinata
'''

from __future__ import absolute_import,division,print_function,unicode_literals

from libyo.version import Version
from libyo.compat.uni import b #@UnresolvedImport
from libyo.youtube import resolve#,subtitles
from libyo.youtube.resolve import profiles,AbstractBackend
from libyo.util.util import sdict_parser
import sip
sip.setapi("QString",2)
from PyQt4 import QtCore,QtGui
from vlyc.vlyc_gui import Ui_MainWindow
import sys,re
from vlc import libvlc
from collections import OrderedDict
import logging

if Version.PythonVersion.minVersion(3): #@UndefinedVariable
    vlcstring = b
else:
    vlcstring = unicode #@UndefinedVariable

class DummyResolver(AbstractBackend.AbstractBackend):
    def __init__(self,url,title):
        self.url = url
        self.title = title
    def _resolve(self):
        return {"fmt_url_map":{18:self.url}, "title": self.title, "description":"DummyResolver Video", "uploader":"DummyResolver"}

class Application(QtGui.QApplication):
    #Constants
    pos_fractional = 1000.0
    instance_args  = []#[b"-v"]
    #youtube_regexp = re.compile(r"(?:https?\:\/\/)?(?:www\.)?youtube\.(?:com|de)\/watch\?(.*)",re.IGNORECASE)
    youtube_regexp = re.compile(r"^.+youtube\..{2,3}\/watch\?(.+)$")
    youtube_message= """URL does not seem to be a valid YouTube Video URL:\r\n{0}"""
    resolve_message= """Could not resolve Video: {0}\r\n(Are you sure your Internet connection is Up?)"""
    window_title_1 = """VideoLan Youtube Client"""
    window_title_2 = """{0} -- VLYC"""
    main_q_lookup = list(profiles.profiles["mixed-avc"][0].values())
    pref_q_lookup = [18,5]
    resolver = None #use libyo default resolver
#    resolver = resolve.create_resolver(DummyResolver(
#                "/media/Volume/youtube/playlists/TNC_OLD/Nightcore_-_The_Power_Of_Pleasure.webm",
#                "Nightcore - What makes you beautiful"))
    logger      = logging.getLogger("vlyc")
    logger_player= logger.getChild("player")
    logger_youtube= logger.getChild("youtube")
    logger_libvlc= logger.getChild("libvlc")
    logger_ui   = logger.getChild("ui")
    # Main
    def main(self):
        # Check Versions
        self.logger.info("Running Python "+Version.PythonVersion.format()) #@UndefinedVariable
        if not Version.PythonVersion.minVersion(3,2): #@UndefinedVariable
            QtGui.QMessageBox.critical(None,"Unsupported Python Version","Your Python Version is not supported: {0}\r\nThis Application may or may not work.\r\nYou are advised to upgrade to Python 3.2+".format(Version.PythonVersion.format()),"Dismiss") #@UndefinedVariable
        self.logger.info("Running libyo "+Version.LibyoVersion.format()) #@UndefinedVariable
        if not Version.LibyoVersion.minVersion(0,9,10,"b"): #@UndefinedVariable
            QtGui.QMessageBox.critical(None,"Unsupported libyo Version","The libyo version you are using is not supported by this software: {0}\r\nPlease upgrade to at least libyo 0.9.11".format(Version.LibyoVersion.format()),"Quit") #@UndefinedVariable
            return 1
        self.logger.info("Running libvlc %s"%libvlc.libvlc_get_version())

        # Setup UI
        self.logger.debug("Loading Interface")
        self.main_window = QtGui.QMainWindow()
        self.main_window.ui = Ui_MainWindow()
        self.main_window.ui.setupUi(self.main_window)
        self.main_window.setWindowTitle(self.window_title_1)
        self.main_window.ui.frame_video.setAttribute(QtCore.Qt.WA_NativeWindow)
        self.video_frame = self.main_window.ui.frame_video
        self.video_frame.installEventFilter(self)

        # Setup Signals and Player Instance
        self.logger.debug("Setting up libvlc")
        self.setupPlayer()
        self.connectPlayer()
        self.setupSignals()
        self.setupTimer()

        # Enter Main Loop
        self.logger.debug("Entering Main Loop")
        self.main_window.show()
        self.exec_()

        # Cleanup
        self.logger.debug("Cleaning Up")
        self.cleanUp()
        self.logger.debug("Terminating")

    # Event Handler
    def eventFilter(self,receipent,event):
        if receipent == self.main_window.ui.frame_video:
            if event.type() == QtCore.QEvent.WinIdChange:
                self.logger_ui.warn("Video Frame WindowID changed: %i"%self.video_frame.winId())
                self.reattachPlayer()
                return True
        return False

    # Init code
    def setupSignals(self):
        self.logger_ui.debug("Setting up Qt Signal connections")
        connect = self.main_window.connect
        ui = self.main_window.ui
        SIGNAL = QtCore.SIGNAL
        SLOT = QtCore.SLOT
        #Menu Bar
        connect(ui.action_quit,SIGNAL("triggered()"),self,SLOT("quit()"))
        connect(ui.action_open_youtube,SIGNAL("triggered()"),self.OpenYoutubeUrl)
        connect(ui.action_open,SIGNAL("triggered()"),self.OpenMrl)
        connect(ui.action_open_file,SIGNAL("triggered()"),self.OpenFile)
        #Player Controls
        connect(ui.button_playpause,SIGNAL("clicked()"),self.PlayPause)
        connect(ui.button_stop,SIGNAL("clicked()"),self.player_stop)
        connect(ui.button_fullscreen,SIGNAL("clicked()"),self.player_toggleFullscreen)
        #connect(ui.slider_seek,SIGNAL("valueChanged(int)"),self.player_seekTo)
        connect(ui.slider_seek,SIGNAL("sliderMoved(int)"),self.player_seekTo)
        connect(ui.slider_vol,SIGNAL("valueChanged(int)"),self.player_setVolume)
        connect(ui.slider_vol,SIGNAL("sliderMoved(int)"),self.player_setVolume)
        #Youtube Controls
        connect(ui.combo_quality,SIGNAL("currentIndexChanged(const QString&)"),self.ChangeQuality)

    def setupPlayer(self):
        self.logger_ui.debug("Setting video frame palette")
        palette = self.main_window.ui.frame_video.palette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(0,0,0))
        self.main_window.ui.frame_video.setPalette(palette)
        self.logger_ui.debug("Setting Slider Values")
        self.main_window.ui.slider_seek.setMaximum(self.pos_fractional)
        self.main_window.ui.slider_vol.setMaximum(200)
        self.logger_player.debug("Creating libVLC instance")
        self.vlc = libvlc.Instance(self.instance_args)
        self.media_player = self.vlc.media_player_new()
        self.logger_player.debug("Finishing Player Setup")
        self.srtfile = None
        self.uilock = False
        self.player_paused = self.player_starting = False
        self.fullscreen = False
        self.video_info = self.fmt = self.qa_map = None

    def setupTimer(self):
        self.logger_ui.debug("Initializing Update Timer")
        self.ui_timer = QtCore.QTimer()
        self.ui_timer.setInterval(500)
        self.connect(self.ui_timer,QtCore.SIGNAL("timeout()"),self.ui_update)

    def reattachPlayer(self):
        if self.media_player.is_playing():
            self.logger_ui.warn("Reattaching Video Player")
            self.logger_ui.debug("Temporarily Stopping Playback")
            self.ui_timer.stop()
            pos = self.player_getPosition()
            self.media_player.stop()
            self.logger_ui.debug("Saving Position: %i"%pos)
            self.connectPlayer()
            self.logger_ui.debug("Re-starting Playback")
            self.player_raw_play()
            self.logger_ui.debug("Restoring Position")
            self.player_seekTo(pos)
            self.processEvents()
            self.ui_timer.start()
        else:
            self.connectPlayer()

    def connectPlayer(self):
        self.logger_ui.debug("Embedding Video Player")
        winid = self.main_window.ui.frame_video.winId()
        if sys.platform == "linux2": # for Linux using the X Server
            self.media_player.set_xwindow(winid)
        elif sys.platform == "win32": # for Windows
            self.media_player.set_hwnd(winid)
        elif sys.platform == "darwin": # for MacOS
            self.media_player.set_agl(winid)

    def cleanUp(self):
        self.logger_youtube.debug("Freeing Cache")
        del self.video_info
        del self.fmt
        del self.qa_map
        self.logger_player.debug("Stopping Player")
        self.ui_timer.stop()
        self.media_player.stop()
        self.logger_player.debug("Cleaning up LibVLC")
        self.media_player.set_media(None)
        self.media.release()
        del self.media
        self.media_player.release()
        del self.media_player
        self.vlc.release()
        del self.vlc
        self.logger_ui.debug("Dismantling UI")
        self.video_frame.removeEventFilter(self)
        del self.video_frame
        self.main_window.close()
        self.main_window.destroy()
        del self.main_window

    # Main code
    def ui_update(self):
        self.main_window.ui.slider_seek.setValue(self.player_getPosition())
        self.main_window.ui.label_time.setText("{0:02}:{1:02}:{2:02}".format(*self.make_time(self.media_player.get_time())))
        if not self.media_player.is_playing() and not self.player_starting:
            self.ui_timer.stop()
            self.logger_ui.debug("Video Paused!")
            if not self.player_paused:
                self.logger_ui.debug("No, Stopped!")
                self.player_stop()
        elif self.media_player.is_playing() and self.player_starting:
            self.player_starting = False

    def make_time(self,ms):
        sec = ms//1000; ms = ms%1000
        min = sec//60; sec %=60
        hrs = min//60; min %=60
        return hrs,min,sec,ms

    # Youtube Stuffs
    def youtube_init_video(self,video_url):
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
        video_info = resolve.resolve3(vid,self.resolver)
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
        self.main_window.setWindowTitle(self.window_title_2.format(video_info.title))
        # Populate Quality ComboBox
        self.main_window.ui.combo_quality.clear()
        self.main_window.ui.combo_quality.addItems(list(self.qa_map.keys()))
        self.main_window.ui.combo_quality.setCurrentIndex(
            self.main_window.ui.combo_quality.findText(profiles.descriptions[fmt], flags=QtCore.Qt.MatchExactly))
        self.uilock=False
        # Set Quality Level
        self.youtube_set_fmt(fmt)

    def youtube_set_fmt(self,fmt):
        self.logger_youtube.debug("Setting FMT: %i"%fmt)
        self.fmt = fmt
        url = self.video_info.fmt_url(fmt)
        self.player_open(url)

    def youtube_change_fmt(self,fmt):
        pos = self.player_getPosition()
        self.logger_youtube.debug("Changing FMT: %i; pos=%i"%(fmt,pos))
        self.youtube_set_fmt(fmt)
        self.player_play()
        self.player_seekTo(pos)

    # Player Control
    def player_raw_play(self):
        r = self.media_player.play()
        if not r:
            self.player_starting=True
        return r
    def player_play(self):
        self.logger_player.debug("Starting Playback")
        self.player_paused = False
        self.main_window.ui.button_playpause.setText("Pause")
        ra=self.player_raw_play()
        self.ui_timer.start()
        return ra #have to call timer.start() AFTER player.play()!
    def player_pause(self):
        self.logger_player.debug("Pausing Playback")
        self.player_paused = True
        self.media_player.pause()
        self.main_window.ui.button_playpause.setText("Play")
    def player_stop(self):
        self.logger_player.debug("Stopping Playback")
        self.media_player.stop()
        self.player_reset()
        self.player_setFullscreen(False)
    def player_reset(self):
        self.logger_ui.debug("Resetting Player UI")
        self.main_window.ui.slider_seek.setValue(0)
        self.main_window.ui.slider_vol.setValue(self.media_player.audio_get_volume())
        self.main_window.ui.label_time.setText("00:00:00")
        self.main_window.ui.button_playpause.setText("Play")
    def player_open(self,mrl):
        self.logger_player.debug("Opening %s"%mrl)
        if ":" in mrl and mrl.index(":")>1:
            #self.media = self.vlc.media_new_location(mrl.encode("utf-8"))
            self.media = self.vlc.media_new_location(vlcstring(mrl))
        else:
            #self.media = self.vlc.media_new_path(mrl.encode("utf-8"))
            self.media = self.vlc.media_new_path(vlcstring(mrl))
        self.media_player.set_media(self.media)
        self.player_reset()
    def player_setFullscreen(self,enabled):
        if self.media_player.get_fullscreen()==enabled:
            return
        if enabled:
            self.logger_ui.debug("UnLinking VideoFrame (Fullscreen)")
            self.main_window.ui.frame_video.setParent(None)
            self.main_window.ui.frame_video.setWindowTitle("VLYC Video Output")
        self.media_player.set_fullscreen(enabled)
        if not enabled:
            self.logger_ui.debug("ReLinking VideoFrame (Un-Fullscreen)")
            self.main_window.ui.frame_video.setParent(self.main_window)
            self.main_window.ui.layout_main.addWidget(self.main_window.ui.frame_video,0)
        self.main_window.ui.frame_video.show()
        self.fullscreen = enabled
    def player_toggleFullscreen(self):
        #self.media_player.toggle_fullscreen()
        self.player_setFullscreen(not self.fullscreen)
    def player_setVolume(self,int_vol):
        #self.logger_player.debug("Setting Volume: %i"%int_vol)
        self.media_player.audio_set_volume(int_vol)
    def player_seekTo(self,int_position):
        #self.logger_player.debug("Seeking Video: %i"%int_position)
        self.media_player.set_position(int_position/self.pos_fractional)
    def player_getPosition(self):
        #self.logger_player.debug("getPosition: %f"%self.media_player.get_position())
        return int(self.media_player.get_position()*self.pos_fractional)
    # Slots
    def OpenYoutubeUrl(self):
        self.logger_ui.debug("Opening youtube video")
        url, ok = QtGui.QInputDialog.getText(self.main_window,"Open YouTube URL","Enter a YouTube Vide URL")
        if not ok:
            return
        x = self.youtube_init_video(url)
        if x:
            QtGui.QMessageBox.critical(self.main_window,"Youtube Video Error",x,"Dismiss")
        else:
            self.player_play()
    def ChangeQuality(self,str_qa):
        if not self.uilock:
            fmt = self.qa_map[str_qa]
            self.youtube_change_fmt(fmt)
    def PlayPause(self):
        if self.media_player.is_playing():
            self.player_pause()
        else:
            not self.player_play() or self.OpenYoutubeUrl()
    def OpenMrl(self):
        self.logger_ui.debug("Opening Generic MRL")
        mrl, ok = QtGui.QInputDialog.getText(self.main_window,"Open MRL","Enter a MRL/Path")
        if not ok: return
        self.player_open(mrl)
        self.player_play()
    def OpenFile(self):
        self.logger_ui.debug("Opening File")
        path = QtGui.QFileDialog.getOpenFileName(self.main_window, "Open Video File")
        if not path:
            return
        self.player_open(path)
        self.player_play()

if __name__=="__main__":
    if Version.PythonVersion.minVersion(3,2): #@UndefinedVariable
        logging.basicConfig(level=logging.DEBUG,format="[{msecs:09.3f}] {name:12} {levelname:5}: {msg}",style="{")
    else:
        logging.basicConfig(level=logging.DEBUG,format="[%(msecs)09.3f] %(name)-12s %(levelname)-5s: %(msg)s")
    app = Application(sys.argv)
    sys.exit(app.main())

