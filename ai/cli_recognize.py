import sys
import json
import cv2
import traceback

try:
    from ai.recognize import recognize_face
except ImportError:
    from recognize import recognize_face

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            print(json.dumps({"student_id": None, "message": "No image path provided"}))
            sys.exit(0)

        image_path = sys.argv[1]
        frame = cv2.imread(image_path)

        if frame is None:
            print(json.dumps({"student_id": None, "message": "Failed to read image frame"}))
            sys.exit(0)

        # Ang recognize.py ay nagbabalik ng: student_id, confidence, bbox
        student_id, confidence, bbox = recognize_face(frame)

        if student_id:
            print(json.dumps({
                "status": "success",
                "student_id": str(student_id),
                "confidence": float(confidence) if confidence else 0.0
            }))
        else:
            print(json.dumps({
                "status": "unknown",
                "student_id": None,
                "confidence": float(confidence) if confidence else 0.0,
                "message": "Unrecognized face or below threshold"
            }))

    except Exception as e:
        print(json.dumps({
            "status": "error",
            "student_id": None,
            "message": str(e),
            "trace": traceback.format_exc()
        }))