from enum import IntEnum

from PIL import Image

import io
import sys
import threading

from clientapi import Mode
from displaymanager import DisplayManager
class DeviceAPI:
  def __init__(self, matrix_driver):
    #self._device_gui = device_gui
    self.matrix_driver = matrix_driver
    self.display_manager = DisplayManager(matrix_driver)
    self.display_manager_thread = threading.Thread(target=self.display_manager.run)
    self.display_manager_thread.start()

  def set_slot(self, slot_index : int, gif_data : bytes | None) -> bool:
    self.display_manager.set_slot(slot_index, gif_data)
    return True

  def get_slot(self, slot_index : int) -> bytes | None:
    pass

  def set_mode(self, mode : Mode, slot : int | None) -> bool:
    pass

  def set_live(self, gif_data : bytes) -> bool:
    pass
  
  def ping(self, data : int) -> int:
    return -data
