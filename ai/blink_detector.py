import cv2
import dlib
import numpy as np
from scipy.spatial import distance

# Load detector + predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(
    "ai/models/shape_predictor_68_face_landmarks.dat"
)

# Eye landmarks
LEFT_EYE = [36, 37, 38, 39, 40, 41]
RIGHT_EYE = [42, 43, 44, 45, 46, 47]

def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

def detect_blink(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    if len(faces) == 0:
        return False, "No face detected"

    for face in faces:

        landmarks = predictor(gray, face)

        left_eye = []
        right_eye = []

        for n in LEFT_EYE:
            x = landmarks.part(n).x
            y = landmarks.part(n).y
            left_eye.append((x, y))

        for n in RIGHT_EYE:
            x = landmarks.part(n).x
            y = landmarks.part(n).y
            right_eye.append((x, y))

        left_ear = eye_aspect_ratio(left_eye)
        right_ear = eye_aspect_ratio(right_eye)

        ear = (left_ear + right_ear) / 2.0

        # THRESHOLD (adjustable)
        if ear < 0.21:
            return True, "Blink detected"

        return False, "No blink"

    return False, "No valid face"