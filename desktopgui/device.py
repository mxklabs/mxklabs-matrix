"""Server application that drives the LED matrix.
"""

import rest
import deviceapi
import devicegui
import threading

if __name__ == "__main__":

  server = rest.server_api(deviceapi.DeviceAPI())

  gui = devicegui.DeviceGUI()
  server_thread = threading.Thread(target=server.app.run)
  server_thread.start()

  gui.exec()

  server_thread.join()
