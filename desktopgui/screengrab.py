"""User interface to allow the user to select a portion of their screen to use
"""
import argparse
from enum import Enum

import pyautogui

import pygame
from PIL import ImageEnhance

BORDER_WIDTH = 1

class MousePositionContext(Enum):
    """Specifies where the mouse is relative to the selection along 1 axis.
    """
    OUTSIDE = 1
    NEGATIVE_BORDER = 2
    INSIDE = 3
    POSITIVE_BORDER = 4

def get_mouse_position_context(rect, can_use_border, resize_margin=5):
    """Gives context about the position of the mouse relative to the selection

    Args:
        rect (pygame.Rect): The selection rect
        can_use_border (bool): whether or not the mouse can interact with borders.
        resize_margin (int, optional): width either side of the border the mouse
          can use to resuze. Defaults to 5.

    Returns:
        tuple of 2 MousePositionContext: The context
    """
    x_ctx = MousePositionContext.OUTSIDE
    y_ctx = MousePositionContext.OUTSIDE
    pos = pygame.mouse.get_pos()
    if can_use_border:
        if rect.left - resize_margin <= pos[0] < rect.left + resize_margin:
            x_ctx = MousePositionContext.NEGATIVE_BORDER
        if rect.left + resize_margin <= pos[0] < rect.right - resize_margin:
            x_ctx = MousePositionContext.INSIDE
        if  rect.right - resize_margin <= pos[0] < rect.right + resize_margin:
            x_ctx = MousePositionContext.POSITIVE_BORDER

        if rect.top - resize_margin <= pos[1] < rect.top + resize_margin:
            y_ctx = MousePositionContext.NEGATIVE_BORDER
        if rect.top + resize_margin <= pos[1] < rect.bottom - resize_margin:
            y_ctx = MousePositionContext.INSIDE
        if rect.bottom - resize_margin <= pos[1] < rect.bottom + resize_margin:
            y_ctx = MousePositionContext.POSITIVE_BORDER
    else:
        if rect.left <= pos[0] < rect.right:
            x_ctx = MousePositionContext.INSIDE
        if rect.top <= pos[1] < rect.bottom:
            y_ctx = MousePositionContext.INSIDE
    return (x_ctx, y_ctx)

def get_cursor_type(ctx):
    """Returns the cursor type for the given context

    Args:
        ctx (tuple of 2 MousePositionContext): The cursor context

    Returns:
        int: The pygame constant referring to the correct cursor type.
    """
    if ctx[0] == MousePositionContext.OUTSIDE or ctx[1] == MousePositionContext.OUTSIDE:
        return pygame.SYSTEM_CURSOR_ARROW
    if ctx[0] == MousePositionContext.INSIDE and ctx[1] == MousePositionContext.INSIDE:
        return pygame.SYSTEM_CURSOR_SIZEALL
    if ctx[1] == MousePositionContext.INSIDE:
        return pygame.SYSTEM_CURSOR_SIZEWE
    if ctx[0] == MousePositionContext.INSIDE:
        return pygame.SYSTEM_CURSOR_SIZENS
    if ctx[0] == ctx[1]:
        return pygame.SYSTEM_CURSOR_SIZENWSE
    return pygame.SYSTEM_CURSOR_SIZENESW

