"""
/*****************************************************************************
 * vlyc2::mainwindow : MainWindow
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

import logging

from PyQt4 import QtCore
from PyQt4 import QtGui

from . import vlc_res #@UnusedImport

from .input_slider import SeekSlider
from .widgets import SoundWidget
from .widgets import VideoWidget
from .widgets import TimeLabel
from .widgets import PlayButton
from .settings import Settings

logger = logging.getLogger(__name__)


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
        
        self.pageStack = QtGui.QStackedLayout(self.root_layout)
        self.pageStack.setObjectName("pageStack")

        #/---------------------------------------
        # Video Widget (page 0)
        #---------------------------------------/
        self.videoPage = QtGui.QWidget()
        self.videoPage.setLayout(QtGui.QHBoxLayout())
        self.pageStack.addWidget(self.videoPage)
        self.video_widget = VideoWidget(self.root_widget)
        self.video_widget.setObjectName("video_widget")
        self.video_widget.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        palette = self.video_widget.palette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(0, 0, 0))
        self.video_widget.setPalette(palette)
        self.video_widget.setAutoFillBackground(True)
        self.videoPage.layout().addWidget(self.video_widget)
        
        #/---------------------------------------
        # Videos Page
        #---------------------------------------/
        self.videosPage = QtGui.QWidget(self)
        self.videosPage.setObjectName("videosPage")
        self.pageStack.addWidget(self.videosPage)
        self.videosLayout = QtGui.QHBoxLayout(self.videosPage)
        self.videosLayout.setObjectName("videosLayout")
        self.videosLeftLayout = QtGui.QVBoxLayout()
        self.videosLeftLayout.setObjectName("videosLeftLayout")
        self.videosLayout.addLayout(self.videosLeftLayout)
        self.videosModeList = QtGui.QListWidget()
        self.videosModeList.setObjectName("videosModeList")
        self.videosLeftLayout.addWidget(self.videosModeList)
        self.videosStack = QtGui.QStackedLayout()
        self.videosStack.setObjectName("videosStack")
        self.videosLayout.addLayout(self.videosStack)
        
        # Search page
        self.videoSearchPage = QtGui.QWidget()
        self.videoSearchPage.setObjectName("videoSearchPage")
        self.videoSearchLayout = QtGui.QVBoxLayout(self.videoSearchPage)
        self.videoSearchLayout.setObjectName("videoSearchLayout")
        self.videoSearchTopLayout = QtGui.QHBoxLayout()
        self.videoSearchTopLayout.setObjectName("videoSearchTopLayout")
        self.videoSearchLayout.addLayout(self.videoSearchTopLayout)
        self.videoSearchInput = QtGui.QLineEdit()
        self.videoSearchInput.setObjectName("videoSearchInput")
        self.videoSearchTopLayout.addWidget(self.videoSearchInput)
        self.videoSearchButton = QtGui.QPushButton("Search")
        self.videoSearchButton.setObjectName("videoSearchButton")
        self.videoSearchTopLayout.addWidget(self.videoSearchButton)
        self.videoSearchResults = QtGui.QListWidget()
        self.videoSearchResults.setObjectName("videoSearchResults")
        self.videoSearchLayout.addWidget(self.videoSearchResults)
        self.videosStack.addWidget(self.videoSearchPage)
        self.videosModeList.addItem("Video Search")
        
        # Feed page
        self.videoFeedPage = QtGui.QWidget()
        self.videoFeedPage.setObjectName("videoFeedPage")
        self.videoFeedLayout = QtGui.QVBoxLayout(self.videoFeedPage)
        self.videoFeedLayout.setObjectName("videoFeedLayout")
        self.videoFeedTopLayout = QtGui.QHBoxLayout()
        self.videoFeedTopLayout.setObjectName("videoFeedTopLayout")
        self.videoFeedLayout.addLayout(self.videoFeedTopLayout)
        self.videoFeedInput = QtGui.QLineEdit()
        self.videoFeedInput.setObjectName("videoFeedInput")
        self.videoFeedTopLayout.addWidget(self.videoFeedInput)
        self.videoFeedButton = QtGui.QPushButton("Go")
        self.videoFeedButton.setObjectName("videoFeedButton")
        self.videoFeedTopLayout.addWidget(self.videoFeedButton)
        self.videoFeedResults = QtGui.QListWidget()
        self.videoFeedResults.setObjectName("videoFeedResults")
        self.videoFeedLayout.addWidget(self.videoFeedResults)
        self.videosStack.addWidget(self.videoFeedPage)
        self.videosModeList.addItem("API Feed")
        
        self.videosModeList.setCurrentRow(0)

        #/---------------------------------------
        # Time Toolbar
        #---------------------------------------/
        self.time_layout = QtGui.QHBoxLayout()
        self.time_layout.setObjectName("time_layout")

        self.seeker = SeekSlider(QtCore.Qt.Horizontal, self.root_widget,
            Settings().value("MainWindow/classic_slider", False))
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
        #self.play_button.setShortcut(" ")
        self.play_button.setFocusPolicy(QtCore.Qt.NoFocus)
        #self.play_button.setFixedSize(self.play_button.width(), self.play_button.height())
        self.control_layout.addWidget(self.play_button)

        self.stop_button = QtGui.QToolButton(self.root_widget)
        self.stop_button.setObjectName("stop_button")
        self.stop_button.setIcon(QtGui.QIcon(":/toolbar/stop_b"))
        self.stop_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.control_layout.addWidget(self.stop_button)

        self.control_layout.addStretch(10)
        
        self.pageSelectButton = QtGui.QToolButton(self.root_widget)
        self.pageSelectButton.setObjectName("pageSelectButton")
        self.pageSelectButton.setIcon(QtGui.QIcon(":/toolbar/playlist"))
        self.pageSelectButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.pageSelectButton.setCheckable(True)
        self.control_layout.addWidget(self.pageSelectButton)
        
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

        self.sound_widget = SoundWidget(self.root_widget,
            Settings().value("MainWindow/shiny_sound", True))
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
        
        self.tools_menu = self.menubar.addMenu("&Tools")
        self.tools_menu.setObjectName("tools_menu")
        
        self.tools_login_action = self.tools_menu.addAction("&Login")
        self.tools_login_action.setObjectName("tools_login_action")
        
        self.tools_webpage_action = self.tools_menu.addAction("open YouTube page")
        self.tools_webpage_action.setObjectName("tools_webpage_action")
        
        #self.tools_setPage_action = self.tools_menu.addAction("set pageStack index")
        #self.tools_setPage_action.setObjectName("tools_setPage_action")

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
    
    #/-----------------------------------------
    # Signals
    #-----------------------------------------/
    videoFeedQuery = QtCore.Signal("QString")
    searchVideoQuery = QtCore.Signal("QString")
    videoSelected = QtCore.Signal(QtGui.QListWidgetItem)
    
    @QtCore.Slot(list)
    def searchVideoResponse(self, lst):
        for i in lst:
            self.videoSearchResults.addItem(i)
    
    @QtCore.Slot(list)
    def videoFeedResponse(self, lst):
        for i in lst:
            self.videoFeedResults.addItem(i)
    
    #/-----------------------------------------
    # UI Signal handlers
    #-----------------------------------------/
    def connectAll(self):
        QtCore.QMetaObject.connectSlotsByName(self)
        self.videoSearchResults.itemActivated.connect(self.videoSelected)
        self.videoFeedResults.itemActivated.connect(self.videoSelected)
    
    @QtCore.Slot(int)
    def on_videosModeList_currentRowChanged(self, row):
        self.videosStack.setCurrentIndex(row)
    
    @QtCore.Slot(int)
    def on_pageStack_currentChanged(self, i):
        if i == 0:
            self.videoPage.layout().addWidget(self.video_widget)
        elif i == 1:
            self.videosLeftLayout.addWidget(self.video_widget)
    
    @QtCore.Slot()
    def on_videoSearchButton_clicked(self):
        self.videoSearchResults.clear()
        self.searchVideoQuery.emit(self.videoSearchInput.text())
    
    @QtCore.Slot()
    def on_videoFeedButton_clicked(self):
        self.videoFeedResults.clear()
        self.videoFeedQuery.emit(self.videoFeedInput.text())
    
    @QtCore.Slot()
    def on_tools_setPage_action_triggered(self):
        i, ok = QtGui.QInputDialog.getInt(self, "Set pageStack index", "", value=self.pageStack.currentIndex(), min=0, max=self.pageStack.count(), step=1)
        if not ok:
            return
        self.pageStack.setCurrentIndex(i)
    
    @QtCore.Slot()
    def on_pageSelectButton_clicked(self):
        if self.pageSelectButton.isChecked():
            self.pageStack.setCurrentIndex(1)
        else:
            self.pageStack.setCurrentIndex(0)

    #/-------------------------------------------
    # arbitary stuffs
    #-------------------------------------------/
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.__logger = logging.getLogger("vlyc.ui.MainWindow")
        self.setupUi()
        self.connectAll()
        self.resize(Settings().value("MainWindow/size", self.size()))
        self.move(Settings().value("MainWindow/position", self.pos()))

    def savePosition(self):
        self.__logger.debug("MainWindow: saving position") #@UndefinedVariable
        Settings().setValue("MainWindow/position", self.pos())
        Settings().setValue("MainWindow/size", self.size())
    
    def closeEvent(self, e):
        QtGui.qApp.quit()
