from insightface.app import FaceAnalysis
import cv2
import numpy as np

face_app = FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"]
)

face_app.prepare(
    ctx_id=0,
    det_size=(320, 320)
)

def detect_face(frame):
    if frame is None:
        return None, "No frame provided"

    # Kunin ang aktwal na taas at lapad ng camera frame
    h, w, _ = frame.shape

    faces = face_app.get(frame)

    if len(faces) == 0:
        return None, "No face detected"

    if len(faces) > 1:
        return None, "Multiple faces detected"

    face = faces[0]

    # ==========================================
    # PROTECTION LAYER: Detection Confidence Check
    # Sinisigurong totoo at malinaw ang mukha bago i-crop (i-re-reject ang background/anino)
    # ==========================================
    det_score = getattr(face, 'det_score', 1.0)
    if det_score < 0.60:  # Same threshold para sa consistency
        return None, "Low detection confidence (False positive)"

    x1, y1, x2, y2 = map(int, face.bbox)

    # ==========================================
    # PROTECTION LAYER: Bounding Box Clipping
    # Siguraduhing hindi lalabas sa screen ang coordinates
    # ==========================================
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(w, x2)
    y2 = min(h, y2)

    # I-crop ang mukha gamit ang ligtas na coordinates
    crop = frame[y1:y2, x1:x2]

    if crop.size == 0 or crop.shape[0] == 0 or crop.shape[1] == 0:
        return None, "Invalid face dimensions"

    # I-resize sa standard size na kailangan ng embedding system mo
    crop = cv2.resize(crop, (160, 160))

    return crop, "OK"