import io
import json
import os
import pathlib
import shutil
import sys
from enum import IntEnum

from PIL import Image

class Mode(IntEnum):
    OFF         = 0
    ROUND_ROBIN = 1
    SHOW_SLOT   = 2
    LIVE        = 3

with open(pathlib.Path(__file__).parents[0] / "config.json", "r") as f:
    CONFIG = json.load(f)
    SLOT_DATA_DIR = pathlib.Path(CONFIG['slotDataDir'])
    SLOT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    shutil.chown(SLOT_DATA_DIR, user=CONFIG['user'], group=CONFIG['group'])
    os.chmod(SLOT_DATA_DIR, 0o777)

class DeviceAPI:
  def __init__(self, matrix_driver):
    #self._device_gui = device_gui
    self.matrix_driver = matrix_driver

  def clear_slot(self, slot_index : int) -> bool:
    filename = SLOT_DATA_DIR / f'{slot_index}.gif'
    try:
      filename.unlink()
      return True
    except:
      return False

  def set_slot(self, slot_index : int, gif_data : bytes | None) -> bool:
    filename = SLOT_DATA_DIR / f'{slot_index}.gif'
    if gif_data is None:
      # Clear it if it exists.
      print(f"Removing {filename} [set_slot({slot_index}, None)]")
      raise RuntimeError(f"TODO: Deal with None data in set_slow")
    else:
      # Write it to a file.
      print(f"Writing new data to {filename} [set_slot({slot_index}, <bytes>)]")
      with open(filename, 'wb') as f:
          f.write(gif_data)
    return True

  def get_slot(self, slot_index : int) -> bytes | None:
    try:
      filename = SLOT_DATA_DIR / f'{slot_index}.gif'
      with open(filename, 'rb') as f:
        return True, f.read()
    except:
      return False, None

  def set_mode(self, mode : Mode, slot : int | None) -> bool:
    pass

  def set_live(self, gif_data : bytes) -> bool:
    if gif_data is None:
        raise RuntimeError(f"TODO: Deal with None data in set_live")
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

            im.seek(0)  # skip to the first frame

            # self._device_gui.set_preview(im)
            self.matrix_driver.set_image(im.convert('RGB'))
    return True
  
  def ping(self, data : int) -> int:
    return -data
