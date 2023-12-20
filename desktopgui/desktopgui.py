"""Desktop application for managing the LED matrix.
"""

import collections
import pathlib
import sys
import time

from PIL import ImageGrab, ImageQt, Image

from screengrab import main as screengrab

from PySide6 import QtCore, QtGui, QtWidgets, QtUiTools

Resolution = collections.namedtuple("Resolution", ["width", "height"])

DISPLAY_RESOLUTION = Resolution(width=128, height=128)

class DesktopApp(QtWidgets.QApplication):
  def __init__(self):
    self._app = QtWidgets.QApplication.__init__(self, sys.argv)
    ui_file = QtCore.QFile(pathlib.Path(__file__).parents[0] / "desktopgui.ui")
    if not ui_file.open(QtCore.QIODevice.ReadOnly):
        print("Cannot open 'desktopgui.ui'")
        sys.exit(-1)
    loader = QtUiTools.QUiLoader()
    self._window = loader.load(ui_file)
    self._grab_bbox = None
    self._is_streaming = False

    self._window.push_button_1_1.clicked.connect(lambda : self._launch_screengrab(width=128, height=128))
    self._window.push_button_1_2.clicked.connect(lambda : self._launch_screengrab(width=256, height=256))
    self._window.push_button_1_3.clicked.connect(lambda : self._launch_screengrab(width=384, height=384))
    self._window.push_button_1_4.clicked.connect(lambda : self._launch_screengrab(width=512, height=512))
    self._window.push_button_1_5.clicked.connect(lambda : self._launch_screengrab(width=640, height=640))
    self._window.push_button_1_6.clicked.connect(lambda : self._launch_screengrab(width=768, height=768))
    self._window.push_button_1_7.clicked.connect(lambda : self._launch_screengrab(width=896, height=896))
    self._window.push_button_1_8.clicked.connect(lambda : self._launch_screengrab(width=1024, height=1024))
    self._window.push_button_1_9.clicked.connect(lambda : self._launch_screengrab(width=1152, height=1152))
    self._window.push_button_arbitrary.clicked.connect(lambda : self._launch_screengrab(resizable=True))

    self._window.button_take_image.clicked.connect(self._take_image)
    self._window.button_live.clicked.connect(self._toggle_stream)

    self._update_enabledness()

    self._window.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
    self._window.setFixedSize(self._window.size())
    #self._window.layout().setSizeConstraint(QtWidgets.QLayout.SetFixedSize);
    self._window.show()

  def _launch_screengrab(self, width=128, height=128, resizable=False):
    self._hide()
    self._grab_bbox = screengrab(width=width, height=height, is_resizable=resizable)
    self._update_enabledness()
    self._show()

  def _update_enabledness(self):
    self._window.button_take_image.setEnabled(self._grab_bbox is not None)
    self._window.button_take_video.setEnabled(False)
    self._window.button_live.setEnabled(self._grab_bbox is not None)

  def _toggle_stream(self):
    self._is_streaming = not self._is_streaming
    if self._is_streaming:
        self._update_stream()

  def _update_stream(self):
    if self._is_streaming:
      self._grab_image()
      QtCore.QTimer.singleShot(1, self._update_stream)

  def _take_image(self):
    self._is_streaming = False
    self._grab_image()

  def _grab_image(self):
    assert self._grab_bbox is not None
    self._img = ImageGrab.grab(bbox=self._grab_bbox)
    if self._img.width != DISPLAY_RESOLUTION.width or self._img.height != DISPLAY_RESOLUTION.height:
      self._img = self._img.resize((DISPLAY_RESOLUTION.width,DISPLAY_RESOLUTION.height), resample=Image.BILINEAR)
    self._qt_img = ImageQt.ImageQt(self._img)
    self._qt_pix = QtGui.QPixmap.fromImage(self._qt_img)
    self._window.label_matrix_preview.setPixmap(self._qt_pix)

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
