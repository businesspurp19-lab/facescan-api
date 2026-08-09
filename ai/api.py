from datetime import datetime
import os
import cv2
import base64
import numpy as np
import mysql.connector
import traceback

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ai.config import UPLOAD_FOLDER
from ai.detector import detect_face
from ai.embedding import generate_embedding
from ai.database_manager import LocalDatabaseManager

try:
    from ai.recognize import recognize_face, refresh
except ImportError:
    from ai.recognize import refresh
    def recognize_face(*args, **kwargs):
        return None, 0.0, None

app = FastAPI(
    title="FaceScan"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Local SQLite Database Manager for offline-first operations
db_manager = LocalDatabaseManager("facescan_local.db")

class FrameData(BaseModel):
    student_id: str
    image: str

class RecognitionData(BaseModel):
    image: str

class EmbeddingData(BaseModel):
    student_id: str

class AttendanceData(BaseModel):
    student_id: str
    student_name: str
    subject_id: int
    instructor_id: int
    status: str

def format_student_id(raw_id: str) -> str:
    clean_id = raw_id.replace("-", "").strip()
    if len(clean_id) == 7:
        return f"{clean_id[:2]}-{clean_id[2:3]}-{clean_id[3:]}"
    return raw_id

def execute_embedding_and_sync(student_id: str):
    """
    Finalizes embedding generation, refreshes the AI model, 
    updates the MySQL database to set face_registered = 1,
    saves the face image path, and inserts/updates the record in the face_embeddings table.
    """
    try:
        print(f"\n[PIPELINE] >>> Starting embedding & DB registration for: '{student_id}'")
        
        # 1. Generate embedding using embedding.py
        generate_embedding(student_id)
        print(f"[PIPELINE] >>> generate_embedding finished for: '{student_id}'")
        
        # 2. Refresh recognition system
        refresh()
        print(f"[PIPELINE] >>> refresh() finished.")
        
        # 3. MySQL Connection to update face_registered, face_image, and insert into face_embeddings
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="facescan_db"
        )
        cursor = connection.cursor()
        
        embedding_filename = f"{student_id}.npy"
        face_image_path = f"uploads/faces/{student_id}/1.jpg"
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # A. Update face_registered = 1, face_image, registered_at, and embedding_file in students table
        update_query = """
            UPDATE students 
            SET face_registered = 1, 
                face_image = %s, 
                registered_at = %s, 
                embedding_file = %s 
            WHERE student_id = %s OR student_id = REPLACE(%s, '-', '')
        """
        cursor.execute(update_query, (face_image_path, current_time, embedding_filename, student_id, student_id))
        
        # B. Insert or update record in face_embeddings table if it exists in schema
        try:
            insert_embedding_query = """
                INSERT INTO face_embeddings (student_id, embedding_file) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE embedding_file = VALUES(embedding_file)
            """
            cursor.execute(insert_embedding_query, (student_id, embedding_filename))
        except Exception as db_err:
            print(f"[PIPELINE NOTICE] face_embeddings table update skipped or not used: {db_err}")
        
        connection.commit()
        print(f"[PIPELINE] Rows affected in students: {cursor.rowcount}")
        
        cursor.close()
        connection.close()
        
        print(f"[PIPELINE] >>> Database updated successfully: '{student_id}' is registered.\n")
        return True
        
    except Exception as e:
        print(f"\n[PIPELINE ERROR DETAILED]:")
        traceback.print_exc()
        return False

@app.get("/")
def home():
    return {
        "status": "running",
        "message": "FaceScan API Running"
    }

@app.get("/generate_embedding/{student_id}")
def create_embedding(student_id: str):
    try:
        formatted_id = format_student_id(student_id)
        success = execute_embedding_and_sync(formatted_id)
        
        if success:
            return {
                "success": True,
                "message": "Embedding generated and database synced successfully.",
                "student_id": formatted_id
            }
        else:
            return {
                "success": False,
                "message": "Error occurred during embedding pipeline execution."
            }
    except Exception as e:
        print("EMBEDDING ERROR:", e)
        return {
            "success": False,
            "message": str(e)
        }

@app.post("/upload_frame")
def upload_frame(data: FrameData):
    try:
        formatted_id = format_student_id(data.student_id)
        print(f"[API DEBUG] Processing single-shot registration for: '{formatted_id}'")

        student_folder = os.path.join(
            UPLOAD_FOLDER,
            formatted_id
        )

        os.makedirs(
            student_folder,
            exist_ok=True
        )

        # Decode base64 image from frontend
        image = data.image.split(",")[1] if "," in data.image else data.image
        image_bytes = base64.b64decode(image)
        np_array = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if frame is None:
            return {
                "success": False,
                "message": "Invalid image received."
            }

        # Detect face using AI detector
        face, message = detect_face(frame)

        if face is None:
            return {
                "success": False,
                "message": f"No face detected: {message}"
            }

        # Save the captured face as 1.jpg inside the student's folder
        filename = os.path.join(
            student_folder,
            "1.jpg"
        )
        cv2.imwrite(filename, face)

        # Immediately execute embedding generation and database sync
        success = execute_embedding_and_sync(formatted_id)

        if success:
            return {
                "success": True,
                "complete": True,
                "registered": True,
                "count": 1,
                "message": "Face registration completed and database updated successfully!",
                "student_id": formatted_id
            }
        else:
            return {
                "success": False,
                "message": "Face captured, but failed to generate embedding or update database."
            }

    except Exception as e:
        print(f"[API ERROR]: {str(e)}")
        traceback.print_exc()
        return {
            "success": False,
            "message": str(e)
        }

@app.post("/recognize")
def api_recognize(data: RecognitionData):
    """
    Endpoint na tumatanggap ng live video frames galing sa frontend para sa attendance recognition.
    """
    try:
        image_data = data.image
        if not image_data:
            return {"status": "unknown", "message": "No image data provided."}

        # Alisin ang base64 data URI header kung meron man
        if "," in image_data:
            image_data = image_data.split(",")[1]

        image_bytes = base64.b64decode(image_data)
        np_array = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if frame is None:
            return {"status": "unknown", "message": "Failed to decode image frame."}

        # I-run ang recognition engine
        student_id, confidence, bbox = recognize_face(frame)

        if student_id is not None:
            return {
                "status": "success",
                "student_id": student_id,
                "confidence": confidence
            }
        else:
            return {
                "status": "unknown",
                "message": "No face detected or unrecognized person."
            }

    except Exception as e:
        print(f"[RECOGNIZE ERROR]: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.post("/log_attendance", status_code=status.HTTP_201_CREATED)
def api_log_attendance(data: AttendanceData):
    """
    Receives verified attendance and saves it to the local SQLite queue.
    """
    try:
        success = db_manager.log_local_attendance(
            student_id=data.student_id,
            student_name=data.student_name,
            subject_id=data.subject_id,
            instructor_id=data.instructor_id,
            status=data.status
        )
        if success:
            return {"status": "success", "message": f"Attendance logged locally for {data.student_id}"}
        raise HTTPException(status_code=500, detail="Failed to write local attendance log.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pending-sync-records")
def get_pending_sync():
    """Retrieves attendance logs that have not yet been synced online."""
    try:
        records = db_manager.get_pending_sync_records()
        return {"status": "success", "count": len(records), "data": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mark-records-synced")
def mark_synced(record_ids: list[int]):
    """Marks uploaded attendance logs as synced."""
    try:
        db_manager.mark_records_as_synced(record_ids)
        return {"status": "success", "message": f"Marked {len(record_ids)} records as synced."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))