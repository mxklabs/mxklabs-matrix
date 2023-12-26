from enum import IntEnum

from PIL import Image

import io
import sys

class Mode(IntEnum):
    OFF         = 0
    ROUND_ROBIN = 1
    SHOW_SLOT   = 2
    LIVE        = 3

class DeviceAPI:
  def __init__(self, matrix_driver):
    #self._device_gui = device_gui
    self.matrix_driver = matrix_driver

  def set_slot(self, slot_index : int, gif_data : bytes | None) -> bool:
    if gif_data is None:
        raise RuntimeError(f"TODO: Deal with None data in set_slow")
    else:
        Image._initialized = 0
        print(gif_data, flush=True)
        print(Image.__version__)
        print(type(gif_data), type(type(gif_data)), flush=True)
        fp = io.BytesIO(gif_data)
        fp.seek(0)
        with Image.open(fp) as im:#, formats=["GIF"]
            if im.n_frames < 1 or im.n_frames > 1:
              raise RuntimeError(f"TODO: Deal with .gif that has {im.n_frames} frames")
            im.seek(0)  # skip to the second frame

            # self._device_gui.set_preview(im)
            self.matrix_driver.set_image(im.convert('RGB'))
    return True

  def get_slot(self, slot_index : int) -> bytes | None:
    pass

  def set_mode(self, mode : Mode, slot : int | None) -> bool:
    pass

  def set_live(self, gif_data : bytes) -> bool:
    pass
  
  def ping(self, data : int) -> int:
    return -data
