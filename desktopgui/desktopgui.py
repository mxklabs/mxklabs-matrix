"""Desktop application for managing the LED matrix.
"""

import pathlib
import sys
import time

from PIL import ImageGrab, ImageQt

from screengrab import main as screengrab

from PyQt6 import QtCore, QtGui, QtWidgets, uic

class DesktopApp(QtWidgets.QApplication):
  def __init__(self):
    QtWidgets.QApplication.__init__(self, sys.argv)
    self._window = uic.loadUi(pathlib.Path(__file__).parents[0] / "desktopgui.ui")
    self._grab_bbox = None

    self._window.push_button_1_1.clicked.connect(lambda : self._launch_screengrab(width=128, height=128))
    self._window.push_button_1_2.clicked.connect(lambda : self._launch_screengrab(width=256, height=256))
    self._window.push_button_1_3.clicked.connect(lambda : self._launch_screengrab(width=384, height=384))
    self._window.push_button_1_4.clicked.connect(lambda : self._launch_screengrab(width=512, height=512))
    self._window.push_button_1_5.clicked.connect(lambda : self._launch_screengrab(width=640, height=640))
    self._window.push_button_1_6.clicked.connect(lambda : self._launch_screengrab(width=768, height=768))
    self._window.push_button_1_7.clicked.connect(lambda : self._launch_screengrab(width=896, height=896))
    self._window.push_button_1_8.clicked.connect(lambda : self._launch_screengrab(width=1024, height=1024))
    self._window.push_button_arbitrary.clicked.connect(lambda : self._launch_screengrab(resizable=True))

    self._window.push_button_image.clicked.connect(self._grab_image)

    self._update_enabledness()

    self._window.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
    self._window.show()

  def _launch_screengrab(self, width=128, height=128, resizable=False):
    self._hide()
    self._grab_bbox = screengrab(width=width, height=height, is_resizable=resizable)
    self._update_enabledness()
    self._show()

  def _update_enabledness(self):
    self._window.push_button_image.setEnabled(self._grab_bbox is not None)

  def _grab_image(self):
    assert self._grab_bbox is not None
    print(self._grab_bbox)
    img = ImageGrab.grab(bbox=self._grab_bbox)
    qt_img = ImageQt.ImageQt(img)
    qt_pix = QtGui.QPixmap.fromImage(qt_img)
    self._window.label_matrix_preview.setPixmap(qt_pix)

  def _hide(self):
    self._window.hide()

  def _show(self):
    self._window.show()

  def exec(self):
    QtWidgets.QApplication.exec()

def main(width=128, height=128):
  app = DesktopApp()
  app.exec()


if __name__ == "__main__":
  main()
