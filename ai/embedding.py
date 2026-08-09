from insightface.app import FaceAnalysis
import mysql.connector
import numpy as np
import cv2
import os

# ==========================================
# EXPLICIT PATH DEFINITIONS (Para walang ImportError)
# ==========================================
AI_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(AI_DIR)
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "uploads", "faces")
EMBEDDING_FOLDER = os.path.join(AI_DIR, "embeddings")

# Siguraduhing may embeddings folder
if not os.path.exists(EMBEDDING_FOLDER):
    os.makedirs(EMBEDDING_FOLDER, exist_ok=True)

# ==========================================
# INSIGHTFACE
# ==========================================

app = FaceAnalysis(name="buffalo_l")
app.prepare(ctx_id=0, det_size=(640, 640))

# ==========================================
# GENERATE EMBEDDING
# ==========================================

def generate_embedding(student_id):
    student_folder = os.path.join(UPLOAD_FOLDER, student_id)

    if not os.path.isdir(student_folder):
        raise Exception(f"Student folder not found: {student_folder}")

    image_files = sorted([
        f for f in os.listdir(student_folder)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ])

    if len(image_files) == 0:
        raise Exception("No captured images found.")

    embeddings = []

    print(f"[EMBEDDING] Processing {len(image_files)} images for student: {student_id}")

    for file in image_files:
        path = os.path.join(student_folder, file)
        img = cv2.imread(path)

        if img is None:
            print(f"[DEBUG] Failed to read image file: {file}")
            continue

        # 1. Subukang i-detect gamit ang InsightFace sa original na imahe
        faces = app.get(img)

        # 2. FALLBACK: Kung walang nakita, subukang lagyan ng padding (border) 
        # sakaling ang imahe ay naka-crop nang masyadongikot sa mukha
        if len(faces) == 0:
            print(f"[DEBUG] Direct detection failed for {file}. Applying padding fallback...")
            h, w, _ = img.shape
            # Magdagdag ng 50 pixels na padding sa paligid para lumuwag ang mukha sa paningin ng AI
            padded_img = cv2.copyMakeBorder(img, 50, 50, 50, 50, cv2.BORDER_CONSTANT, value=[255, 255, 255])
            faces = app.get(padded_img)

        if len(faces) == 0:
            print(f"[DEBUG] No face detected by InsightFace even with padding in: {file}")
            continue

        embeddings.append(faces[0].embedding)

    if len(embeddings) == 0:
        raise Exception("No valid faces detected.")

    print(f"[EMBEDDING] Successfully extracted {len(embeddings)}/{len(image_files)} valid face embeddings.")

    avg_embedding = np.mean(embeddings, axis=0)
    embedding_path = os.path.join(EMBEDDING_FOLDER, f"{student_id}.npy")
    np.save(embedding_path, avg_embedding)

    print("=" * 60)
    print("Embedding Saved:", embedding_path)

    return "completed"


# ==========================================
# AUTO-PROCESS ALL STUDENTS KUNG PINATAKBO DIREKTA
# ==========================================
if __name__ == "__main__":
    print("[INFO] Scanning upload folders for student embeddings...")
    if os.path.exists(UPLOAD_FOLDER):
        student_ids = os.listdir(UPLOAD_FOLDER)
        for s_id in student_ids:
            s_path = os.path.join(UPLOAD_FOLDER, s_id)
            if os.path.isdir(s_path):
                print(f"[PROCESSING] Generating embedding for student: {s_id}")
                try:
                    generate_embedding(s_id)
                    print(f"[SUCCESS] Embedding generated for {s_id}")
                except Exception as e:
                    print(f"[ERROR] Failed for {s_id}: {e}")
        print("[INFO] All folder processing completed.")
    else:
        print(f"[ERROR] Upload folder not found at: {UPLOAD_FOLDER}")