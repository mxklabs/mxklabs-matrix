import io
import json
import pathlib
import time
import threading

from enum import IntEnum

from PIL import Image

from clientapi import Mode
# from slots import ImageSlot, GifSlot
from matrixdriver import MatrixDriver
from matrix import PygameDriver

from slotmanager import SlotManager, SlotType

with open(pathlib.Path(__file__).parents[0] / "config.json", "r") as f:
    CONFIG = json.load(f)

class DisplayManagerMode(IntEnum):
    """ Mode of display manager. """
    DARK         = 0
    SHOW_SLOT    = 1
    ROUND_ROBIN  = 2
    LIVE         = 3

class DisplayManager:
    """ Object responsible for deciding what to display on the matrix. """
    def __init__(self, driver : MatrixDriver | PygameDriver, slot_manager : SlotManager):
        self._driver = driver
        self._mode = DisplayManagerMode.DARK
        self._slot_manager = slot_manager

        self._thread = None
        self._thread_kill_event = threading.Event()

    def process_go_slot(self, slot : int):
        """ Process when the user wants to show a specific slot. """
        if self._thread is not None:
            self._kill_thread()

        res = self._slot_manager.get_slot(slot)
        if res is None:
            raise RuntimeError(f"Unable to get slot {slot}")

        slot_type, slot_data = res

        if slot_type == SlotType.IMG:
            # No thread required!
            img = Image.open(io.BytesIO(slot_data))
            self._driver.set_image(img)
        else:
            # We need to worry about animation.
            img = Image.open(io.BytesIO(slot_data))
            self._thread_kill_event.clear()
            self._thread = threading.Thread(target=self._run_single_slot, args=(img, self._thread_kill_event))
            print('created new thread')
            self._thread.start()
            print('started new thread')
        self._mode = DisplayManagerMode.SHOW_SLOT

    def process_go_round_robin(self):
        """ Do the slots in a round robin fashion. """
        raise RuntimeError("Not Implemented")

    def process_live_img(self, img : Image.Image):
        """ Set a live image. """
        if self._thread is not None:
            self._kill_thread()
        self._driver.set_image(img)
        self._mode = DisplayManagerMode.LIVE

    def process_go_black(self):
        """ Set a black image. """
        if self._thread is not None:
            self._kill_thread()
        self._driver.set_image(Image.new("RGB", (CONFIG['matrixWidth'], CONFIG['matrixHeight']), (0,0,0)))
        self._mode = DisplayManagerMode.DARK

    def _kill_thread(self):
      """ Kill the internal thread. """
      self._thread_kill_event.set()
      print(f'set _thread_kill_event')
      self._thread.join()
      print(f'joined thread')
      self._thread = None

    def _run_single_slot(self, img : Image.Image, kill_event : threading.Event):
        """ Show animation in a single slot. """
        frame = 0
        while not kill_event.is_set():
            try:
                img.seek(frame)
                self._driver.set_image(img.convert('RGB'))
                frame += 1

                # Sleep for the frame duration.
                time.sleep(img.info['duration'] / 1000.0)

            except EOFError:
                frame = 0
                continue