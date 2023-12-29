import threading
import time

from statistics import mean

from PIL import ImageChops

class GIFGrabber:

    def __init__(self, callback):
        """ Constructor. """
        self._callback = callback
        self._callback_called = False
        self._imgs = []
        self._img_timestamps = []
        self._valid_frame_indices = []
        self._durations = []
        self._processing_index = -1
        self._processing_thread_kill_event = threading.Event()
        self._processing_semaphore = threading.Semaphore(0)
        self._processing_thread = threading.Thread(target=self._process)
        self._processing_thread.start()

    def feed_img(self, img):
        """ Feed an new frame to the image grabber. """
        self._imgs.append(img)
        self._img_timestamps.append(time.perf_counter())
        self._processing_semaphore.release()

    def _process(self):
        """ Code for internal processing thread. """

        while (not self._processing_thread_kill_event.is_set()):
            if self._processing_semaphore.acquire(timeout=0.1):
                self._processing_index += 1

                # Work out if the frame is new.
                first_repeat = None
                for i in range(self._processing_index):
                    diff = ImageChops.difference(self._imgs[i], self._imgs[self._processing_index])
                    if diff.getbbox() is None:
                        first_repeat = i
                        break

                if first_repeat is None:
                    # The frame is new, should be part of the .gif.
                    self._valid_frame_indices.append(self._processing_index)
                    if self._processing_index > 0:
                        # Store duration for previous valid frame.
                        self._durations.append(int(1000*(self._img_timestamps[self._processing_index] - self._img_timestamps[self._valid_frame_indices[-2]])))
                else:
                    # If the frame is not new, and the frame we are repeating is
                    # the starting frame, but we do have more than one frame then we're done.
                    if first_repeat == 0 and len(self._valid_frame_indices) > 1:
                        # Store duration for last frame.
                        self._durations.append(int(1000*(self._img_timestamps[self._processing_index] - self._img_timestamps[self._valid_frame_indices[-1]])))
                        self._processing_thread_kill_event.set()
                        self._callback()
                        self._callback_called = True

    def cancel(self):
        """ Cancel processing. """
        self._processing_thread_kill_event.set()
        self._processing_thread.join()

    def done(self):
        """ Finish processing whereever we are now. """
        print(f'done - setting kill event')
        self._processing_thread_kill_event.set()
        print(f'done - joining')
        self._processing_thread.join()
        print(f'done - joined')
        if not self._callback_called:
            print(f'done - calling callback')
            self._callback()
            self._callback_called = True

    def imgs(self):
        """ Return frames. """
        assert len(self._valid_frame_indices)>0
        return [self._imgs[i] for i in self._valid_frame_indices]

    def durations(self):
        """ Return durations. """
        # It might be we have fewer durations than we have frames if 'done' was pressed.
        if len(self._durations):
          sensible_fake_duration = round(mean(self._durations))
        else:
          sensible_fake_duration = 100
        return self._durations + [sensible_fake_duration] * (len(self._valid_frame_indices) - len(self._durations))











