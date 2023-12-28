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
        if res is None or res[0] == SlotType.NULL:
            raise RuntimeError(f"Unable to get slot {slot}")

        slot_type, slot_data = res


        if slot_type == SlotType.IMG:
            # No thread required!
            img = Image.open(io.BytesIO(slot_data))
            self._driver.set_image(img)
        elif slot_type == SlotType.VID:
            # We need to worry about animation.
            img = Image.open(io.BytesIO(slot_data))
            self._thread_kill_event.clear()
            self._thread = threading.Thread(target=self._run_single_slot_vid, args=(img, self._thread_kill_event))
            self._thread.start()
        self._mode = DisplayManagerMode.SHOW_SLOT

    def process_go_round_robin(self):
        """ Do the slots in a round robin fashion. """
        if self._thread is not None:
            self._kill_thread()

        # Start a round robin thread.
        self._thread_kill_event.clear()
        self._thread = threading.Thread(target=self._run_round_robin, args=(self._thread_kill_event,))
        self._thread.start()
        self._mode = DisplayManagerMode.ROUND_ROBIN

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
      self._thread.join()
      self._thread = None

    def _run_single_slot_img(self, img : Image.Image, kill_event : threading.Event, minimumTime: float | None=None):
        """ Show static image in a single slot. Designed to run as a part
            of a thread.  """
        start_time = time.perf_counter()

        # Set the image at the start.
        self._driver.set_image(img)

        while not kill_event.is_set():
            now = time.perf_counter()
            if (now - start_time) < minimumTime:
                time.sleep(0.01)
                continue
            else:
                break

    def _run_single_slot_vid(self, img : Image.Image, kill_event : threading.Event, loop : bool=True, minimumTime: float | None=None):
        """ Show animation in a single slot. Designed to run as part of a thread.
            If loop==False then loop at least for the minimum time and then 
            stop. Else loop indefinitely.  """
        frame = 0
        start_time = time.perf_counter()

        while not kill_event.is_set():
            try:
                img.seek(frame)
                self._driver.set_image(img.convert('RGB'))
                frame += 1

                # Sleep for the frame duration.
                time.sleep(img.info['duration'] / 1000.0)

            except EOFError:
                now = time.perf_counter()
                if loop or (now - start_time) < minimumTime:
                    frame = 0
                    continue
                else:
                    break

    def _run_round_robin(self, kill_event : threading.Event):
        """ Show animation in a single slot. """

        img = None
        slot_type = None
        slot_data = None
        slot = 0
        frame = 0

        while not kill_event.is_set():

            # Find next slot with data.
            for _ in range(CONFIG['numSlots']):
                res = self._slot_manager.get_slot(slot)
                if res is not None:
                    slot_type, slot_data = res
                    if slot_type == SlotType.NULL:
                        break
                    img = Image.open(io.BytesIO(slot_data))
                    if slot_type == SlotType.IMG:
                        self._run_single_slot_img(img, kill_event, minimumTime=CONFIG['minimumSlotTime'])
                    elif slot_type == SlotType.VID:
                        self._run_single_slot_vid(img, kill_event, loop=False, minimumTime=CONFIG['minimumSlotTime'])
                    slot = (slot + 1) % CONFIG['numSlots']
                    break
                else:
                    slot = (slot + 1) % CONFIG['numSlots']

            time.sleep(0.01)