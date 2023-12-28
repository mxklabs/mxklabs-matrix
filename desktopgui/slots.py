from enum import IntEnum
import io
import threading
from typing import Union, TYPE_CHECKING
import time

from PIL import Image

if TYPE_CHECKING:
    from matrixdriver import MatrixDriver
    from matrix import PygameDriver

class SlotType(IntEnum):
    NULL        = 0
    IMG         = 1
    VID         = 2
    TXT         = 3

class Slot:
    EXT_TO_SLOT_TYPE = {"png": SlotType.IMG, "gif": SlotType.VID}

    def run_slot(self, driver : Union['MatrixDriver', 'PygameDriver'], kill_event : threading.Event, minimum_time: float | None=None):
        raise NotImplementedError()
    
    def ext(self) -> str:
        raise NotImplementedError()
    
    @staticmethod
    def from_bytes(slot_type: SlotType, data: bytes) -> 'Slot':
        match slot_type:
            case SlotType.IMG:
                return ImageSlot(data)
            case SlotType.VID:
                return VideoSlot(data)
            case _:
                raise NotImplementedError()


class ImageSlot(Slot):
    def __init__(self, data: bytes):
        self._data = data
        self._img = None
    
    def _ensure_img_available(self):
        if self._img is None:
            self._img = Image.open(io.BytesIO(self._data))

    def run_slot(self, driver : Union['MatrixDriver', 'PygameDriver'], kill_event : threading.Event, minimum_time: float | None=None):
        """ Show static image in a single slot. Designed to run as a part
            of a thread.  """
        self._ensure_img_available()

        start_time = time.perf_counter()

        # Set the image at the start.
        driver.set_image(self._img)

        while not kill_event.is_set():
            now = time.perf_counter()
            if minimum_time is None or (now - start_time) < minimum_time:
                time.sleep(0.01)
                continue
            else:
                break
    
    def ext(self) -> str:
        return "png"


class VideoSlot(Slot):
    def __init__(self, data: bytes):
        self._data = data
        self._imgs = None
    
    def _ensure_imgs_available(self):
        if self._imgs is None:
            self._imgs = Image.open(io.BytesIO(self._data))

    def run_slot(self, driver : Union['MatrixDriver', 'PygameDriver'], kill_event : threading.Event, minimum_time: float | None=None):
        """ Show animation in a single slot. Designed to run as part of a thread.
        """
        self._ensure_imgs_available()
        frame = 0
        start_time = time.perf_counter()

        while not kill_event.is_set():
            try:
                self._imgs.seek(frame)
                driver.set_image(self._imgs.convert('RGB'))
                frame += 1

                # Sleep for the frame duration.
                time.sleep(self._imgs.info.get("duration", 1000/15) / 1000.0)

            except EOFError:
                now = time.perf_counter()
                if minimum_time is None or (now - start_time) < minimum_time:
                    frame = 0
                    continue
                else:
                    break
    
    def ext(self) -> str:
        return "gif"