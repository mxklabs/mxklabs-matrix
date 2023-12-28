from enum import Enum
import io
import json
import os
import pathlib
from typing import Any

from PIL import Image, ImageChops

import clientapi
from slotmanager import SlotType

with open(pathlib.Path(__file__).parents[0] / "config.json", "r") as f:
    CONFIG = json.load(f)

class Mode(Enum):
   LIVE_SNAPSHOT = 0
   LIVE_STREAM = 1
   SLOT_SPECIFIC = 2
   SLOT_ROUND_ROBIN = 3
   DARK = 4

class ClientLogic:

    def __init__(self):
        """ Constructor for client logic class. """
        self._client_api = clientapi.ClientAPI()
        self._mode = Mode.DARK
        self._last_screen_img = None
        self._location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        self._have_slot = [False] * CONFIG['numSlots']

        # Check if we got slots.
        for i in range(CONFIG['numSlots']):
            if self._client_api.get_slot(i) is not None:
                self._have_slot[i] = True

    def have_slot(self, slot : int) -> bool:
        """ Check if we have a slot. """
        return self._have_slot[slot]

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

    def process_clear_slot(self, slot : int):
        """ Clear a slot. """
        if self._client_api.clear_slot(slot):
            self._have_slot[slot] = False

    def process_set_slot_img(self, slot : int, img : Image.Image | None):
        """ Set a slot for an image. """
        if img is None:
            self._client_api.set_slot(slot, None)
            self._have_slot[slot] = False
        else:
            buffer = io.BytesIO()
            img.save(buffer, format="png")
            self._client_api.set_slot(slot, SlotType.IMG, buffer.getvalue())
            self._have_slot[slot] = True

    def process_set_slot_vid(self, slot : int, imgs : [Image], durations : [int]):
        """ Set a slot for a video. """
        buffer = io.BytesIO()
        imgs[0].save(buffer, format="gif", save_all=True, append_images=imgs[1:], duration=durations, loop=0)
        self._client_api.set_slot(slot, SlotType.VID, buffer.getvalue())
        self._have_slot[slot] = True

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