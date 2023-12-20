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

  @rest.endpoint('/set_slot')
  def set_slot(self, slot_index : int, gif_data : bytes | None) -> bool:
    pass

  @rest.endpoint('/get_slot')
  def get_slot(self, slot_index : int) -> bytes | None:
    pass

  @rest.endpoint('/set_mode')
  def set_mode(self, mode : Mode, slot : int | None) -> bool:
    pass

  @rest.endpoint('/set_live')
  def set_live(self, gif_data : bytes) -> bool:
    pass
