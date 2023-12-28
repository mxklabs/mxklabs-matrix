from enum import IntEnum
from typing import Tuple

class SlotType(IntEnum):
  IMG         = 0
  VID         = 1

class SlotObserver:

  def __init__(self):
    ...

  def slot_changed(self, slot : int):
    ...

class SlotSetter:

  def __init__(self):
    ...

  def set_slot(self, slot : int, slot_type : SlotType, data : bytes) -> bool:
    ...

class SlotGetter:

  def __init__(self):
    ...

  def get_slot(self, slot : int) -> Tuple[SlotType, bytes]:
    ...

class SlotManager:

  def __init__(self, slot_setter : SlotSetter, slot_getter : SlotGetter):
    ...

  def have_slot(self, slot : int) -> bool:
    ...

  def set_slot(self, slot : int, slot_type : SlotType, data : bytes) -> bool:
    ...

  def get_slot(self, slot : int) -> Tuple[SlotType, bytes] | None:
    ...

  def add_observer(self, slot_observer: SlotObserver):
    ...

  def remove_observer(self, slot_observer: SlotObserver):
    ...