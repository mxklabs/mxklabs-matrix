import json
import os
import pathlib
import shutil

from enum import IntEnum
from typing import Callable, Tuple

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from clientapi import ClientAPI

with open(pathlib.Path(__file__).parents[0] / "config.json", "r") as f:
    CONFIG = json.load(f)


class SlotType(IntEnum):
  NULL        = 0
  IMG         = 1
  VID         = 2


class SlotManager:

  def __init__(self, slot_setter : Callable, slot_getter : Callable):
    """ Initialise slot manager. """
    self._slots = [None] * CONFIG['numSlots']
    self._slot_setter = slot_setter
    self._slot_getter = slot_getter

  def have_slot(self, slot : int) -> bool:
    """ Return true if slot is set. """
    return self.get_slot(slot) is not None

  def set_slot(self, slot : int, slot_type : SlotType, data : bytes | None) -> bool:
    """ Set a slot (or fail). """
    res = self._slot_setter(slot, slot_type, data)
    if res:
      if data is None:
        self._slots[slot] = None
      else:
        self._slots[slot] = (slot_type, bytes)
    return res

  def get_slot(self, slot : int) -> Tuple[SlotType, bytes] | None:
    """ Get a slot (or fail). """
    if self._slots[slot] is not None:
        return self._slots[slot]
    else:
        res = self._slot_getter(slot)
        self._slots[slot] = res
        return res
    return


class HTTPBackedSlotManager(SlotManager):
    """ Slot manager (used on client) that backs up slot storage by HTTP
        calls to server. """

    def __init__(self, client_api : 'ClientAPI'):
        self._client_api = client_api
        SlotManager.__init__(
            self,
            slot_setter=self._client_api.set_slot,
            slot_getter=self._client_api.get_slot)


class FileBackedSlotManager(SlotManager):
    """ Slot manager (used on device) that backs up slot storage by
        storing/loading files on disk. """

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
        # TODO: Should check if the data matches the extension.
        try:
            # Delete what is there.
            possible_filenames = [ (slot_type, self.SLOT_DATA_DIR / f'{slot}.{ext}') for slot_type, ext in FileBackedSlotManager.EXT_MAP.items()]
            for _, filename in possible_filenames:
                if filename.exists():
                    filename.unlink()

            if data is None:
                # It was a deletion.
                return True
            else:
                # Writing file.
                ext = FileBackedSlotManager.EXT_MAP[slot_type]
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
