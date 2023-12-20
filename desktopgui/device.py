"""Server application that drives the LED matrix.
"""
import json
import pathlib
import threading

import rest
import deviceapi
import devicegui

with open(pathlib.Path(__file__).parents[0] / "config.json", "r") as f:
    CONFIG = json.load(f)

if __name__ == "__main__":

  gui = devicegui.DeviceGUI()
  device_api = rest.server_api(deviceapi.DeviceAPI(gui))
  device_api_thread = threading.Thread(target=device_api.app.run, kwargs={
     "host": CONFIG['listenIP4Addr'],
     "port": CONFIG['port']
  })
  device_api_thread.start()

  gui.exec()

  device_api_thread.join()
