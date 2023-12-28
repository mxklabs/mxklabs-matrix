import json
import os
import pathlib
import shutil

from enum import IntEnum
from typing import Callable, Tuple

with open(pathlib.Path(__file__).parents[0] / "config.json", "r") as f:
    CONFIG = json.load(f)

class SlotType(IntEnum):
  IMG         = 0
  VID         = 1


class SlotManager:

  def __init__(self, slot_setter : Callable, slot_getter : Callable):
    """ Initialise slot manager. """
    self._have_slots = [False] * CONFIG['numSlots']
    self._slot_setter = slot_setter
    self._get_setter = slot_getter

  def have_slot(self, slot : int) -> bool:
    """ Return true if slot is set. """
    return self._have_slots[slot]

  def set_slot(self, slot : int, slot_type : SlotType, data : bytes | None) -> bool:
    """ Set a slot (or fail). """
    res = self._slot_setter(slot, slot_type, data)
    if res:
      self._have_slots[slot] = bytes is not None
    return res

  def get_slot(self, slot : int) -> Tuple[SlotType, bytes] | None:
    """ Get a slot (or fail). """
    return self._get_setter(slot)


class FileBackedSlotManager(SlotManager):

    EXT_MAP = { SlotType.IMG : 'png', SlotType.VID : 'gif'}

    def __init__(self):
        SlotManager.__init__(
            self,
            slot_setter=self._file_backed_set_slot,
            slot_getter=self._file_backed_get_slot)
        self.SLOT_DATA_DIR = pathlib.Path(CONFIG['slotDataDir'])
        self.SLOT_DATA_DIR.mkdir(parents=True, exist_ok=True)
        shutil.chown(self.SLOT_DATA_DIR, user=CONFIG['user'], group=CONFIG['group'])
        os.chmod(self.SLOT_DATA_DIR, 0o777)


        self.SLOT_DATA_DIR = pathlib.Path(CONFIG['slotDataDir'])
        self.SLOT_DATA_DIR.mkdir(parents=True, exist_ok=True)
        shutil.chown(self.SLOT_DATA_DIR, user=CONFIG['user'], group=CONFIG['group'])
        os.chmod(self.SLOT_DATA_DIR, 0o777)


    def _file_backed_set_slot(self, slot : int, slot_type : SlotType, data : bytes | None) -> bool:
        """ Write a file to disk. """
        print(f"Writing slot {slot} of type {slot_type} ({type(slot_type)})")
        # TODO: Should check if the data matches the extension.
        try:
            # Delete what is there.
            possible_filenames = [ (slot_type, self.SLOT_DATA_DIR / f'{slot}.{ext}') for slot_type, ext in FileBackedSlotManager.EXT_MAP.items()]
            for _, filename in possible_filenames:
                if filename.exists():
                    filename.unlink()

            # Add new file if we have data.
            if data is not None:
                print(f"BEFORE {slot_type} ({type(slot_type)})")
                ext = FileBackedSlotManager.EXT_MAP[slot_type]
                print(f"EXT {ext} ({FileBackedSlotManager.EXT_MAP})")
                filename = self.SLOT_DATA_DIR / f'{slot}.{ext}'
                with open(filename, 'wb') as f:
                    f.write(data)
                    return True
        except:
            return False

    def _file_backed_get_slot(self, slot : int) -> Tuple[SlotType, bytes] | None:
        """ Work out what file we have. """
        try:
            possible_filenames = [ (slot_type, self.SLOT_DATA_DIR / f'{slot}.{ext}') for slot_type, ext in FileBackedSlotManager.EXT_MAP.items()]
            for slot_type, filename in possible_filenames:
                if filename.exists():
                    with open(filename, 'rb') as f:
                        return slot_type, f.read()
        except:
            return None
        return None
