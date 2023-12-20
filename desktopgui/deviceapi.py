from enum import Enum

import rest

class DeviceAPI:

  class Mode(Enum):
    OFF         = 0
    ROUND_ROBIN = 1
    SHOW_SLOT   = 2
    LIVE        = 3

  def __init__(self):
    pass

  @rest.endpoint(rest.RequestType.POST, '/slot')
  def set_slot(self, slot_index : int, gif_data : bytes | None) -> bool:
    print(gif_data)
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
