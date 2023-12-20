"""Server application that drives the LED matrix.
"""

import rest
import deviceapi

class Device(deviceapi.DeviceAPI, rest.ServerAPI):
  pass

if __name__ == "__main__":
  device = Device()
  device.run()
