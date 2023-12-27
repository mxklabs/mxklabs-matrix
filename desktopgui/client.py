"""Desktop application for managing the LED matrix.
"""

import collections
import io
import json
import pathlib
import sys
import threading
import time

from PIL import Image, ImageChops, ImageFilter, ImageGrab

from screengrab import main as screengrab
import gifgrabber

from PyQt6 import QtCore, QtGui, QtWidgets, uic

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

class SlotWidget(QtWidgets.QWidget):
  def __init__(self):
    QtWidgets.QWidget.__init__(self)
    uic.loadUi(pathlib.Path(__file__).parents[0] / "slotwidget.ui", self)

class ClientApp(QtWidgets.QMainWindow):
  _screen_preview_thread_fired = QtCore.pyqtSignal(name="previewThreadFired")
  _gif_grabber_done = QtCore.pyqtSignal(int, name="videoGrabberDone")

  def __init__(self, client_handler):
    QtWidgets.QMainWindow.__init__(self, parent=None)
    self._client_handler = client_handler
    self._window = uic.loadUi(pathlib.Path(__file__).parents[0] / "client.ui")

    self._grab_bbox = None
    self._is_streaming = False
    self._preview_img_unscaled = None
    self._preview_img = None

    self._screen_preview_timer = QtCore.QTimer(self)
    self._screen_preview_timer.timeout.connect(self._update_screen_preview)

    self._gif_grabber = None
    self._gif_grabber_done.connect(self._process_gif_grabber_done)

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
    self._window.button_go_live_stream.clicked.connect(self._button_go_live_stream_clicked)
    # self._window.button_take_image.clicked.connect(self._take_image)
    # self._window.button_live.clicked.connect(self._toggle_stream)

    # slot_layout = QtWidgets.QVBoxLayout()

    # .setLayout(slot_layout)#

    self._window.label_screen_preview.setMinimumSize(MATRIX_WIDTH, MATRIX_HEIGHT)
    self._window.label_screen_preview.setMaximumSize(MATRIX_WIDTH, MATRIX_HEIGHT)
    self._window.layout().activate()

    self._window.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
    self._window.setFixedSize(self._window.size())

    self._slot_widgets = []

    for slot in range(CONFIG['numSlots']):
      self._slot_widgets.append(SlotWidget())
      self._slot_widgets[-1].label.setText(f"Slot {slot}:")
      self._slot_widgets[-1].button_get_img.clicked.connect(lambda _,slot=slot: self._process_slot_get_img_click(slot))
      self._slot_widgets[-1].button_get_vid.clicked.connect(lambda _,slot=slot: self._process_slot_get_vid_click(slot))
      self._window.scroll_area_slots_contents.layout().addWidget(self._slot_widgets[-1])

    self._window.scroll_area_slots_contents.layout().addStretch()

    self._update_enabledness()
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
      self._show()
      self._grab_bbox = None
      self._screen_preview_timer.stop
      # self._kill_update_preview_thread()

  def _update_enabledness(self):
    self._window.button_go_live_snapshot.setEnabled(self._grab_bbox is not None)
    self._window.button_go_live_stream.setEnabled(self._grab_bbox is not None)
    for slot in range(CONFIG['numSlots']):
      self._slot_widgets[slot].setEnabled(self._grab_bbox is not None)
    # self._window.button_take_video.setEnabled(False)
    # self._window.button_live.setEnabled(self._grab_bbox is not None)
    pass

  def _button_go_live_snapshot_clicked(self):
    self._client_handler.process_go_live_screenshot()

  def _button_go_live_stream_clicked(self):
    self._client_handler.process_go_live_stream()

  def _process_slot_get_img_click(self, slot):
    assert self._preview_img is not None
    self._client_handler.process_set_slot(slot, self._preview_img)

  def _process_slot_get_vid_click(self, slot):
    self._gif_grabber = gifgrabber.GIFGrabber(callback=lambda slot=slot:self._gif_grabber_done.emit(slot))
    print(f"Getting slot {slot} video.")

  def _process_gif_grabber_done(self, slot):
    imgs = self._gif_grabber.imgs()
    durs = self._gif_grabber.durations()  
    self._client_handler.process_set_slot_vid(slot, imgs, durs)
    self._gif_grabber = None

  def _update_screen_preview(self):
    # Take an image.
    assert self._grab_bbox is not None
    new_preview_img = ImageGrab.grab(bbox=self._grab_bbox)
    if new_preview_img.width != MATRIX_WIDTH or new_preview_img.height != MATRIX_HEIGHT:
      resample_method = self._window.combo_resample_method.itemData(self._window.combo_resample_method.currentIndex())
      new_preview_img = new_preview_img.resize((MATRIX_WIDTH, MATRIX_HEIGHT), resample=resample_method)
    if self._window.checkbox_sharpen.isChecked():
      new_preview_img = new_preview_img.filter(ImageFilter.SHARPEN)
    self._preview_img = new_preview_img

    # Call handler.
    self._client_handler.process_screen_image(self._preview_img)
    if self._gif_grabber is not None:
      self._gif_grabber.feed_img(self._preview_img)

    # Update preview widget.
    self._qt_img = PIL_to_qimage(self._preview_img)
    self._qt_pix = QtGui.QPixmap.fromImage(self._qt_img, QtCore.Qt.ImageConversionFlag.AutoColor)
    self._window.label_screen_preview.setPixmap(self._qt_pix)

  def _hide(self):
    self._window.hide()

  def _show(self):
    self._window.show()

  def exec(self):
    QtWidgets.QApplication.exec()

def main(width=128, height=128):
  import clientlogic
  app = QtWidgets.QApplication(sys.argv)
  client_logic = clientlogic.ClientLogic()
  client_app = ClientApp(client_logic)
  app.exec()


if __name__ == "__main__":
  main()