def handle_event(event, ctx, selection_rect, drag_state):
    """Handles pygame events.

    Args:
        event (pygame event)
        ctx (tuple of 2 MousePositionContext): context of mouse position
        selection_rect (pygame.Rect): the rect of the selection
        drag_state (dict): data referring to the state of the dragging.
    """
    if event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1:
            drag_state["is_dragging"] = True
            drag_state["is_resizing"] = True
            drag_state["is_resizing_x"] = ctx[0] != MousePositionContext.INSIDE
            drag_state["is_resizing_y"] = ctx[1] != MousePositionContext.INSIDE
            if ctx[0] == MousePositionContext.INSIDE and \
                    ctx[1] == MousePositionContext.INSIDE:
                drag_state["is_resizing"] = False
            elif ctx[0] == MousePositionContext.NEGATIVE_BORDER and \
                    ctx[1] == MousePositionContext.INSIDE:
                drag_state["resize_anchor"]="right"
            elif ctx[0] == MousePositionContext.POSITIVE_BORDER and \
                    ctx[1] == MousePositionContext.INSIDE:
                drag_state["resize_anchor"]="left"
            elif ctx[0] == MousePositionContext.INSIDE and \
                    ctx[1] == MousePositionContext.NEGATIVE_BORDER:
                drag_state["resize_anchor"]="bottom"
            elif ctx[0] == MousePositionContext.INSIDE and \
                    ctx[1] == MousePositionContext.POSITIVE_BORDER:
                drag_state["resize_anchor"]="top"
            elif ctx[0] == MousePositionContext.NEGATIVE_BORDER and \
                    ctx[1] == MousePositionContext.NEGATIVE_BORDER:
                drag_state["resize_anchor"]="bottomright"
            elif ctx[0] == MousePositionContext.POSITIVE_BORDER and \
                    ctx[1] == MousePositionContext.NEGATIVE_BORDER:
                drag_state["resize_anchor"]="bottomleft"
            elif ctx[0] == MousePositionContext.NEGATIVE_BORDER and \
                    ctx[1] == MousePositionContext.POSITIVE_BORDER:
                drag_state["resize_anchor"]="topright"
            elif ctx[0] == MousePositionContext.POSITIVE_BORDER and \
                    ctx[1] == MousePositionContext.POSITIVE_BORDER:
                drag_state["resize_anchor"]="topleft"
            else:
                drag_state["is_dragging"] = False
                drag_state["is_resizing"] = False

    if event.type == pygame.MOUSEBUTTONUP:
        if event.button == 1:
            drag_state["is_dragging"] = False

    if event.type == pygame.MOUSEMOTION:
        if drag_state["is_dragging"]:
            if drag_state["is_resizing"]:
                before = getattr(selection_rect, drag_state["resize_anchor"])
                if drag_state["is_resizing_x"]:
                    if "right" in drag_state["resize_anchor"]:
                        selection_rect.width -= event.rel[0]
                    else:
                        selection_rect.width += event.rel[0]
                    if selection_rect.width < 128:
                        selection_rect.width = 128
                        drag_state["is_dragging"] = False
                if drag_state["is_resizing_y"]:
                    if "bottom" in drag_state["resize_anchor"]:
                        selection_rect.height -= event.rel[1]
                    else:
                        selection_rect.height += event.rel[1]
                    if selection_rect.height < 128:
                        selection_rect.height = 128
                        drag_state["is_dragging"] = False
                setattr(selection_rect, drag_state["resize_anchor"], before)
            else:
                selection_rect.centerx += event.rel[0]
                selection_rect.centery += event.rel[1]

# pylint: disable=no-member
def main(width = 128, height = 128, is_resizable = False):
    """Entry function

    Args:
        width (int, optional): Initial width of selection. Defaults to 128.
        height (int, optional): Initial height of selection. Defaults to 128.
        is_resizable (bool, optional): Can selection be resized. Defaults to False.
    """

    image = pyautogui.screenshot()
    enhancer = ImageEnhance.Brightness(image)

    img = pygame.image.fromstring(enhancer.enhance(0.5).tobytes(), image.size, image.mode)
    bright = pygame.image.fromstring(image.tobytes(), image.size, image.mode)

    game = pygame.display.set_mode(image.size)
    selection_rect = pygame.Rect((image.size[0]-width)//2, (image.size[1]-height)//2, width, height)

    drag_state = {"is_dragging":False, "is_resizing":False,
                   "is_resizing_x":False, "is_resizing_y":False, "resize_anchor":None}

    running = True
    while running:
        ctx = get_mouse_position_context(selection_rect, is_resizable)

        if not drag_state["is_dragging"]:
            pygame.mouse.set_cursor(get_cursor_type(ctx))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

            handle_event(event, ctx, selection_rect, drag_state)

        game.blit(img, (0,0))
        pygame.draw.rect(game, (255, 0, 0), (selection_rect.left -BORDER_WIDTH,
                                              selection_rect.top - BORDER_WIDTH,
                                              selection_rect.width + 2 * BORDER_WIDTH,
                                              selection_rect.height + 2 * BORDER_WIDTH)
                                                  , width=5)
        game.blit(bright, selection_rect.topleft, selection_rect)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--width", type=int, default=128,
                        help="The initial width of the selection")

    parser.add_argument("-v", "--height", type=int, default=128,
                        help="The initial height of the selection")

    parser.add_argument("-r", "--resizable", action="store_true",
                        help="Can the selection be resized")

    args = parser.parse_args()
    main(args.width, args.height, args.resizable)
