import cv2
import numpy as np
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
cascade_path = os.path.join(script_dir, "haarcascade_frontalface_default.xml")

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def detect_face(frame):
    if frame is None:
        return None, "No frame provided"

    h, w, _ = frame.shape

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )

    if len(faces) == 0:
        return None, "No face detected"

    if len(faces) > 1:
        return None, "Multiple faces detected"

    # Kunin ang coordinates ng unang mukha (x, y, w, h)
    x, y, fw, fh = faces[0]
    x1, y1 = x, y
    x2, y2 = x + fw, y + fh

    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(w, x2)
    y2 = min(h, y2)

    crop = frame[y1:y2, x1:x2]

    if crop.size == 0 or crop.shape[0] == 0 or crop.shape[1] == 0:
        return None, "Invalid face dimensions"

    crop = cv2.resize(crop, (160, 160))

    return crop, "OK"
