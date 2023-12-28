import json
import os
import pathlib
import shutil

from enum import IntEnum
from typing import Callable, Tuple

with open(pathlib.Path(__file__).parents[0] / "config.json", "r") as f:
    CONFIG = json.load(f)
    SLOT_DATA_DIR = pathlib.Path(CONFIG['slotDataDir'])
    SLOT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    shutil.chown(SLOT_DATA_DIR, user=CONFIG['user'], group=CONFIG['group'])
    os.chmod(SLOT_DATA_DIR, 0o777)

class SlotType(IntEnum):
  IMG         = 0
  VID         = 1

# class SlotObserver:

#   def __init__(self):
#     ...

#   def slot_changed(self, slot : int):
#     ...

class SlotManager:

  def __init__(self, slot_setter : Callable, slot_getter : Callable):
    self._have_slots = [False] * CONFIG['numSlots']
    self._slot_setter = slot_setter
    self._get_setter = slot_getter

  def have_slot(self, slot : int) -> bool:
    return self._have_slots[slot]

  def set_slot(self, slot : int, slot_type : SlotType, data : bytes | None) -> bool:
    return self._slot_setter(slot, slot_type, data)

  def get_slot(self, slot : int) -> Tuple[SlotType, bytes] | None:
    return self._get_setter(slot)

  # def add_observer(self, slot_observer: SlotObserver):
  #   ...

  # def remove_observer(self, slot_observer: SlotObserver):
  #   ...

class FileBackedSlotManager(SlotManager):

    EXT_MAP = { SlotType.IMG : 'png', SlotType.VID : 'gif'}

    def __init__(self):
        SlotManager.__init__(
            self,
            slot_setter=self._file_backed_set_slot,
            slot_getter=self._file_backed_get_slot)

    def _file_backed_set_slot(self, slot : int, slot_type : SlotType, data : bytes | None) -> bool:
        """ Write a file to disk. """
        # TODO: Should check if the data matches the extension.
        try:
            # Delete what is there.
            possible_filenames = [ (slot_type, SLOT_DATA_DIR / f'{slot}.{ext}') for slot_type, ext in FileBackedSlotManager.EXT_MAP.items()]
            for slot_type, filename in possible_filenames:
                if filename.exists():
                    filename.unlink()

            # Add new file if we have data.
            if data is not None:
                ext = FileBackedSlotManager.EXT_MAP[slot_type]
                filename = SLOT_DATA_DIR / f'{slot}.{ext}'
                with open(filename, 'wb') as f:
                    f.write(data)
                    return True
        except:
            return False

    def _file_backed_get_slot(self, slot : int) -> Tuple[SlotType, bytes] | None:
        """ Work out what file we have. """
        try:
            possible_filenames = [ (slot_type, SLOT_DATA_DIR / f'{slot}.{ext}') for slot_type, ext in FileBackedSlotManager.EXT_MAP.items()]
            for slot_type, filename in possible_filenames:
                if filename.exists():
                    with open(filename, 'rb') as f:
                        return slot_type, f.read()
        except:
            return None
        return None
