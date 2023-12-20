"""Desktop application for managing the LED matrix.
"""

import collections
import json
import pathlib
import sys

from PIL import ImageGrab, ImageQt, Image
from PySide6 import QtCore, QtGui, QtWidgets, QtUiTools

import utils

with open(pathlib.Path(__file__).parents[0] / "config.json", "r") as f:
    CONFIG = json.load(f)

class DeviceGUI(QtWidgets.QApplication):
    def __init__(self):
        self._app = QtWidgets.QApplication.__init__(self, sys.argv)
        ui_file = QtCore.QFile(pathlib.Path(__file__).parents[0] / "devicegui.ui")
        if not ui_file.open(QtCore.QIODevice.ReadOnly):
            print("Cannot open 'devicegui.ui'")
            sys.exit(-1)
        loader = QtUiTools.QUiLoader()
        self._window = loader.load(ui_file)

        # Not remembering these seems to cause bugs.
        self._qt_img = None
        self._qt_pix = None

        # Keep on top.
        self._window.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)

        # Resize the preview widget to the configured size.
        self._window.label_matrix_preview.setMinimumSize(
            CONFIG['matrixWidth'], CONFIG['matrixHeight'])
        self._window.label_matrix_preview.setMaximumSize(
            CONFIG['matrixWidth'], CONFIG['matrixHeight'])
        self._window.layout().activate()

        self._window.setFixedSize(self._window.size())
        self._window.show()

    def set_mode_string(self, mode : str) -> None:
        self._window.label_mode.setText(f'Mode: {mode}')

    def set_preview(self, img : Image) -> None:
        assert img.width != CONFIG['matrixWidth'] or img.height != CONFIG['matrixHeight'], \
          f"Expected size {CONFIG['matrixWidth']}x{CONFIG['matrixHeight']} but got {img.width}x{img.height}"

        self._qt_img = utils.pil_to_qimage(img)
        self._qt_pix = QtGui.QPixmap.fromImage(self._qt_img, QtCore.Qt.ImageConversionFlag.AutoColor)
        self._window.label_matrix_preview.setPixmap(self._qt_pix)

    def _hide(self):
        self._window.hide()

    def _show(self):
        self._window.show()

    def exec(self):
        QtWidgets.QApplication.exec()

# def main():
#     app = DeviceGUI()
#     app.exec()


# if __name__ == "__main__":
#     main()
