import os
import cv2
import numpy as np
import mysql.connector

from insightface.app import FaceAnalysis

# ==========================================
# CONFIG
# ==========================================

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UPLOAD_FOLDER = os.path.join(
    PROJECT_ROOT,
    "uploads",
    "faces"
)

EMBEDDING_FOLDER = os.path.join(
    PROJECT_ROOT,
    "embeddings"
)

os.makedirs(
    EMBEDDING_FOLDER,
    exist_ok=True
)

# ==========================================
# DATABASE
# ==========================================

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="facescan_db"
)

cursor = db.cursor()

# ==========================================
# INSIGHTFACE
# ==========================================

app = FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"]
)

app.prepare(
    ctx_id=0,
    det_size=(640,640)
)

# ==========================================
# ENROLL STUDENT
# ==========================================

def enroll_student(student_id):

    folder = os.path.join(
        UPLOAD_FOLDER,
        student_id
    )

    if not os.path.exists(folder):

        return False, "Folder not found"

    files = sorted(

        [

            f for f in os.listdir(folder)

            if f.lower().endswith(".jpg")

        ]

    )

    if len(files) == 0:

        return False, "No images found"

    embeddings = []

    print()

    print("==========================")
    print("Generating Embeddings")
    print(student_id)
    print("==========================")

    for file in files:

        image_path = os.path.join(
            folder,
            file
        )

        image = cv2.imread(image_path)

        if image is None:
            continue

        faces = app.get(image)

        if len(faces) == 0:
            continue

        embedding = faces[0].embedding

        embeddings.append(embedding)

        print("Processed:", file)
            # ==========================================
    # CHECK EMBEDDINGS
    # ==========================================

    if len(embeddings) == 0:

        return False, "No valid face embeddings generated."

    embeddings = np.array(embeddings)

    # Average all embeddings
    final_embedding = np.mean(embeddings, axis=0)

    # Normalize
    final_embedding = final_embedding / np.linalg.norm(final_embedding)

    # ==========================================
    # SAVE EMBEDDING
    # ==========================================

    embedding_filename = f"{student_id}.npz"

    embedding_path = os.path.join(
        EMBEDDING_FOLDER,
        embedding_filename
    )

    np.savez_compressed(
        embedding_path,
        embedding=final_embedding
    )

    print("Embedding Saved:", embedding_path)

    # ==========================================
    # UPDATE DATABASE
    # ==========================================

    sql = """

        UPDATE students

        SET

            face_registered = 1,

            embedding_file = %s,

            registered_at = NOW()

        WHERE student_id = %s

    """

    cursor.execute(

        sql,

        (

            embedding_filename,

            student_id

        )

    )

    db.commit()

    print("Database Updated.")

    print("==========================")
    print("ENROLLMENT COMPLETE")
    print("==========================")

    return True, "Enrollment Successful"


# ==========================================
# COMMAND LINE
# ==========================================

if __name__ == "__main__":

    import sys

    if len(sys.argv) < 2:

        print("Usage:")

        print("python -m ai.enrollment STUDENT_ID")

        exit()

    student_id = sys.argv[1]

    success, message = enroll_student(student_id)

    print(message)