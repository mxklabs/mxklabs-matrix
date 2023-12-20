from PIL import Image
from PySide6 import QtGui

def pil_to_qimage(pil_img : Image) -> QtGui.QImage:
    """ Convert PIL image to Qt image."""
    temp = pil_img.convert('RGBA')
    return QtGui.QImage(
        temp.tobytes('raw', "RGBA"),
        temp.size[0],
        temp.size[1],
        QtGui.QImage.Format.Format_RGBA8888
    )
