from enum import Enum
from PIL import Image, ImageChops

import clientapi
import io

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

    def process_set_slot(self, slot : int, img : Image):
        """ Set a slot for an image. """
        buffer = io.BytesIO()
        img.save(buffer, format="gif")
        self._client_api.set_slot(slot, buffer.getvalue())

    def process_set_slot_vid(self, slot : int, imgs : [Image], durations : [int]):
        """ Set a slot for a video. """
        buffer = io.BytesIO()
        imgs[0].save(buffer, format="gif", save_all=True, append_images=imgs[1:], duration=durations, loop=0)
        self._client_api.set_slot(slot, buffer.getvalue())

    def _send_live_img(self, img):
        buffer = io.BytesIO()
        img.save(buffer, format="gif")
        # TODO: update to better API.
        self._client_api.set_live(buffer.getvalue())