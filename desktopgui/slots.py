from enum import IntEnum
import io
import json
import os
import pathlib
import re
import threading
from typing import Union, TYPE_CHECKING
import time

import find_system_fonts_filename
from PIL import Image, ImageFont, ImageDraw

if TYPE_CHECKING:
    from matrixdriver import MatrixDriver
    from matrix import PygameDriver

with open(pathlib.Path(__file__).parents[0] / "config.json", "r") as f:
    CONFIG = json.load(f)
    MATRIX_WIDTH = CONFIG['matrixWidth']
    MATRIX_HEIGHT = CONFIG['matrixHeight']

class SlotType(IntEnum):
    NULL        = 0
    IMG         = 1
    VID         = 2
    TXT         = 3

class Slot:
    EXT_TO_SLOT_TYPE = {"png": SlotType.IMG, "gif": SlotType.VID, "txt": SlotType.TXT}

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
            case SlotType.TXT:
                return TextSlot(data)
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
    
def get_text_size(font, text):
    left, top, right, bottom = font.getbbox(text)
    return right - left, bottom - top


DEFAULT_FONT = "Comic" if os.name == 'nt' else "FreeSans"

FONTNAME_PATTERN = re.compile("\W+")
PROCESS_FONTNAME = lambda x: FONTNAME_PATTERN.sub("", x.strip()).lower()

FONTS = {PROCESS_FONTNAME(pathlib.Path(i).stem): i for i in find_system_fonts_filename.get_system_fonts_filename()}

MATRIX_PAD = MATRIX_WIDTH // 2

def look_for_font(fontname : str, size: int, old: ImageFont.ImageFont | None) -> ImageFont.ImageFont:
    processed_fontname = PROCESS_FONTNAME(fontname)
    font = FONTS.get(processed_fontname, None)
    if font is None:
        return old
    return ImageFont.truetype(font, size=size)

def clamp(num, _max, _min=0):
    return max(min(_max, num), _min)

def hex_color_to_tuple(color):
    return (int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16))

class TextSlot(Slot):
    def __init__(self, data: bytes):
        self._data = data
        self._imgs = None
        self._scrollspeeds = None # Pixels per second
        self._fps = 15
    
    def _ensure_imgs_available(self):
        if self._imgs is None:
            text = self._data.decode('utf-8')
            bg = (0, 0, 0)
            fg = (255, 255, 255)
            scrollspeed = 50
            self._imgs = []
            self._scrollspeeds = []
            font: ImageFont.ImageFont = look_for_font(DEFAULT_FONT, 80, None)
            for line in text.splitlines():
                line = line.strip()
                if line.startswith("?"):
                    #All branches should continue
                    if line.startswith("?fg"):
                        fg = hex_color_to_tuple(next(re.finditer("#([0-9a-fA-F]{6})", line)).group(1))
                        continue
                    if line.startswith("?bg"):
                        bg = hex_color_to_tuple(next(re.finditer("#([0-9a-fA-F]{6})", line)).group(1))
                        continue
                    raise NotImplementedError
                else:
                    size = get_text_size(font, line)
                    img = Image.new("RGB", (size[0], MATRIX_WIDTH), bg)
                    draw = ImageDraw.Draw(img)
                    draw.text((0,0), line, font=font, fill=fg)
                    self._imgs.append(img.convert('RGB'))
                    self._scrollspeeds.append(scrollspeed)

    def run_slot(self, driver : Union['MatrixDriver', 'PygameDriver'], kill_event : threading.Event, minimum_time: float | None=None):
        """ Show animation in a single slot. Designed to run as part of a thread.
        """
        self._ensure_imgs_available()
        frame = 0
        img = self._imgs[frame]
        scroll = -MATRIX_PAD
        scrollspeed = self._scrollspeeds[frame]
        maxscroll = img.size[0]

        start_time = time.perf_counter()

        while not kill_event.is_set():
            try:
                driver.set_image(img.crop((clamp(int(scroll), maxscroll - MATRIX_WIDTH), 0, clamp(int(scroll) + MATRIX_WIDTH, maxscroll, _min=MATRIX_WIDTH), MATRIX_HEIGHT)))
                scroll += scrollspeed / self._fps
                if scroll >= maxscroll - MATRIX_PAD:
                    frame += 1
                    img = self._imgs[frame]
                    scroll = -MATRIX_PAD
                    scrollspeed = self._scrollspeeds[frame]
                    maxscroll = img.size[0]

                # Sleep for the frame duration.
                time.sleep(1/self._fps)

            except IndexError:
                now = time.perf_counter()
                if minimum_time is None or (now - start_time) < minimum_time:
                    frame = 0
                    img = self._imgs[frame]
                    scroll = -MATRIX_PAD
                    scrollspeed = self._scrollspeeds[frame]
                    maxscroll = img.size[0]
                    continue
                else:
                    break
    
    def ext(self) -> str:
        return "txt"