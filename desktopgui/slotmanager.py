import json
import os
import pathlib
import shutil

from enum import IntEnum
from typing import Callable, Tuple
from os import PathLike

from observable import Observable

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from clientapi import ClientAPI


with open(pathlib.Path(__file__).parents[0] / "config.json", "r") as f:
    CONFIG = json.load(f)


class SlotType(IntEnum):
  NULL        = 0
  IMG         = 1
  VID         = 2


class SlotManager(Observable):

    def __init__(self, slot_setter : Callable, slot_getter : Callable):
        """ Initialise slot manager. """
        """
            For _slots,
            * None means we haven't checked yet.
            * (SlotType, bytes) for SlotType == NULL and bytes=None means the slot is empty. 
            * (SlotType, bytes) for SlotType != NULL means we have checked and it's that. 
        """
        Observable.__init__(self)
        self._slots = [None] * CONFIG['numSlots']
        self._slot_setter = slot_setter
        self._slot_getter = slot_getter

    def have_slot(self, slot : int) -> bool:
        """ Return true if slot is set. """
        return self.get_slot(slot) is not None

    def set_slot(self, slot : int, slot_type : SlotType, data : bytes | None) -> bool:
        """ Set a slot (or fail). """
        if data is None:
            print(f"Clearing slot {slot}...", flush=True)
        else:
            print(f"Setting slot {slot} to {slot_type}...", flush=True)
        res = self._slot_setter(slot, slot_type, data)
        if res:
            if data is None:
                self._slots[slot] = (SlotType.NULL, None)
            else:
                self._slots[slot] = (slot_type, data)
            self._notify_observers()
        return res

    def get_slot(self, slot : int) -> Tuple[SlotType, bytes] | None:
        """ Get a slot (or fail). """
        if self._slots[slot] is not None:
            # We have a cached value.
            if self._slots[slot][0] != SlotType.NULL:
                return self._slots[slot]
            else:
                return None
        else:
            # We don't have a cached value.
            res = self._slot_getter(slot)
            if res is None:
                self._slots[slot] = (SlotType.NULL, None)
            else:
                self._slots[slot] = res
            return res

    def save_all(self, dir_path : PathLike):
        """ Save all slots to a directory. """
        for slot in range(CONFIG['numSlots']):
            png_filename = os.path.join(dir_path, f'{slot}.png')
            if png_filename.exists():
                png_filename.unlink()
            if gif_filename.exists():
                png_filename.unlink()
            gif_filename = os.path.join(dir_path, f'{slot}.gif')
            res = self.get_slot(slot)
            if res is not None:
                slot_type, data = res
                if slot_type == SlotType.IMG:
                    ext = 'png'
                elif slot_type == SlotType.VID:
                    ext = 'gif'
                else:
                    raise RuntimeError(f"Unknown slot type {slot_type}")
                filename = os.path.join(dir_path, f'{slot}.{ext}')
                with open(filename, 'wb') as f:
                    f.write(data)

    def load_all(self, dir_path : PathLike):
        """ Load slots from a directory. """
        for slot in range(CONFIG['numSlots']):
            png_filename = os.path.join(dir_path, f'{slot}.png')
            gif_filename = os.path.join(dir_path, f'{slot}.gif')
            if os.path.exists(png_filename):
                # It's a .png!
                slot_type = SlotType.IMG
                with open(png_filename, 'rb') as f:
                    slot_data = f.read()
                self.set_slot(slot, slot_type, slot_data)
            elif os.path.exists(gif_filename):
                # It's a .gif!
                slot_type = SlotType.VID
                with open(gif_filename, 'rb') as f:
                    slot_data = f.read()
                self.set_slot(slot, slot_type, slot_data)
            else:
                # Nothing to see here!
                self.set_slot(slot, SlotType.NULL, None)

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
