from enum import Enum

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
        self._last_screen_img = screen_img

        if self._mode == Mode.LIVE_STREAM:
            self._send_live_img(screen_img)

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

    def _send_live_img(self, img):
        buffer = io.BytesIO()
        self._last_screen_img.save(buffer, format="gif")
        # TODO: update to better API.
        self._client_api.set_slot(0, buffer.getvalue())