import time

from clientapi import Mode
from slots import ImageSlot, GifSlot

class DisplayManager:
    def __init__(self, driver):
        self.driver = driver
        self.mode = Mode.SHOW_SLOT
        self.slots = [None for i in range(20)]
        self.staticslot = 0
        self.lasttime = time.time_ns() // 1000000
    
    def set_slot(self, slotnum, data):
        self.load_slot(slotnum, data)
    
    def load_slot(self, slotnum, data):
        slot_identifier = data[0]
        slot_data = data[1:]
        if slot_identifier == 1:
            self.slots[slotnum] = ImageSlot(slot_data, self.driver)
        if slot_identifier == 2:
            self.slots[slotnum] = GifSlot(slot_data, self.driver)
    
    def run(self):
        while True:
            newtime = time.time_ns() // 1000000
            deltatime = newtime - self.lasttime
            if self.mode == Mode.SHOW_SLOT:
                #print("EPIC", self.slots)
                slot = self.slots[self.staticslot]
                if slot is not None:
                    #print("GGGEAHGH")
                    slot.run(deltatime)
            self.lasttime = newtime