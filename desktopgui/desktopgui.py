"""Desktop application for managing the LED matrix.
"""

import collections
import io
import json
import pathlib
import sys
import threading
import time

from PIL import ImageGrab, Image

from screengrab import main as screengrab

from PyQt6 import QtCore, QtGui, QtWidgets, uic

import clientapi

Resolution = collections.namedtuple("Resolution", ["width", "height"])

with open(pathlib.Path(__file__).parents[0] / "config.json", "r") as f:
    CONFIG = json.load(f)
    MATRIX_WIDTH = CONFIG['matrixWidth']
    MATRIX_HEIGHT = CONFIG['matrixHeight']


def PIL_to_qimage(pil_img):
    temp = pil_img.convert('RGBA')
    return QtGui.QImage(
        temp.tobytes('raw', "RGBA"),
        temp.size[0],
        temp.size[1],
        QtGui.QImage.Format.Format_RGBA8888
    )

class DesktopApp(QtWidgets.QMainWindow):
  _screen_preview_thread_fired = QtCore.pyqtSignal(name="previewThreadFired")

  def __init__(self):
    QtWidgets.QMainWindow.__init__(self, parent=None)
    self._window = uic.loadUi(pathlib.Path(__file__).parents[0] / "desktopgui.ui")
    self._device = clientapi.ClientAPI()
    self._grab_bbox = None
    self._is_streaming = False

    self._last_preview_bytes = None
    self._screen_preview_timer = QtCore.QTimer(self)
    self._screen_preview_timer.timeout.connect(self._update_screen_preview)

    # self._screen_preview_thread = None
    # self._screen_preview_thread_kill_event = threading.Event()
    # self._screen_preview_thread_fired.connect(self._grab_image)

    self._window.combo_resample_method.addItem("Nearest", Image.NEAREST)
    self._window.combo_resample_method.addItem("Bilinear", Image.BILINEAR)
    self._window.combo_resample_method.addItem("Bicubic", Image.BICUBIC)
    self._window.combo_resample_method.addItem("Lanczos", Image.LANCZOS)
    self._window.combo_resample_method.setCurrentIndex(1)

    self._window.push_button_1_1.clicked.connect(lambda : self._set_screen_area(width=1*MATRIX_WIDTH, height=1*MATRIX_HEIGHT))
    self._window.push_button_1_2.clicked.connect(lambda : self._set_screen_area(width=2*MATRIX_WIDTH, height=2*MATRIX_HEIGHT))
    self._window.push_button_1_3.clicked.connect(lambda : self._set_screen_area(width=3*MATRIX_WIDTH, height=3*MATRIX_HEIGHT))
    self._window.push_button_1_4.clicked.connect(lambda : self._set_screen_area(width=4*MATRIX_WIDTH, height=4*MATRIX_HEIGHT))
    self._window.push_button_1_5.clicked.connect(lambda : self._set_screen_area(width=5*MATRIX_WIDTH, height=5*MATRIX_HEIGHT))
    self._window.push_button_1_6.clicked.connect(lambda : self._set_screen_area(width=6*MATRIX_WIDTH, height=6*MATRIX_HEIGHT))
    self._window.push_button_1_7.clicked.connect(lambda : self._set_screen_area(width=7*MATRIX_WIDTH, height=7*MATRIX_HEIGHT))
    self._window.push_button_1_8.clicked.connect(lambda : self._set_screen_area(width=8*MATRIX_WIDTH, height=8*MATRIX_HEIGHT))
    self._window.push_button_any_fixed_ratio.clicked.connect(lambda : self._set_screen_area(resizable=True, fixed_ratio=True))
    self._window.push_button_any.clicked.connect(lambda : self._set_screen_area(resizable=True, fixed_ratio=False))

    self._window.button_go_live_snapshot.clicked.connect(self._button_go_live_snapshot_clicked)
    # self._window.button_take_image.clicked.connect(self._take_image)
    # self._window.button_live.clicked.connect(self._toggle_stream)

    self._update_enabledness()

    self._window.label_screen_preview.setMinimumSize(MATRIX_WIDTH, MATRIX_HEIGHT)
    self._window.label_screen_preview.setMaximumSize(MATRIX_WIDTH, MATRIX_HEIGHT)
    self._window.layout().activate()

    self._window.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
    self._window.setFixedSize(self._window.size())
    self._window.show()

    #self._window.layout().setSizeConstraint(QtWidgets.QLayout.SetFixedSize);
    self._window.show()

  def _set_screen_area(self, width=128, height=128, resizable=False, fixed_ratio=True):
    """ Launch screengrabber pygame window to select area of the screen. """
    # Do something.
    try:
      self._hide()
      self._grab_bbox = screengrab(width=width, height=height, is_resizable=resizable, fixed_ratio=fixed_ratio)
      self._update_enabledness()
      self._show()

      # Ensure we can see a preview image.
      self._screen_preview_timer.stop()
      self._screen_preview_timer.start(CONFIG['screenPreviewUpdateMillis'])

    except:
      # If something fails, deal with it.
      self._grab_bbox = None
      self._screen_preview_timer.stop
      # self._kill_update_preview_thread()

  def _update_enabledness(self):
    self._window.button_go_live_snapshot.setEnabled(self._grab_bbox is not None)
    # self._window.button_take_video.setEnabled(False)
    # self._window.button_live.setEnabled(self._grab_bbox is not None)
    pass

  # def _take_image(self):
  #   self._is_streaming = False
  #   self._grab_image()
  #   arr = io.BytesIO()
  #   self._img.save(arr, format="gif")
  #   print(arr.getvalue())
  #   self._device.set_slot(0, arr.getvalue())

  def _button_go_live_snapshot_clicked(self):
    # print('_button_go_live_snapshot_clicked')
    if self._last_preview_bytes is not None:
      self._device.set_slot(0, self._last_preview_bytes)
    # mem = QtCore.QBuffer(self)
    
    # self._window.label_screen_preview.pixmap().save(mem, "GIF")
    # print(bytes(mem.data()).decode())
    # self._device.set_slot(0, bytes(mem.data()).decode())
    # qimage = pixmap.toImage()
    # pass


  def _update_screen_preview(self):
    assert self._grab_bbox is not None
    self._img = ImageGrab.grab(bbox=self._grab_bbox)
    if self._img.width != MATRIX_WIDTH or self._img.height != MATRIX_HEIGHT:
      resample_method = self._window.combo_resample_method.itemData(self._window.combo_resample_method.currentIndex())
      self._img = self._img.resize((MATRIX_WIDTH, MATRIX_HEIGHT), resample=resample_method)

    arr = io.BytesIO()
    self._img.save(arr, format="gif")
    self._last_preview_bytes = arr.getvalue()
    self._qt_img = PIL_to_qimage(self._img)
    self._qt_pix = QtGui.QPixmap.fromImage(self._qt_img, QtCore.Qt.ImageConversionFlag.AutoColor)
    self._window.label_screen_preview.setPixmap(self._qt_pix)

  def _hide(self):
    self._window.hide()

  def _show(self):
    self._window.show()

  def exec(self):
    QtWidgets.QApplication.exec()

def main(width=128, height=128):
  app = QtWidgets.QApplication(sys.argv)
  window = DesktopApp()
  window.show()
  app.exec()


if __name__ == "__main__":
  main()
