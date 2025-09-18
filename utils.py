import os
from PIL import Image
import cv2

def save_thumbnail(image_bgr, path, size=(320,240), quality=80):
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(image_rgb)
    img.thumbnail(size)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, format='JPEG', quality=quality)
    return path
