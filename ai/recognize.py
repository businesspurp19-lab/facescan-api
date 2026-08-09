import os
import cv2
import numpy as np
from insightface.app import FaceAnalysis
from ai.config import EMBEDDING_FOLDER, RECOGNITION_THRESHOLD

# ==========================================
# INSIGHTFACE MODEL
# ==========================================
# Ginamit ang 640x640 para maging pareho sa registration at mas madaling mamukaan ang mukha
app = FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"]
)

app.prepare(
    ctx_id=0,
    det_size=(640, 640)
)

# ==========================================
# GLOBAL EMBEDDINGS
# ==========================================
embeddings = {}

# ==========================================
# LOAD / REFRESH EMBEDDINGS
# ==========================================

def refresh():
    global embeddings
    embeddings.clear()

    os.makedirs(
        EMBEDDING_FOLDER,
        exist_ok=True
    )

    files = sorted(os.listdir(EMBEDDING_FOLDER))

    for file in files:
        if not file.endswith(".npy"):
            continue

        student_id = file[:-4]
        path = os.path.join(EMBEDDING_FOLDER, file)

        try:
            embedding = np.load(path)
            # SIGURUHING 1D ARRAY ITO PARA SA TAMANG COSINE SIMILARITY MATH
            embedding = np.squeeze(embedding)
            if embedding.ndim > 1:
                embedding = embedding.flatten()
                
            embeddings[student_id] = embedding
            print(f"[Recognition] Successfully loaded embedding for ID: {student_id} with shape {embedding.shape}")
        except Exception as e:
            print(f"[Recognition Error] Failed loading {file}: {e}")

    print(f"[Recognition] Total loaded embeddings: {len(embeddings)}")
    return True

# Awtomatikong i-load ang mga embeddings sa pagsisimula ng app
refresh()

# ==========================================
# COSINE SIMILARITY
# ==========================================
def compare_faces(embedding1, embedding2):
    if embedding1 is None or embedding2 is None:
        return 0.0

    # L2 Normalization para sa tumpak na angular distance match
    norm1 = np.linalg.norm(embedding1)
    norm2 = np.linalg.norm(embedding2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0

    embedding1 = embedding1 / norm1
    embedding2 = embedding2 / norm2

    return float(np.dot(embedding1, embedding2))

# ==========================================
# FACE RECOGNITION ENGINE
# ==========================================
def recognize_face(frame):
    if frame is None:
        return None, 0.0, None

    faces = app.get(frame)

    if len(faces) == 0:
        return None, 0.0, None

    face = faces[0]

    # ==========================================
    # PROTECTION LAYER: Detection Confidence Check
    # ==========================================
    det_score = getattr(face, 'det_score', 1.0)
    if det_score < 0.50:  # Ibaba sa 0.50 para madaling masagap ang live frames
        return None, 0.0, None

    current_embedding = face.embedding
    bbox = face.bbox.astype(int)

    best_student = None
    best_score = -1.0 

    # Mag-loop sa lahat ng rehistradong estudyante sa cache dictionary
    for student_id, saved_embedding in embeddings.items():
        score = compare_faces(current_embedding, saved_embedding)

        if score > best_score:
            best_score = score
            best_student = student_id

    # I-convert ang raw similarity score sa readable confidence percentage (0-100%)
    confidence = round(max(0.0, best_score) * 100, 2)

    # Ligtas na pagkumpara gamit ang hilaw na decimal score
    if best_score >= RECOGNITION_THRESHOLD:
        return best_student, confidence, bbox

    return None, confidence, bbox

# ==========================================
# REAL-TIME LIVE VIDEO ENGINE LOOP HOOK
# ==========================================
def recognize_live_stream(logger_instance, subject_id=None, subject_name=None, subject_code=None):
    video_capture = cv2.VideoCapture(0)
    
    if not video_capture.isOpened():
        print("[CAMERA ERROR] Could not initialize structural hardware device framework loop.")
        return

    print("[CAMERA ENGINE] Video stream framework loop active. FaceScan Core Monitoring...")
    
    last_logged_student = None
    cooldown_start_time = 0
    COOLDOWN_DURATION = 5.0 

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("[STREAM FAULT] Failed to grab frame interface buffer partition.")
            break

        student_id, confidence, bbox = recognize_face(frame)

        status_color = (0, 0, 255) 
        display_label = f"Unknown Face ({confidence}%)"

        if student_id is not None:
            status_color = (0, 255, 0) 
            display_label = f"ID: {student_id} ({confidence}%)"

            import time 
            
            if student_id != last_logged_student or (time.time() - cooldown_start_time) > COOLDOWN_DURATION:
                mock_name = f"Student_{student_id}" 
                
                # Ipinapasa na ngayon ang subject variables patungo sa logger
                success = logger_instance.log_face_match(
                    student_id=student_id,
                    student_name=mock_name,
                    confidence=(confidence / 100.0),
                    subject_id=subject_id,         
                    subject_name=subject_name,     
                    subject_code=subject_code      
                )
                
                if success:
                    last_logged_student = student_id
                    cooldown_start_time = time.time()

        if bbox is not None:
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), status_color, 2)
            cv2.putText(frame, display_label, (bbox[0], bbox[1] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 2)

        cv2.putText(frame, "FaceScan Engine Terminal Node Mode", (15, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, "Press [ESC] key to exit and close window session tracking.", (15, 55), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
        
        cv2.imshow("FaceScan Terminal Engine - Camera View", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27: 
            print("[CAMERA ENGINE] Hardware interruption loop execution signal received. Closing view matrix framework.")
            break

    video_capture.release()
    cv2.destroyAllWindows()