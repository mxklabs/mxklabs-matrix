"""Server application that drives the LED matrix.
"""

import rest
import deviceapi
import devicegui
import threading

if __name__ == "__main__":

  gui = devicegui.DeviceGUI()
  device_api = rest.server_api(deviceapi.DeviceAPI(gui))
  device_api_thread = threading.Thread(target=device_api.app.run)
  device_api_thread.start()

  gui.exec()

  device_api_thread.join()
