"""Server application that drives the LED matrix.
"""

import rest
import deviceapi

if __name__ == "__main__":
  device = rest.server_api(deviceapi.DeviceAPI())
  device.app.run()
