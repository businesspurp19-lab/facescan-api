import os

# ==========================================
# PROJECT PATHS
# ==========================================
# Kasalukuyang lokasyon ng config.py (loob ng ai/ folder)
AI_DIR = os.path.dirname(os.path.abspath(__file__))

# Ang root folder ng buong web application mo
PROJECT_ROOT = os.path.dirname(AI_DIR)

# Dito ise-save ang raw faces ng estudyante
UPLOAD_FOLDER = os.path.join(
    PROJECT_ROOT,
    "uploads",
    "faces"
)

# Dito ise-save ang .npy trained embedding vector file
EMBEDDING_FOLDER = os.path.join(
    AI_DIR,
    "embeddings"
)

# ==========================================
# AI ENGINE SETTINGS
# ==========================================
CAPTURE_LIMIT = 1
RECOGNITION_THRESHOLD = 0.35

# ==========================================
# AUTO-CREATE REQUIRED FOLDERS
# ==========================================
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    print(f"[CONFIG] Created face uploads directory at: {UPLOAD_FOLDER}")

if not os.path.exists(EMBEDDING_FOLDER):
    os.makedirs(EMBEDDING_FOLDER, exist_ok=True)
    print(f"[CONFIG] Created system embeddings directory at: {EMBEDDING_FOLDER}")