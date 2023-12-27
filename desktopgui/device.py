"""Server application that drives the LED matrix.
"""
import json
import os
import pathlib
import sys
import threading

import deviceapi
import matrixdriver
import server

from PIL import Image

with open(pathlib.Path(__file__).parents[0] / "config.json", "r") as f:
    CONFIG = json.load(f)

if __name__ == "__main__":
  # Need to initialise Pillow here to avoid bug.
  Image.preinit()


  matrix_driver = matrixdriver.MatrixDriver()
  device_api = deviceapi.DeviceAPI(matrix_driver)
  matrix_server = server.matrix_server(device_api)
  server_thread = threading.Thread(target=matrix_server, kwargs={
     "host": CONFIG['listenIP4Addr'],
     "port": CONFIG['port'],
     "debug": False
  })

  server_thread.start()

  if CONFIG['flaskThreadCpuAffinity'] is not None:
    old_affinity = os.sched_getaffinity(server_thread.native_id)
    new_affinity = [CONFIG['flaskThreadCpuAffinity']]
    print(f'Changing flask thread ({server_thread.native_id}) affinity from {old_affinity} to {new_affinity}')
    os.sched_setaffinity(server_thread.native_id, new_affinity)



  #gui.exec()

  server_thread.join()
