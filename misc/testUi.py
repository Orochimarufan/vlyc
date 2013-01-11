from vlyc import input_slider
from PyQt4 import QtCore,QtGui

app = QtGui.QApplication([])
from vlyc import vlc_res
#sl = input_slider.SoundSlider(None,2,False,"2;3;4;5;6;7;8;9;33;99;150")
sl = input_slider.SeekSlider(QtCore.Qt.Horizontal, None, True)
sl.show()
app.exec_()
