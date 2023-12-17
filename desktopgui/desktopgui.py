import sys
from PyQt6 import QtWidgets, uic

def launch_screen_grabber(width=None, height=None, resizable=None):
  print(f"button {width}, {height}, {resizable}")

def main(width=128, height=128):
  app = QtWidgets.QApplication(sys.argv)
  window = uic.loadUi("desktopgui.ui")

  window.push_button_1_1.clicked.connect(lambda : launch_screen_grabber(width=128, height=128))
  window.push_button_1_2.clicked.connect(lambda : launch_screen_grabber(width=256, height=256))
  window.push_button_1_3.clicked.connect(lambda : launch_screen_grabber(width=384, height=384))
  window.push_button_1_4.clicked.connect(lambda : launch_screen_grabber(width=512, height=512))
  window.push_button_1_5.clicked.connect(lambda : launch_screen_grabber(width=640, height=640))
  window.push_button_1_6.clicked.connect(lambda : launch_screen_grabber(width=768, height=768))
  window.push_button_1_7.clicked.connect(lambda : launch_screen_grabber(width=896, height=896))
  window.push_button_1_8.clicked.connect(lambda : launch_screen_grabber(width=1024, height=1024))
  window.push_button_arbitrary.clicked.connect(lambda : launch_screen_grabber(resizable=True))

  window.show()

  app.exec()

if __name__ == "__main__":
  main()