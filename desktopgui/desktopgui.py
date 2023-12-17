import pathlib
import sys
import time

from screengrab import main as screengrab

from PyQt6 import QtCore, QtWidgets, uic


def launch_screen_grabber(app, width=128, height=128, resizable=False):
  #screengrab_file = pathlib.Path(__file__).parents[1] / 'screengrab' / 'screengrab.py'
  # cmd = [sys.executable, screengrab_file]
  # if width is not None:
  #   cmd += ['--width', f'{width}']
  # if height is not None:
  #   cmd += ['--height', f'{height}']
  # if resizable is not None:
  #   cmd += ['--resizable']
  app.hide()
  screengrab(width=width, height=height, is_resizable=resizable)
  app.show()
  # p = mp.Process(target=screengrab, args=(width, height, resizable))
  # p.start()
  #p.join()

  print(f"button {width}, {height}, {resizable}")


class DesktopApp:
  def __init__(self):
    self._app = QtWidgets.QApplication(sys.argv)
    self._window = uic.loadUi(pathlib.Path(__file__).parents[0] / "desktopgui.ui")

    self._window.push_button_1_1.clicked.connect(lambda : launch_screen_grabber(self, width=128, height=128))
    self._window.push_button_1_2.clicked.connect(lambda : launch_screen_grabber(self, width=256, height=256))
    self._window.push_button_1_3.clicked.connect(lambda : launch_screen_grabber(self, width=384, height=384))
    self._window.push_button_1_4.clicked.connect(lambda : launch_screen_grabber(self, width=512, height=512))
    self._window.push_button_1_5.clicked.connect(lambda : launch_screen_grabber(self, width=640, height=640))
    self._window.push_button_1_6.clicked.connect(lambda : launch_screen_grabber(self, width=768, height=768))
    self._window.push_button_1_7.clicked.connect(lambda : launch_screen_grabber(self, width=896, height=896))
    self._window.push_button_1_8.clicked.connect(lambda : launch_screen_grabber(self, width=1024, height=1024))
    self._window.push_button_arbitrary.clicked.connect(lambda : launch_screen_grabber(self, resizable=True))

    self._window.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
    self._window.show()

  def exec(self):
    self._app.exec()

  def hide(self):
    self._window.hide()

  def show(self):
    self._window.show()

def main(width=128, height=128):
  app = DesktopApp()
  app.exec()
  time.sleep(5)
  app.quit()
  time.sleep(5)

if __name__ == "__main__":
  main()
