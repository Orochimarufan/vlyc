'''
Created on 12.06.2012

@author: hinata
'''

import sip
sip.setapi("QString",2)
from PyQt4 import QtGui
import libvlc
import time

class Application(QtGui.QApplication):
    def main(self):
        print("init")
        self.frame = QtGui.QFrame()
        self.inst = libvlc.Instance()
        self.player = self.inst.media_player_new(self.arguments()[1])
        print("xwindow: %i"%self.frame.winId())
        self.player.set_xwindow(self.frame.winId())
        print("play")
        self.frame.show()
        self.player.play()
        self.processEvents()
        time.sleep(5)
        while self.player.is_playing():
            time.sleep(5)
        print("exit")
        self.quit()

if __name__=="__main__":
    import sys
    app = Application(sys.argv)
    app.main()