from slots import SlotType, Slot

from enum import Enum
import io
import json
import os
import pathlib
import requests
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from PIL import Image, ImageChops, ImageFilter

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from clientapi import ClientAPI
    from slotmanager import SlotManager


with open(pathlib.Path(__file__).parents[0] / "config.json", "r") as f:
    CONFIG = json.load(f)
    MATRIX_WIDTH = CONFIG['matrixWidth']
    MATRIX_HEIGHT = CONFIG['matrixHeight']

class Mode(Enum):
   LIVE_SNAPSHOT = 0
   LIVE_STREAM = 1
   SLOT_SPECIFIC = 2
   SLOT_ROUND_ROBIN = 3
   DARK = 4



class ClientLogic:

    def __init__(self, client_api : 'ClientAPI', slot_manager : 'SlotManager'):

        """ Constructor for client logic class. """
        self._client_api = client_api
        self._slot_manager = slot_manager
        self._mode = Mode.DARK
        self._last_screen_img = None
        self._location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

    def process_screen_image(self, screen_img):
        """ Process a fresh image captured from the screen. """
        if self._mode == Mode.LIVE_STREAM:
            # Keep blasting if it's on stream mode.
            diff = ImageChops.difference(self._last_screen_img, screen_img)
            if diff.getbbox() is not None:
              self._send_live_img(screen_img)

        self._last_screen_img = screen_img

    def process_go_live_screenshot(self):
        """ We're going live with a snapshot. """
        if self._last_screen_img is not None:
            self._send_live_img(self._last_screen_img)
        self._mode = Mode.LIVE_SNAPSHOT

    def process_go_live_stream(self):
        """ We're going live with a stream."""
        if self._last_screen_img is not None:
            self._send_live_img(self._last_screen_img)
        self._mode = Mode.LIVE_STREAM

    def process_go_slot(self, slot : int):
        """ Display a specific slot. """
        self._client_api.go_slot(slot)
        self._mode = Mode.SLOT_SPECIFIC

    def process_go_round_robin(self):
        """ Display all slots in round-robin fashion. """
        self._client_api.go_round_robin()
        self._mode = Mode.SLOT_ROUND_ROBIN

    def process_go_black(self):
        """ Display nothing. """
        self._client_api.go_black()
        self._mode = Mode.DARK

    def process_set_slot_img(self, slot : int, img : Image.Image | None):
        """ Set a slot for an image. """
        if img is None:
            self._slot_manager.set_slot(slot, SlotType.NULL, None)
        else:
            buffer = io.BytesIO()
            img.save(buffer, format="png")
            self._slot_manager.set_slot(slot, SlotType.IMG, buffer.getvalue())

    def process_set_slot_vid(self, slot : int, imgs : [Image], durations : [int]):
        """ Set a slot for a video. """
        buffer = io.BytesIO()
        imgs[0].save(buffer, format="gif", save_all=True, append_images=imgs[1:], duration=durations, loop=0)
        self._slot_manager.set_slot(slot, SlotType.VID, buffer.getvalue())

    def process_slot_load(self, window, slot: int, filepath: str):
        file = pathlib.Path(filepath)
        ext = file.suffix.split(".")[-1]
        slottype = Slot.EXT_TO_SLOT_TYPE[ext]
        if slottype not in  (SlotType.IMG, SlotType.VID):
            # Most types, we just upload the file.
            with open(file, "rb") as f:
                self._slot_manager.set_slot(slot, slottype, f.read())

        else:
            img = Image.open(file)
            assert img.n_frames > 0
            if img.n_frames == 1:
                img = self.process_image(window, img)
                self.process_set_slot_img(slot, img)
            else:
                # > 1 frame
                imgs = []
                durations = []
                for frame in range(img.n_frames):
                    img.seek(frame)
                    imgs.append(self.process_image(window, img))
                    durations.append(img.info.get("duration", 1000/15))
                self.process_set_slot_vid(slot, imgs, durations)

    def process_slot_load_network(self, window, slot: int, url: str):
        file = pathlib.Path(urlunsplit(urlsplit(url)._replace(query="", fragment="")))
        ext = file.suffix.split(".")[-1]
        slottype = Slot.EXT_TO_SLOT_TYPE[ext]
        response = requests.get(url)
        if slottype not in  (SlotType.IMG, SlotType.VID):
            # Most types, we just upload the file.
            self._slot_manager.set_slot(slot, slottype, response.content)

        else:
            img = Image.open(io.BytesIO(response.content))
            frames = img.n_frames if hasattr(img, "n_frames") else 1
            assert frames > 0
            if frames == 1:
                img = self.process_image(window, img)
                self.process_set_slot_img(slot, img)
            else:
                # > 1 frame
                imgs = []
                durations = []
                for frame in range(frames):
                    img.seek(frame)
                    imgs.append(self.process_image(window, img))
                    durations.append(img.info.get("duration", 1000/15))
                self.process_set_slot_vid(slot, imgs, durations)

    def process_image(self, window, img):
        if img.width != MATRIX_WIDTH or img.height != MATRIX_HEIGHT:
            resample_method = window.combo_resample_method.itemData(window.combo_resample_method.currentIndex())
            resize_function = window.combo_resize_method.itemData(window.combo_resize_method.currentIndex())
            img = resize_function(im=img, size=(MATRIX_WIDTH, MATRIX_HEIGHT), resample=resample_method)
        img = img.convert("RGB")
        if window.checkbox_sharpen.isChecked():
            img = img.filter(ImageFilter.SHARPEN)
        return img


    def _send_live_img(self, img):
        buffer = io.BytesIO()
        img.save(buffer, format="gif")
        # TODO: update to better API.
        self._client_api.set_live(buffer.getvalue())

    def update_client_data(self, tochange: {str: Any}):
        """Update client's local data.
        """
        try:
            with open(os.path.join(self._location, "clientdata.json"), "r") as f:
                data = json.load(f)

            data.update(tochange)

            with open(os.path.join(self._location, "clientdata.json"), "w") as f:
                json.dump(data, f)
        except FileNotFoundError:
            with open(os.path.join(self._location, "clientdata.json"), "w") as f:
                json.dump(tochange, f)

    def get_client_data(self, key: str, default: Any):
        """Update client's local data.
        """
        try:
            with open(os.path.join(self._location, "clientdata.json"), "r") as f:
                data = json.load(f)
            return data[key]
        except (FileNotFoundError, IndexError):
            return default