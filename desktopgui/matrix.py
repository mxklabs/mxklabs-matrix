import pathlib
import json
import random
import io
import threading

import clientapi
import deviceapi

from PIL import Image
import pygame
import requests

with open(pathlib.Path(__file__).parents[0] / "config.json", "r") as f:
    CONFIG = json.load(f)

api = None
img = Image.new("RGB", (128,128))

def scale2x(im):
  return pygame.transform.scale(im, (im.get_width() * 2, im.get_height() * 2))

class PygameDriver:
    def __init__(self):
        self.game = pygame.display.set_mode((256,256))
    
    def set_image(self, image):
        image_data = image.tobytes()
        image_dimensions = image.size
        pygame_surface = scale2x(pygame.image.fromstring(image_data, image_dimensions, "RGB"))
        self.game.blit(pygame_surface, (0,0))

def reset():
    global img
    img = Image.new("RGB", (128,128))

def run(f, *args, **kwargs):
    connect(*args, **kwargs)
    is_pygame = isinstance(api.matrix_driver, PygameDriver)
    print(is_pygame)
    func_thread = threading.Thread(target = f)
    func_thread.start()
    if is_pygame:
        done = False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    done = True
            pygame.display.flip()
    func_thread.join()

def connect(hostname = CONFIG["connectToIP4Addr"], port = CONFIG["port"]):
    global api
    api = clientapi.ClientAPI(f"http://{hostname}:{port}")
    x = random.randint(100, 10000)
    try:
        res = api.ping(x)
        success = (x + res) == 0
    except requests.exceptions.ConnectionError:
        success = False
    if success:
        print("Connected to raspberry pi!")
    else:
        print("Simulating matrix")
        api = deviceapi.DeviceAPI(PygameDriver())

def set_pixel(x, y, color):
    img.putpixel((x,y), color)

def send_to_matrix():
    arr = io.BytesIO()
    img.save(arr, format="gif")
    api.set_slot(0, arr.getvalue())