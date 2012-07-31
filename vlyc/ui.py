"""
/*****************************************************************************
 * vlyc2.py : libVLC YouTube Player GUI 
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
import logging

from PyQt4 import QtCore
from PyQt4 import QtGui

from . import vlc_res #@UnusedImport

from .input_slider import SeekSlider
from .widgets import SoundWidget
from .widgets import VideoWidget
from .widgets import TimeLabel
from .widgets import PlayButton
from .fullscreen import Controller as BaseFullscreenController
from .settings import Settings

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
        self.video_widget = VideoWidget(self.root_widget)
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

        self.seeker = SeekSlider(QtCore.Qt.Horizontal, self.root_widget, Settings().value("MainWindow/classic_slider",False))
        self.seeker.setObjectName("seeker")
        self.time_layout.addWidget(self.seeker)

        self.time_label = TimeLabel(TimeLabel.Display.Both) #@UndefinedVariable
        self.time_label.setObjectName("time_label")
        self.time_layout.addWidget(self.time_label)

        self.root_layout.addLayout(self.time_layout)

        #/---------------------------------------
        # Control Toolbar
        #---------------------------------------/
        self.control_layout = QtGui.QHBoxLayout()
        self.control_layout.setObjectName("control_layout")

        self.play_button = PlayButton(self.root_widget)
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

        self.sound_widget = SoundWidget(self.root_widget, Settings().value("MainWindow/shiny_sound",True))
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
        
        self.help_menu = self.menubar.addMenu("&Help")
        self.help_menu.setObjectName("help_menu")
        
        self.help_about_action = self.help_menu.addAction("&About")
        self.help_about_action.setObjectName("help_about_action")

        self.setMenuBar(self.menubar)

        #/---------------------------------------
        # Status Bar
        #---------------------------------------/
        self.statusbar = QtGui.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")

        self.setStatusBar(self.statusbar)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.__logger = logging.getLogger("vlyc.ui.MainWindow")
        self.setupUi()
        self.resize(Settings().value("MainWindow/size",self.size()))
        self.move(Settings().value("MainWindow/position",self.pos()))

    def savePosition(self):
        self.__logger.debug("MainWindow: saving position") #@UndefinedVariable
        Settings().setValue("MainWindow/position",self.pos())
        Settings().setValue("MainWindow/size",self.size())

class FullscreenController(BaseFullscreenController):
    def createUiInput(self):
        layout = QtGui.QHBoxLayout()

        self.seeker = SeekSlider(QtCore.Qt.Horizontal, None, True)
        self.seeker.setObjectName("fscSeeker")
        layout.addWidget(self.seeker)

        self.time_label = TimeLabel(TimeLabel.Display.Both) #@UndefinedVariable
        self.time_label.setObjectName("fscTimeLabel")
        layout.addWidget(self.time_label)

        return layout

    def createUiFscToolbar(self):
        layout = QtGui.QHBoxLayout()

        self.play_b = PlayButton()
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

        self.sound_w = SoundWidget(None, True)
        self.sound_w.setObjectName("fscSoundWidget")
        layout.addWidget(self.sound_w)

        return layout

class AboutDialog(QtGui.QDialog):
    def __init__(self,parent=None):
        super(AboutDialog,self).__init__(parent);
        self.setupUi();

    def setupUi(self):
        tr = QtCore.QCoreApplication.instance().translate
        
        self.setObjectName("AboutDialog");
        self.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed);
        self.setWindowTitle(tr("AboutDialog","About VLYC"))
        self.resize(500,400);
        
        self.root_layout = QtGui.QVBoxLayout(self);
        self.root_layout.setObjectName("root_layout");
        
        from libyo.version import Version;
        from vlc.libvlc import libvlc_get_version;
        from platform import platform,architecture,machine,python_version,python_implementation;
        self.about_text = QtGui.QTextEdit(self);
        self.about_text.setObjectName("about_text");
        self.about_text.setReadOnly(True);
        self.about_text.setHtml(tr("AboutDialog",
"""<b>VideoLan YouTube Client</b> <i>{vlyc_version}</i><br>
<br>
This Program is not affilited with or approved by the VideoLan Organization.
The Program name is based soely on the fact that it uses the VLC library.<br>
<hr>
<table><tbody>
<tr><td colspan=2><b>Library Versions</b></td></tr>
<tr><td>Platform</td><td>{platform} ({arch})</td></tr>
<tr><td>Python</td><td>{python_version} {python_implementation}{frozen}</td></tr>
<tr><td>libvlc</td><td>{libvlc_version}</td></tr>
<tr><td>libyo</td><td>{libyo_version}</td></tr>
<tr><td>Qt</td><td>{qt_version}</td></tr>
<tr><td>PyQt4</td><td>{pyqt4_version}</td></tr>
</tbody></table>
<hr>
<table><tbody>
<tr><td colspan=2><b>Copyright</b></td></tr>
<tr><td>VLYC</td><td>&copy; 2012 Orochimarufan</td></tr>
<tr><td>UI design & code</td><td>&copy; the VideoLan Team and Orochimarufan</td></tr>
<tr><td>libvlc</td><td>&copy; <a href="http://www.videolan.org">the VideoLan Team and VLC contributors</a></td></tr>
<tr><td>libyo</td><td>&copy; Orochimarufan</td></tr>
<tr><td>Qt</td><td>&copy; <a href="http://qt.nokia.com">Nokia and/or it's subsidiaries</a></td></tr>
<tr><td>PyQt4</td><td>&copy; <a href="http://riverbankcomputing.co.uk/">Riverbank Computing Limited</a></td></tr>
</tbody></table>
<hr>
<b>License</b><br>
<br>
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or <-- Qt is GPLv3, others are GPLv2, use GPLv3 -->
(at your option) any later version.<br>
<br>
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.<br>
<br>
You should have received a copy of the GNU General Public License
along with this program.  If not, see &lt;<a href="http://www.gnu.org/licenses/">http://www.gnu.org/licenses/</a>&gt;.<br>
""").format(python_version=python_version(),
            python_implementation=python_implementation(),
            frozen=" (frozen binary distribution)" if hasattr(sys,"frozen") else "",
            vlyc_version=QtCore.QCoreApplication.instance().applicationVersion(),
            libvlc_version=str(libvlc_get_version(),"latin-1"),
            libyo_version=Version.LibyoVersion.format(), #@UndefinedVariable
            qt_version=QtCore.qVersion(),
            pyqt4_version=QtCore.PYQT_VERSION_STR,
            platform=platform(),
            arch="%s on %s"%(architecture()[0],machine())));
        self.about_text.setFocusPolicy(QtCore.Qt.NoFocus);
        self.root_layout.addWidget(self.about_text);
        
        self.button_box = QtGui.QHBoxLayout();
        self.button_box.setObjectName("button_box");
        self.root_layout.addLayout(self.button_box);
        
        self.about_qt_button = QtGui.QPushButton(self);
        self.about_qt_button.setObjectName("about_qt_button");
        self.about_qt_button.setText(tr("AboutDialog","About Qt"));
        self.about_qt_button.clicked.connect(QtGui.QApplication.instance().aboutQt);
        self.button_box.addWidget(self.about_qt_button);
        
        self.button_box.addStretch();
        
        self.close_button = QtGui.QPushButton(self);
        self.close_button.setObjectName("close_button");
        self.close_button.setText(tr("AboutDialog","Ok"));
        self.close_button.clicked.connect(self.close);
        self.button_box.addWidget(self.close_button);
        
        self.close_button.setFocus(True);
