'''
/*****************************************************************************
 * actions_manager.py : Controller for the main interface
 ****************************************************************************
 * Copyright (C) 2006-2008 the VideoLAN team
 * $Id: 93a346c230f4f35240011b9d02ad8af020db8f50 $
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

from PyQt4 import QtCore;

from .util import AutoEnum;

actionType_e = AutoEnum("actionType_e",
    # VLC Actions
    "PLAY_ACTION",
    "STOP_ACTION",
    "OPEN_ACTION",
    "PREVIOUS_ACTION",
    "NEXT_ACTION",
    "SLOWER_ACTION",
    "FASTER_ACTION",
    "FULLSCREEN_ACTION",
    "FULLWIDTH_ACTION",
    "EXTENDED_ACTION",
    "PLAYLIST_ACTION",
    "SNAPSHOT_ACTION",
    "RECORD_ACTION",
    "FRAME_ACTION",
    "ATOB_ACTION",
    "REVERSE_ACTION",
    "SKIP_BACK_ACTION",
    "SKIP_FW_ACTION",
    "QUIT_ACTION",
    "RANDOM_ACTION",
    "LOOP_ACTION",
    "INFO_ACTION",
    "OPEN_SUB_ACTION",
    # Custom Actions
    OPEN_YOUTUBE_ACTION=0x50,
);
actionType_e.export();

class ActionsManager(QtCore.QObject):
    _instance=None;
    def __init__(self,app,parent):
        super(ActionsManager,self).__init__(parent);
        self.app = app
        self.logger = app.logger_ui.getChild("ActionsManager")
    @classmethod
    def getInstance(cls,app,parent):
        if (cls._instance is None):
            cls._instance = cls(app,parent);
        return cls._instance;
    @classmethod
    def killInstance(cls):
        del cls._instance;
        cls._instance = None;
    
    def doAction(self,action):
        """ Dispatch Actions """
        case = lambda v: v==action;
        if case( PLAY_ACTION ):
            self.play();
        elif case( STOP_ACTION ):
            self.stop();
        elif case( OPEN_ACTION ):
            self.openDialog();
        elif case( PREVIOUS_ACTION ):
            self.prev();
        elif case( NEXT_ACTION ):
            self.next();
        elif case( SLOWER_ACTION ):
            self.slower();
        elif case( FASTER_ACTION ):
            self.faster();
        elif case( FULLSCREEN_ACTION ):
            self.fullscreen();
        elif case( EXTENDED_ACTION ):
            self.extendedDialog();
        elif case( PLAYLIST_ACTION ):
            self.playlist();
        elif case( SNAPSHOT_ACTION ):
            self.snapshot();
        elif case( RECORD_ACTION ):
            self.record();
        elif case( FRAME_ACTION ):
            self.frame();
        elif case( ATOB_ACTION ):
            self.setAtoB();
        elif case( REVERSE_ACTION ):
            self.reverse();
        elif case( SKIP_BACK_ACTION ):
            self.skipBackward();
        elif case( SKIP_FW_ACTION ):
            self.skipForward();
        elif case( QUIT_ACTION ):
            self.app.quit();
        elif case( RANDOM_ACTION ):
            self.toggleRandom();
        elif case( INFO_ACTION ):
            self.mediaInfoDialog();
        elif case( OPEN_SUB_ACTION ):
            self.loadSubtitlesFile();
        elif case( FULLWIDTH_ACTION ):
            self.app.FSController.toggleFullWidth();
        else:
            self.logger.debug("Action: %i"%action );
    
    def play(self):
        if self.app.playlist.current.i_size==0:
            self.openYoutubeDialog();
        else:
            self.app.player.togglePlayPause();
    
    def fullscreen(self):
        self.app.player.setFullscreen(not self.app.video.fullscreen());
    
    def playlist(self):
        self.app.ui.togglePlaylist();
    
    def record(self):
        self.logger.warn("Tried to record. Not supported!");
    
    def frame(self):
        self.app.player.nextFrame();
    
    def mute(self):
        self.app.player.toggleMute();
    
    def volumeUp(self):
        self.app.player.volumeUp();
    
    def volumeDn(self):
        self.app.player.volumeDn();