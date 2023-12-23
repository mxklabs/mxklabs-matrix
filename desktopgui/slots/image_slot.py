from PIL import Image

class ImageSlot:
    def __init__(self, data: bytes, driver):
        self.driver = driver
        self.canvas = self.driver.get_canvas(Image.open(data))
    
    def start(self):
        self.driver.display_canvas(self.canvas)
    
    def run(self, start, deltatime: int):
        pass
    
    def end(self):
        pass