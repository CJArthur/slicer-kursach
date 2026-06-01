import sqlite3
from datetime import datetime
from pathlib import Path
import os


DB_PATH = Path(os.path.expanduser("~")) / ".video_subtitler" / "history.db"
DB_PATH.parent.mkdir(exist_ok=True)

# Для открытия нового соединения
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # для удобного обращения к колонкам по имени
    return conn

# Вызывается при старте приложения
def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                output TEXT NOT NULL,
                preset TEXT,
                position TEXT,
                parts INTEGER,
                status TEXT,
                error_msg TEXT,
                created_at TEXT
            )
        """)

# Сохранение данных обработки
def save_record(source, output, preset, position,
                parts, status, error_msg = None):
    
    with _connect() as conn:
        conn.execute("""
            INSERT INTO history
                (source, output, preset, position, parts, status, error_msg, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)

        """, (source, output, preset, position,
              parts, status, error_msg, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
# Запрос истории из базы данных
def get_history(limit = 70):
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM history ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()

        return rows