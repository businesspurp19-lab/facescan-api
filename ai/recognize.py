import os
import cv2
import numpy as np
from ai.config import EMBEDDING_FOLDER, RECOGNITION_THRESHOLD

embeddings = {}

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
            embedding = np.squeeze(embedding)
            if embedding.ndim > 1:
                embedding = embedding.flatten()
                
            embeddings[student_id] = embedding
            print(f"[Recognition] Successfully loaded embedding for ID: {student_id} with shape {embedding.shape}")
        except Exception as e:
            print(f"[Recognition Error] Failed loading {file}: {e}")

    print(f"[Recognition] Total loaded embeddings: {len(embeddings)}")
    return True

refresh()

def compare_faces(embedding1, embedding2):
    if embedding1 is None or embedding2 is None:
        return 0.0

    norm1 = np.linalg.norm(embedding1)
    norm2 = np.linalg.norm(embedding2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0

    embedding1 = embedding1 / norm1
    embedding2 = embedding2 / norm2

    return float(np.dot(embedding1, embedding2))

def recognize_face(frame):
    if frame is None or frame.size == 0:
        return None, 0.0, None

    resized = cv2.resize(frame, (112, 112))
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    normalized = gray.astype(np.float32) / 255.0
    current_embedding = normalized.flatten()
    
    norm = np.linalg.norm(current_embedding)
    if norm > 0:
        current_embedding = current_embedding / norm

    h, w, _ = frame.shape
    bbox = np.array([0, 0, w, h])

    best_student = None
    best_score = -1.0 

    for student_id, saved_embedding in embeddings.items():
        score = compare_faces(current_embedding, saved_embedding)

        if score > best_score:
            best_score = score
            best_student = student_id

    confidence = round(max(0.0, best_score) * 100, 2)

    if best_score >= RECOGNITION_THRESHOLD:
        return best_student, confidence, bbox

    return None, confidence, bbox

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
