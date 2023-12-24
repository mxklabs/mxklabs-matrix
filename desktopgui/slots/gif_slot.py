import io

from PIL import Image

class GifSlot:
    def __init__(self, data: bytes, driver):
        self.driver = driver
        images = Image.open(io.BytesIO(data))
        self.canvases = []
        self.durations = []
        for frame in range(images.n_frames):
            images.seek(frame)
            self.canvases.append(driver.get_canvas(images))
            self.durations.append(images.info['duration'])
        self.frame = 0
        self.timeleft = self.durations[0]
        self.frames = images.n_frames
    
    def start(self):
        pass
    
    def run(self, deltatime: int):
        self.timeleft -= deltatime
        if self.timeleft < 0:
            self.frame = (self.frame + 1) % self.frames
            self.timeleft += self.durations[self.frame]
            self.driver.display_canvas(self.canvases[self.frame])
    
    def end(self):
        pass