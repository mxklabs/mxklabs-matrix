"""Desktop application for managing the LED matrix.
"""

import collections
import json
import pathlib
import sys
import html.parser

from PIL import Image, ImageFilter, ImageGrab, ImageOps

from screengrab import main as screengrab
import gifgrabber

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from clientlogic import ClientLogic
    from slotmanager import SlotManager

from PyQt6 import QtCore, QtGui, QtWidgets, uic

class HTMLImgFinder(html.parser.HTMLParser):
    def __init__(self):
       html.parser.HTMLParser.__init__(self)
       self.imgs = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            for k, v in attrs:
               if k == "src":
                  self.imgs.append(v)

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
    def __init__(self, parent, slot):
        QtWidgets.QWidget.__init__(self)
        uic.loadUi(pathlib.Path(__file__).parents[0] / "slotwidget.ui", self)
        self.parent = parent
        self.slot = slot

        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):
        mime = e.mimeData()
        if mime.hasUrls():
            #Check for URLS (local files only)
            num_local_files = 0
            local_file = None
            for url in mime.urls():
                if url.isLocalFile():
                    local_file = url.toLocalFile()
                    num_local_files += 1
            if num_local_files > 1:
               e.ignore()
               return
            if num_local_files == 1:
               e.accept()
               return
        if mime.hasHtml():
          parser = HTMLImgFinder()
          parser.feed(mime.html())
          if len(parser.imgs) >= 1:
            e.accept()
            return
        e.ignore()

 
    def dropEvent(self, e):
        mime = e.mimeData()
        if mime.hasUrls():
            #Check for URLS (local files only)
            num_local_files = 0
            local_file = None
            for url in mime.urls():
                if url.isLocalFile():
                    local_file = url.toLocalFile()
                    num_local_files += 1
            if num_local_files > 1:
               e.ignore()
               raise ValueError(f"Cannot handle drag and drop of more than one file.")
            if num_local_files == 1:
               e.accept()
               res = self.parent._client_logic.process_slot_load(self.parent._window, self.slot, local_file)
               return res
        if mime.hasHtml():
          parser = HTMLImgFinder()
          parser.feed(mime.html())
          if len(parser.imgs) >= 1:
            e.accept()
            res = self.parent._client_logic.process_slot_load_network(self.parent._window, self.slot, parser.imgs[0])
            return res
        e.ignore()

class VidWaitDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Capturing animation...")

        QBtn = QtWidgets.QDialogButtonBox.StandardButton.Cancel | QtWidgets.QDialogButtonBox.StandardButton.Save

        self._buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)

        self._layout = QtWidgets.QVBoxLayout()
        self._layout.setContentsMargins(20, 20, 20, 20)
        self._layout.setSpacing(20)
        message = QtWidgets.QLabel("Either wait for the animation to loop and, or\npress 'Cancel' to cancel or press 'Save'\nto save the frames collected so far.")
        self._layout.addWidget(message)
        self._layout.addWidget(self._buttonBox)
        self.setLayout(self._layout)

    @property
    def accepted(self):
        return self._buttonBox.accepted

    @property
    def rejected(self):
        return self._buttonBox.rejected


