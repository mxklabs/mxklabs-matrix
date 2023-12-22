"""Server application that drives the LED matrix.
"""
import json
import pathlib
import threading

import deviceapi
import devicegui
import server
import sys

with open(pathlib.Path(__file__).parents[0] / "config.json", "r") as f:
    CONFIG = json.load(f)

if __name__ == "__main__":

  gui = devicegui.DeviceGUI()
  device_api = deviceapi.DeviceAPI(gui)
  matrix_server = server.matrix_server(device_api)
  server_thread = threading.Thread(target=matrix_server, kwargs={
     "host": CONFIG['listenIP4Addr'],
     "port": CONFIG['port'],
     "debug": False
  })
  server_thread.start()

  gui.exec()

  server_thread.join()
