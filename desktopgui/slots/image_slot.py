import io

from PIL import Image

class ImageSlot:
    def __init__(self, data: bytes, driver):
        self.driver = driver
        
        self.canvas = self.driver.get_canvas(Image.open(io.BytesIO(data)))
        self.running = False
    
    def start(self):
        self.driver.display_canvas(self.canvas)
        self.running = True
    
    def run(self, deltatime: int):
        if not self.running:
            self.start()
    
    def end(self):
        self.running = False