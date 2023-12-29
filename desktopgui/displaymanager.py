import io
import json
import pathlib
import time
import threading

from enum import IntEnum
from typing import TYPE_CHECKING, Union

from PIL import Image

if TYPE_CHECKING:
    from clientapi import Mode

    from matrixdriver import MatrixDriver
    from matrix import PygameDriver

from slotmanager import SlotManager
from slots import SlotType, Slot
from statemanager import StateHandler, StateManager

with open(pathlib.Path(__file__).parents[0] / "config.json", "r") as f:
    CONFIG = json.load(f)

class DisplayManager(StateHandler):
    """ Object responsible for deciding what to display on the matrix. """
    def __init__(self, driver : Union['MatrixDriver', 'PygameDriver'], slot_manager : 'SlotManager', state_manager: StateManager):
        self._driver = driver
        self._slot_manager = slot_manager
        self._state_manager = state_manager
        self._thread = None
        self._thread_kill_event = threading.Event()

    def go_black(self) -> None:
        """ Set a black image. """
        if self._thread is not None:
            self._kill_thread()
        self._driver.set_image(Image.new("RGB", (CONFIG['matrixWidth'], CONFIG['matrixHeight']), (0,0,0)))

    def go_live(self) -> None:
        """ Go live (start with a white image). """
        if self._thread is not None:
            self._kill_thread()
        self._driver.set_image(Image.new("RGB", (CONFIG['matrixWidth'], CONFIG['matrixHeight']), (255,255,255)))

    def go_slot(self, slot : int) -> None:
        """ Process when the user wants to show a specific slot. """
        if self._thread is not None:
            self._kill_thread()

        res = self._slot_manager.get_slot(slot)
        if res is None or res[0] == SlotType.NULL:
            raise RuntimeError(f"Unable to get slot {slot}")

        slot_type, slot_data = res

        slot = Slot.from_bytes(slot_type, slot_data)

        self._thread_kill_event.clear()
        self._thread = threading.Thread(target=slot.run_slot, args=(self._driver, self._thread_kill_event))
        self._thread.start()

    def go_round_robin(self) -> None:
        """ Do the slots in a round robin fashion. """
        if self._thread is not None:
            self._kill_thread()

        # Start a round robin thread.
        self._thread_kill_event.clear()
        self._thread = threading.Thread(target=self._run_round_robin, args=(self._thread_kill_event,))
        self._thread.start()

    def process_live_img(self, img : Image.Image):
        """ Set a live image. """
        if self._state_manager.is_live():
            self._driver.set_image(img)

    def _kill_thread(self):
      """ Kill the internal thread. """
      self._thread_kill_event.set()
      self._thread.join()
      self._thread = None

    # def _run_single_slot_img(self, img : Image.Image, kill_event : threading.Event, minimum_time: float | None=None):
    #     """ Show static image in a single slot. Designed to run as a part
    #         of a thread.  """
    #     start_time = time.perf_counter()

    #     # Set the image at the start.
    #     self._driver.set_image(img)

    #     while not kill_event.is_set():
    #         now = time.perf_counter()
    #         if (now - start_time) < minimum_time:
    #             time.sleep(0.01)
    #             continue
    #         else:
    #             break

    # def _run_single_slot_vid(self, img : Image.Image, kill_event : threading.Event, loop : bool=True, minimum_time: float | None=None):
    #     """ Show animation in a single slot. Designed to run as part of a thread.
    #         If loop==False then loop at least for the minimum time and then 
    #         stop. Else loop indefinitely.  """
    #     frame = 0
    #     start_time = time.perf_counter()

    #     while not kill_event.is_set():
    #         try:
    #             img.seek(frame)
    #             self._driver.set_image(img.convert('RGB'))
    #             frame += 1

    #             # Sleep for the frame duration.
    #             time.sleep(img.info['duration'] / 1000.0)

    #         except EOFError:
    #             now = time.perf_counter()
    #             if loop or (now - start_time) < minimum_time:
    #                 frame = 0
    #                 continue
    #             else:
    #                 break

    def _run_round_robin(self, kill_event : threading.Event):
        """ Show animation in a single slot. """

        slot_type = None
        slot_data = None
        slot = 0

        while not kill_event.is_set():

            # Find next slot with data.
            for _ in range(CONFIG['numSlots']):
                res = self._slot_manager.get_slot(slot)
                if res is not None:
                    slot_type, slot_data = res
                    if slot_type == SlotType.NULL:
                        break
                    slot_instance = Slot.from_bytes(slot_type, slot_data)
                    slot_instance.run_slot(self._driver, kill_event, minimum_time=CONFIG['minimumSlotTime'])

                    slot = (slot + 1) % CONFIG['numSlots']
                    break
                else:
                    slot = (slot + 1) % CONFIG['numSlots']

            time.sleep(0.01)