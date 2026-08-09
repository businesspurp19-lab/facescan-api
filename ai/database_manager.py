from datetime import datetime
import os
import sqlite3


class LocalDatabaseManager:

  def __init__(self, db_name="facescan_local.db"):
    """Initializes the local SQLite data engine configuration."""
    self.db_name = db_name
    self.initialize_database()

  def get_connection(self):
    """Returns a thread-safe connection instance to the SQLite binary file."""
    return sqlite3.connect(self.db_name)

  def initialize_database(self):
    """Automatically creates structural tables if they do not already exist."""
    with self.get_connection() as conn:
      cursor = conn.cursor()

      # 1. Table for the local copy of the Instructor Load Matrix (Sync Cache)
      cursor.execute("""
                CREATE TABLE IF NOT EXISTS cached_loads (
                    load_id INTEGER PRIMARY KEY,
                    instructor_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    subject_code TEXT NOT NULL,
                    subject_name TEXT NOT NULL,
                    room TEXT NOT NULL,
                    schedule TEXT NOT NULL
                );
            """)

      # 2. Table for the local attendance collection queue (Biometric Scan Buffers)
      cursor.execute("""
                CREATE TABLE IF NOT EXISTS local_attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    student_name TEXT NOT NULL,
                    subject_id INTEGER NOT NULL,
                    instructor_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    is_synced INTEGER DEFAULT 0 -- 0 = Pending Upload, 1 = Successfully Synced
                );
            """)

      # 3. Table for local session parameters and security logs
      cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
            """)

      conn.commit()
      print("[SUCCESS] Local SQLite schema initialization complete.")

  def cache_instructor_loads(self, loads_list):
    """Temporarily stores active loads from the API sync for fully offline operation.

    Expects a list of dictionaries: [{'load_id':1, 'instructor_id':2, ...}]
    """
    with self.get_connection() as conn:
      cursor = conn.cursor()
      # Clear old cache to avoid operational conflicts
      cursor.execute("DELETE FROM cached_loads")

      for load in loads_list:
        cursor.execute(
            """
                    INSERT INTO cached_loads (load_id, instructor_id, subject_id, subject_code, subject_name, room, schedule)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
            (
                load["load_id"],
                load["instructor_id"],
                load["subject_id"],
                load["subject_code"],
                load["subject_name"],
                load["room"],
                load["schedule"],
            ),
        )

      conn.commit()
      print(
          f"[CACHE] Successfully cached {len(loads_list)} subject loads"
          " locally."
      )

  def log_local_attendance(
      self, student_id, student_name, subject_id, instructor_id, status
  ):
    """Inserts a raw verified biometric event into the offline buffer queue."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with self.get_connection() as conn:
      cursor = conn.cursor()
      cursor.execute(
          """
                INSERT INTO local_attendance (student_id, student_name, subject_id, instructor_id, timestamp, status, is_synced)
                VALUES (?, ?, ?, ?, ?, ?, 0)
            """,
          (
              student_id,
              student_name,
              subject_id,
              instructor_id,
              current_time,
              status,
          ),
      )
      conn.commit()
      print(f"[LOGGED] Offline transaction recorded for {student_id} - {status}")
      return True

  def get_pending_sync_records(self):
    """Retrieves all attendance rows that have not yet been uploaded to the online ecosystem."""
    with self.get_connection() as conn:
      conn.row_factory = sqlite3.Row
      cursor = conn.cursor()
      cursor.execute("SELECT * FROM local_attendance WHERE is_synced = 0")
      rows = cursor.fetchall()
      return [dict(row) for row in rows]

  def mark_records_as_synced(self, record_ids):
    """Updates the sync status flag after safe and successful API handshake validation."""
    if not record_ids:
      return
    with self.get_connection() as conn:
      cursor = conn.cursor()
      placeholders = ",".join("?" for _ in record_ids)
      cursor.execute(
          f"UPDATE local_attendance SET is_synced = 1 WHERE id IN"
          f" ({placeholders})",
          record_ids,
      )
      conn.commit()
      print(
          f"[SYNC STATE] Marked {len(record_ids)} records as synchronized"
          " successfully."
      )


if __name__ == "__main__":
  # Test script block for initialization validation
  db = LocalDatabaseManager()