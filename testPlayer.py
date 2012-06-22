
from vlyc import player, util
from PyQt4 import QtCore
import logging, sys
logging.basicConfig(level=logging.DEBUG)

app = QtCore.QCoreApplication([])
p = player.Player()
p.timeChanged.connect(lambda i: print("Time: %s"%util.secstotimestr(int(i/1000)), end="\r"))
p.stateChanged.connect(lambda i: print("State Changed: %s %s"%(p.State.name(i), p.State.name(p.MediaPlayer.get_state()))))
def displayTrack(media):
    media.parse()
    print("Playing: %s"%media.get_meta(player.libvlc.Meta.Title))
p.mediaChanged.connect(displayTrack)
def debugger(event):
    if event.type not in (267, 268):
        print(player.EventManager.Event.name(event.type))
p.mpManager.set_debug(debugger)
p.endReached.connect(app.quit) #TODO: y u no work D:
t = QtCore.QTimer()
t.setInterval(10000)
def extest ():
    if not p.is_playing():
        if p.get_state() == p.State.Ended:
            print("QTimer: State==Ended!!!!!")
            app.quit()
class ConsoleThread(QtCore.QThread):
    KeyReceived = QtCore.pyqtSignal("QString")
    Quit = QtCore.pyqtSignal()
    Play = QtCore.pyqtSignal()
    Pause = QtCore.pyqtSignal()
    Stop = QtCore.pyqtSignal()
    def run(self):
        import tty, termios
        old = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin, termios.TCSANOW)
        self.terminated.connect(lambda: termios.tcsetattr(sys.stdin, termios.TCSANOW, old))
        while True:
            k = sys.stdin.read(1)
            self.KeyReceived.emit(k)
            if k=="q":
                self.Quit.emit()
            elif k==" ":
                self.Pause.emit()
            elif k=="p":
                self.Play.emit()
            elif k=="s":
                self.Stop.emit()

th = ConsoleThread()
th.started.connect(lambda: print("ConsoleThread Started!"))
th.start()
t.timeout.connect(extest)
t.start()
p.open(sys.argv[1])
th.Quit.connect(app.quit)
th.Play.connect(p.play)
def toggle_pause():
    if not p.is_playing():
        p.play()
    else:
        p.pause()
th.Pause.connect(toggle_pause)
th.Stop.connect(p.stop)
p.play()
app.exec_()
th.terminate()
