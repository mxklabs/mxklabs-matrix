#!/usr/bin/env python
import json
import pathlib

from rgbmatrix import RGBMatrix, RGBMatrixOptions

with open(pathlib.Path(__file__).parents[0] / "config.json", "r") as f:
    CONFIG = json.load(f)

class MatrixDriver:
    def __init__(self):

        options = RGBMatrixOptions()
        options.rows                = 64 # Pretend its a 4x1 panel config.
        options.cols                = 64 # Pretend its a 4x1 panel config.
        options.chain_length        = 4  # Pretend its a 4x1 panel config.
        options.parallel            = 1
        options.row_address_type    = 0
        options.multiplexing        = 0
        options.pwm_bits            = 11
        options.brightness          = 100
        options.pwm_lsb_nanoseconds = 130
        options.led_rgb_sequence    = "RGB"

        # This is a custom pixel mapper for our set-up, see https://github.com/mxklabs/rpi-rgb-led-matrix/tree/MorkPixelMapper
        options.pixel_mapper_config = "Mork" 
        options.panel_type          = ""
        options.show_refresh_rate   = 1
        options.gpio_slowdown       = 2

        self._matrix = RGBMatrix(options = options)

    def run(self):
        offset_canvas = self._matrix.CreateFrameCanvas()
        for x in range(0, self._matrix.width):
            offset_canvas.SetPixel(x, x, 255, 255, 255)
            offset_canvas.SetPixel(offset_canvas.height - 1 - x, x, 255, 0, 255)

        for x in range(0, offset_canvas.width):
            offset_canvas.SetPixel(x, 0, 255, 0, 0)
            offset_canvas.SetPixel(x, offset_canvas.height - 1, 255, 255, 0)

        for y in range(0, offset_canvas.height):
            offset_canvas.SetPixel(0, y, 0, 0, 255)
            offset_canvas.SetPixel(offset_canvas.width - 1, y, 0, 255, 0)

        while True:
            offset_canvas = self._matrix.SwapOnVSync(offset_canvas)


# Main function
if __name__ == "__main__":
    matrix_driver = MatrixDriver()
    matrix_driver.run()

    if (not matrix_driver.process()):
        matrix_driver.print_help()
