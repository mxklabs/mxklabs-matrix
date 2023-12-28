import io
import json
import os
import pathlib
import shutil
import sys
from enum import IntEnum

from typing import Tuple, TYPE_CHECKING

from PIL import Image
if TYPE_CHECKING:
    from displaymanager import DisplayManager
    from slotmanager import SlotManager, SlotType

class DeviceAPI:
    """ This interface exists because it's a useful abstraction for the purpose of
        simulating with a PyGame-based matrix driver. """
    def __init__(self, display_manager : 'DisplayManager', slot_manager : 'SlotManager'):
        #self._device_gui = device_gui
        # self.matrix_driver = matrix_driver
        self._display_manager = display_manager
        self._slot_manager = slot_manager

    def set_slot(self, slot : int, slot_type : 'SlotType', data : bytes | None) -> bool:
        return self._slot_manager.set_slot(slot, slot_type, data)

    def get_slot(self, slot_index : int) -> Tuple['SlotType', bytes] | None:
        return self._slot_manager.get_slot(slot_index)

    def go_slot(self, slot_index : int) -> None:
        self._display_manager.process_go_slot(slot_index)

    def go_round_robin(self) -> None:
        self._display_manager.process_go_round_robin()

    def go_black(self) -> None:
        self._display_manager.process_go_black()

    def set_live(self, data : bytes) -> bool:
        if data is None:
            raise RuntimeError(f"TODO: Deal with None data in set_live")
        else:
            Image._initialized = 0
            # print(gif_data, flush=True)
            # print(Image.__version__)
            # print(type(gif_data), type(type(gif_data)), flush=True)
            fp = io.BytesIO(data)
            fp.seek(0)
            with Image.open(fp) as im:#, formats=["GIF"]
                if im.n_frames < 1 or im.n_frames > 1:
                    raise RuntimeError(f"TODO: Deal with .gif that has {im.n_frames} frames")
                im.seek(0)
                self._display_manager.process_live_img(im.convert('RGB'))
        return True

    def ping(self, data : int) -> int:
        return -data
