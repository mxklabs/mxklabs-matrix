import matrix
import time

def square():
    for x in range(128):
        matrix.set_pixel(x, 0, (255, 0, 0))
    for y in range(128):
        matrix.set_pixel(0, y, (0, 255, 0))
    for x in range(128):
        matrix.set_pixel(x, 127, (0, 0, 255))
    for y in range(128):
        matrix.set_pixel(127, y, (255, 255, 0))

    matrix.send_to_matrix()

def moving_square():
    x_move = 0
    y_move = 0
    while True:
        matrix.reset()
        for x in range(0, 63):
            for y in range(0, 63):
                matrix.set_pixel(x + x_move, y + y_move, (255,255,255))
        x_move += 10
        y_move += 12
        x_move %= 64
        y_move %= 64
        matrix.send_to_matrix()
        time.sleep(1)

matrix.run(moving_square)