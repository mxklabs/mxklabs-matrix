from enum import Enum

from PIL import Image

import rest
import devicegui
import io

class DeviceAPI:

  class Mode(Enum):
    OFF         = 0
    ROUND_ROBIN = 1
    SHOW_SLOT   = 2
    LIVE        = 3

  def __init__(self, device_gui: devicegui.DeviceGUI | None=None):
    self._device_gui = device_gui

  @rest.endpoint(rest.RequestType.POST, '/slot')
  def set_slot(self, slot_index : int, gif_data : bytes | None) -> bool:

    if gif_data is None:
        raise RuntimeError(f"TODO: Deal with None data in set_slow")
    else:
        fp = io.BytesIO(gif_data)
        with Image.open(fp) as im:
            if im.n_frames < 1 or im.n_frames > 1:
              raise RuntimeError(f"TODO: Deal with .gif that has {im.n_frames} frames")

            im.seek(0)  # skip to the second frame

            self._device_gui.set_preview(im)

    print(f"SETTING TO SLOT {gif_data}")
    return True

  @rest.endpoint(rest.RequestType.GET, '/slot')
  def get_slot(self, slot_index : int) -> bytes | None:
    return 246467

  @rest.endpoint(rest.RequestType.POST, '/mode')
  def set_mode(self, mode : Mode, slot : int | None) -> bool:
    pass

  @rest.endpoint(rest.RequestType.POST, '/live')
  def set_live(self, gif_data : bytes) -> bool:
    pass