class ClientApp(QtWidgets.QMainWindow):
  # _slot_load = QtCore.pyqtSignal(int, name="slotLoad")
  # _save_all = QtCore.pyqtSignal(name="saveAll")
  # _load_all = QtCore.pyqtSignal(name="loadAll")
  _gif_grabber_done = QtCore.pyqtSignal(int, name="videoGrabberDone")

  def __init__(self, client_logic : 'ClientLogic', slot_manager : 'SlotManager'):
    QtWidgets.QMainWindow.__init__(self, parent=None)
    self._client_logic = client_logic
    self._slot_manager = slot_manager
    self._window = uic.loadUi(pathlib.Path(__file__).parents[0] / "client.ui")

    self._grab_bbox = self._client_logic.get_client_data("bbox", None)
    self._is_streaming = False
    self._preview_img_unscaled = None
    self._preview_img = None

    self._screen_preview_timer = QtCore.QTimer(self)
    self._screen_preview_timer.timeout.connect(self._update_screen_preview)

    self._gif_grabber = None
    self._gif_grabber_done.connect(self._process_gif_grabber_done)
    self._gif_grabber_dialog = None

    self._window.combo_resample_method.addItem("Nearest", Image.NEAREST)
    self._window.combo_resample_method.addItem("Bilinear", Image.BILINEAR)
    self._window.combo_resample_method.addItem("Bicubic", Image.BICUBIC)
    self._window.combo_resample_method.addItem("Lanczos", Image.LANCZOS)
    self._window.combo_resample_method.setCurrentIndex(1)

    self._window.combo_resize_method.addItem("Stretch", lambda im, size, resample: im.resize(size, resample=resample))
    self._window.combo_resize_method.addItem("Crop", lambda im, size, resample: ImageOps.fit(im, size, method=resample))
    self._window.combo_resize_method.addItem("Pad", lambda im, size, resample: ImageOps.pad(im, size, method=resample, color=(0,0,0)))
    self._window.combo_resize_method.setCurrentIndex(1)

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
    self._window.button_go_round_robin.clicked.connect(self._button_go_round_robin_clicked)

    self._window.button_save_all_slots.clicked.connect(self._button_save_all_slots_clicked)
    self._window.button_load_all_slots.clicked.connect(self._button_load_all_slots_clicked)
    self._window.button_go_black.clicked.connect(self._button_go_black_clicked)

    self._window.label_screen_preview.setMinimumSize(MATRIX_WIDTH, MATRIX_HEIGHT)
    self._window.label_screen_preview.setMaximumSize(MATRIX_WIDTH, MATRIX_HEIGHT)
    self._window.layout().activate()

    # self._window.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
    self._window.setFixedSize(self._window.size())

    self._slot_widgets = []

    for slot in range(CONFIG['numSlots']):
      self._slot_widgets.append(SlotWidget(self, slot))
      self._slot_widgets[-1].label.setText(f"Slot {slot}:")
      self._slot_widgets[-1].button_clear.clicked.connect(lambda _,slot=slot: self._process_slot_clear_click(slot))
      self._slot_widgets[-1].button_get_img.clicked.connect(lambda _,slot=slot: self._process_slot_get_img_click(slot))
      self._slot_widgets[-1].button_get_vid.clicked.connect(lambda _,slot=slot: self._process_slot_get_vid_click(slot))
      self._slot_widgets[-1].button_load.clicked.connect(lambda _,slot=slot: self._process_slot_load(slot))
      self._slot_widgets[-1].button_go.clicked.connect(lambda _,slot=slot: self._process_slot_go_click(slot))
      self._window.scroll_area_slots_contents.layout().addWidget(self._slot_widgets[-1])

    self._window.scroll_area_slots_contents.layout().addStretch()

    self._slot_manager.add_observer(self._update_enabledness)
    self._update_enabledness()

    #self._window.layout().setSizeConstraint(QtWidgets.QLayout.SetFixedSize);
    self._window.show()

    if self._grab_bbox is not None:
      self._screen_preview_timer.stop()
      self._screen_preview_timer.start(CONFIG['screenPreviewUpdateMillis'])

  def _set_screen_area(self, width=128, height=128, resizable=False, fixed_ratio=True):
    """ Launch screengrabber pygame window to select area of the screen. """
    # Do something.
    try:
      self._hide()
      try:
        self._grab_bbox = screengrab(width=width, height=height, is_resizable=resizable, fixed_ratio=fixed_ratio)
      except RuntimeError:
        pass # Don't update bbox if cancelling.
      self._update_enabledness()
      self._show()


      self._client_logic.update_client_data({"bbox": self._grab_bbox})
      # Ensure we can see a preview image.
      self._screen_preview_timer.stop()
      self._screen_preview_timer.start(CONFIG['screenPreviewUpdateMillis'])

    except:
      # If something fails, deal with it.
      self._show()
      self._grab_bbox = None
      self._screen_preview_timer.stop()
      # self._kill_update_preview_thread()

  def _update_enabledness(self):
    self._window.button_go_live_snapshot.setEnabled(self._grab_bbox is not None)
    self._window.button_go_live_stream.setEnabled(self._grab_bbox is not None)
    for slot in range(CONFIG['numSlots']):
      have_slot = self._slot_manager.have_slot(slot)
      self._slot_widgets[slot].button_clear.setEnabled(have_slot)
      self._slot_widgets[slot].button_get_img.setEnabled(self._grab_bbox is not None)
      self._slot_widgets[slot].button_get_vid.setEnabled(self._grab_bbox is not None)
      self._slot_widgets[slot].button_go.setEnabled(have_slot)
    # self._window.button_take_video.setEnabled(False)
    # self._window.button_live.setEnabled(self._grab_bbox is not None)
    pass

  def _button_go_live_snapshot_clicked(self):
    self._client_logic.process_go_live_screenshot()

  def _button_go_live_stream_clicked(self):
    self._client_logic.process_go_live_stream()

  def _button_go_round_robin_clicked(self):
    self._client_logic.process_go_round_robin()

  def _button_save_all_slots_clicked(self):
    filepath = QtWidgets.QFileDialog.getExistingDirectory(self, 'Open Save Directory', str(pathlib.Path.home()), options=QtWidgets.QFileDialog.Option.DontUseNativeDialog)
    if filepath == '':
      return
    self._slot_manager.save_all(filepath)

  def _button_load_all_slots_clicked(self):
    filepath = QtWidgets.QFileDialog.getExistingDirectory(self, 'Open Load Directory', str(pathlib.Path.home()), options=QtWidgets.QFileDialog.Option.DontUseNativeDialog)
    if filepath == '':
      return
    self._slot_manager.load_all(filepath)

  def _button_go_black_clicked(self):
    self._client_logic.process_go_black()

  def _process_slot_clear_click(self, slot):
    self._client_logic.process_set_slot_img(slot, None)

  def _process_slot_get_img_click(self, slot):
    assert self._preview_img is not None
    self._client_logic.process_set_slot_img(slot, self._preview_img)

  def _process_slot_go_click(self, slot):
    self._client_logic.process_go_slot(slot)

  def _process_slot_load(self, slot):
      filepath, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', filter="All valid types (*.jpg *.gif *.png);;Image/Video files (*.jpg *.gif *.png)", options=QtWidgets.QFileDialog.Option.DontUseNativeDialog)
      if filepath == '':
        return
      self._client_logic.process_slot_load(self._window, slot, filepath)

  def _process_slot_get_vid_click(self, slot):
    self._gif_grabber = gifgrabber.GIFGrabber(callback=lambda slot=slot:self._gif_grabber_done.emit(slot))
    self._gif_grabber_dialog = VidWaitDialog()
    self._gif_grabber_dialog.accepted.connect(self._gif_grabber.done)
    self._gif_grabber_dialog.rejected.connect(self._process_gif_grabber_cancel)
    self._gif_grabber_dialog.exec()

  def _process_gif_grabber_cancel(self):
    self._gif_grabber_dialog.hide()
    self._gif_grabber_dialog.destroy()
    self._gif_grabber_dialog = None
    self._gif_grabber.cancel()
    self._gif_grabber = None

  def _process_gif_grabber_done(self, slot):
    print("GIF DONE!")
    imgs = self._gif_grabber.imgs()
    durs = self._gif_grabber.durations()
    self._client_logic.process_set_slot_vid(slot, imgs, durs)

    self._gif_grabber_dialog.hide()
    self._gif_grabber_dialog.destroy()
    self._gif_grabber_dialog = None
    self._gif_grabber = None

  def _update_screen_preview(self):
    # Take an image.
    assert self._grab_bbox is not None
    new_preview_img = ImageGrab.grab(bbox=self._grab_bbox)
    self._preview_img = self._client_logic.process_image(self._window, new_preview_img)

    # Call handler.
    self._client_logic.process_screen_image(self._preview_img)
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
  import clientapi
  import clientlogic
  import slotmanager
  app = QtWidgets.QApplication(sys.argv)
  client_api = clientapi.ClientAPI()
  slot_manager = slotmanager.HTTPBackedSlotManager(client_api)
  client_logic = clientlogic.ClientLogic(client_api, slot_manager)
  client_app = ClientApp(client_logic, slot_manager)
  app.exec()

