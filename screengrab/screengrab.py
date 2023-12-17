import pyautogui 
import pygame
from PIL import Image, ImageEnhance
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--width", type=int, default=128,
                    help="The initial width of the selection")

parser.add_argument("-v", "--height", type=int, default=128,
                    help="The initial height of the selection")

parser.add_argument("-r", "--resizable", action="store_true",
                    help="Can the selection be resized")

args = parser.parse_args()

# STUFF TO CHANGE
SELECTION_SIZE = (args.width, args.height) #Initial selection size. Change selection_rect.size after program starts.
is_resizable = args.resizable # Can resize

image = pyautogui.screenshot()

enhancer = ImageEnhance.Brightness(image)

bright = pygame.image.fromstring(image.tobytes(), image.size, image.mode)

img = pygame.image.fromstring(enhancer.enhance(0.5).tobytes(), image.size, image.mode)

game = pygame.display.set_mode(image.size)

selection_pos = ((image.size[0] - SELECTION_SIZE[0]) // 2, (image.size[1] - SELECTION_SIZE[1]) // 2)
is_dragging = False
prev_mouse = None

selection_rect = pygame.Rect(selection_pos[0], selection_pos[1], SELECTION_SIZE[0], SELECTION_SIZE[1])

is_resizing = False
is_resizing_x = False
is_resizing_y = False
resize_anchor = None
RESIZE_MARGIN = 5

running = True
while running:
  mouse = pygame.mouse.get_pos()

  if is_resizable:
    is_y_top = selection_rect.top - RESIZE_MARGIN <= mouse[1] < selection_rect.top + RESIZE_MARGIN
    is_inside_y = selection_rect.top + RESIZE_MARGIN <= mouse[1] < selection_rect.bottom - RESIZE_MARGIN
    is_y_bottom =  selection_rect.bottom - RESIZE_MARGIN  <= mouse[1] < selection_rect.bottom + RESIZE_MARGIN

    is_x_left = selection_rect.left - RESIZE_MARGIN <= mouse[0] < selection_rect.left + RESIZE_MARGIN
    is_inside_x = selection_rect.left + RESIZE_MARGIN <= mouse[0] < selection_rect.right - RESIZE_MARGIN
    is_x_right =  selection_rect.right - RESIZE_MARGIN  <= mouse[0] < selection_rect.right + RESIZE_MARGIN
  else:
    is_y_top = False
    is_y_bottom = False
    is_x_left = False
    is_x_right = False
    is_inside_x = selection_rect.left <= mouse[0] < selection_rect.right   
    is_inside_y = selection_rect.top <= mouse[1] < selection_rect.bottom 

  if not is_dragging:
      if (not (is_y_top or is_inside_y or is_y_bottom)) or (not (is_x_left or is_inside_x or is_x_right)):
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
      elif is_inside_y and is_inside_x:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZEALL)
      elif is_inside_y:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZEWE)
      elif is_inside_x:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZENS)
      elif (is_y_top and is_x_left) or (is_y_bottom and is_x_right):
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZENWSE)
      else:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZENESW)
        
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
          running = False
          
    if event.type == pygame.KEYDOWN:
      if event.key == pygame.K_ESCAPE:
        running = False
        
    if event.type == pygame.MOUSEBUTTONDOWN:
      if event.button == 1:
        is_dragging = True
        is_resizing = True
        is_resizing_x = not is_inside_x
        is_resizing_y = not is_inside_y
        if is_inside_y and is_inside_x:
          is_resizing = False
        elif is_inside_y and is_x_left:
          resize_anchor="right"
        elif is_inside_y and is_x_right:
          resize_anchor="left"
        elif is_inside_x and is_y_top:
          resize_anchor="bottom"
        elif is_inside_x and is_y_bottom:
          resize_anchor="top"
        elif is_x_left and is_y_top:
          resize_anchor="bottomright"
        elif is_x_right and is_y_top:
          resize_anchor="bottomleft"
        elif is_x_left and is_y_bottom:
          resize_anchor="topright"
        elif is_x_right and is_y_bottom:
          resize_anchor="topleft"
        else:
          is_dragging = False
          is_resizing = False
          
        
    if event.type == pygame.MOUSEBUTTONUP:
      if event.button == 1:
        is_dragging = False
    if event.type == pygame.MOUSEMOTION:
      if is_dragging:
        if is_resizing:
          before = getattr(selection_rect, resize_anchor)
          if is_resizing_x:
            if "right" in resize_anchor:
              selection_rect.width -= event.rel[0]
            else:
              selection_rect.width += event.rel[0]
          if is_resizing_y:
            if "bottom" in resize_anchor:
              selection_rect.height -= event.rel[1]
            else:
              selection_rect.height += event.rel[1]
          setattr(selection_rect, resize_anchor, before)
        else:
          selection_rect.centerx += event.rel[0]
          selection_rect.centery += event.rel[1]
        
  
  game.blit(img, (0,0))
  game.blit(bright, selection_rect.topleft, selection_rect)
  pygame.display.flip()
pygame.quit()