def sim(width=128, height=128):
  import clientlogic
  import deviceapi
  import displaymanager
  from matrix import PygameDriver
  import slotmanager

  import pygame

  app = QtWidgets.QApplication(sys.argv)
  pygame_driver = PygameDriver()
  backend_slot_manager = slotmanager.MemoryBackedSlotManager()
  display_manager = displaymanager.DisplayManager(pygame_driver, backend_slot_manager)
  device_api = deviceapi.DeviceAPI(display_manager, backend_slot_manager)
  frontend_slot_manager = slotmanager.HTTPBackedSlotManager(device_api)
  client_logic = clientlogic.ClientLogic(device_api, frontend_slot_manager)
  client_app = ClientApp(client_logic, frontend_slot_manager)
  pg_update_timer = QtCore.QTimer()

  def pygame_update():
    try:
        pygame.display.flip()
    except pygame.error:
       pygame.display.set_mode((256,256))
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        pygame.quit()
        app.quit()
        break
  
  def _set_screen_area(width=128, height=128, resizable=False, fixed_ratio=True):
    pygame.quit()
    pygame.init()
    pg_update_timer.stop()
    ClientApp._set_screen_area(client_app, width, height, resizable, fixed_ratio=False)
    pg_update_timer.start(30)
    pygame.quit()
    pygame.init()
    pygame_driver.game = pygame.display.set_mode((256,256))

  client_app._set_screen_area = _set_screen_area

  pg_update_timer.timeout.connect(pygame_update)
  pg_update_timer.start(30)
  app.exec()
  pg_update_timer.stop()
  pygame.quit()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--simulate", action="store_true",
                        help="Simulate the matrix with pygame")
    args = parser.parse_args()
    if args.simulate:
        sim()
    else:
       main()
