import sqlite3
import json
import os
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "issues.db")

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY,
        repo_name TEXT NOT NULL,
        repo_stars INTEGER DEFAULT 0,
        repo_url TEXT NOT NULL,
        issue_number INTEGER NOT NULL,
        title TEXT NOT NULL,
        body TEXT DEFAULT '',
        html_url TEXT NOT NULL UNIQUE,
        comments_count INTEGER DEFAULT 0,
        labels TEXT DEFAULT '[]',
        language TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        merge_velocity_hours REAL DEFAULT -1,
        merge_verdict TEXT DEFAULT '',
        agent_score INTEGER DEFAULT 0,
        has_code_block INTEGER DEFAULT 0,
        crawled_at TEXT NOT NULL,
        status TEXT DEFAULT 'new'
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crawl_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        scanned_count INTEGER DEFAULT 0,
        added_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'success',
        message TEXT DEFAULT ''
    )
    """)
    
    conn.commit()
    conn.close()

def save_issue(issue_data):
    """Lưu hoặc cập nhật một issue vào DB. Trả về True nếu thêm mới, False nếu đã tồn tại."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat() + "Z"
    
    # Kiểm tra xem issue đã tồn tại chưa
    cursor.execute("SELECT id FROM issues WHERE html_url = ?", (issue_data["html_url"],))
    exists = cursor.fetchone() is not None
    
    labels_json = json.dumps(issue_data.get("labels", []), ensure_ascii=False)
    
    cursor.execute("""
    INSERT INTO issues (
        id, repo_name, repo_stars, repo_url, issue_number, title, body,
        html_url, comments_count, labels, language, created_at, updated_at,
        merge_velocity_hours, merge_verdict, agent_score, has_code_block,
        crawled_at, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(html_url) DO UPDATE SET
        repo_stars = excluded.repo_stars,
        comments_count = excluded.comments_count,
        labels = excluded.labels,
        updated_at = excluded.updated_at,
        merge_velocity_hours = excluded.merge_velocity_hours,
        merge_verdict = excluded.merge_verdict,
        agent_score = excluded.agent_score
    """, (
        issue_data["id"],
        issue_data["repo_name"],
        issue_data.get("repo_stars", 0),
        issue_data["repo_url"],
        issue_data["issue_number"],
        issue_data["title"],
        issue_data.get("body", ""),
        issue_data["html_url"],
        issue_data.get("comments_count", 0),
        labels_json,
        issue_data.get("language", ""),
        issue_data["created_at"],
        issue_data["updated_at"],
        issue_data.get("merge_velocity_hours", -1),
        issue_data.get("merge_verdict", ""),
        issue_data.get("agent_score", 0),
        1 if issue_data.get("has_code_block") else 0,
        now,
        "new"
    ))
    
    conn.commit()
    conn.close()
    return not exists

def record_crawl_log(scanned_count, added_count, status="success", message=""):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat() + "Z"
    cursor.execute("""
    INSERT INTO crawl_history (timestamp, scanned_count, added_count, status, message)
    VALUES (?, ?, ?, ?, ?)
    """, (now, scanned_count, added_count, status, message))
    conn.commit()
    conn.close()

def mark_issue_closed(issue_id):
    """Cập nhật trạng thái issue đã được sửa / đóng trên GitHub"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat() + "Z"
    cursor.execute("UPDATE issues SET status = 'closed', updated_at = ? WHERE id = ?", (now, issue_id))
    conn.commit()
    conn.close()

def get_open_issues(limit=50):
    """Lấy danh sách các issue đang ở trạng thái mở trong DB để kiểm tra trạng thái"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, repo_name, issue_number, title, html_url 
    FROM issues 
    WHERE status != 'closed' 
    ORDER BY updated_at ASC 
    LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_issues(limit=200, only_active=True):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if only_active:
        cursor.execute("""
        SELECT * FROM issues 
        WHERE status != 'closed'
        ORDER BY agent_score DESC, crawled_at DESC 
        LIMIT ?
        """, (limit,))
    else:
        cursor.execute("""
        SELECT * FROM issues 
        ORDER BY agent_score DESC, crawled_at DESC 
        LIMIT ?
        """, (limit,))
        
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        d = dict(row)
        try:
            d["labels"] = json.loads(d["labels"])
        except Exception:
            d["labels"] = []
        results.append(d)
    return results

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM issues")
    total_issues = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM issues WHERE status != 'closed'")
    active_issues = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM issues WHERE status = 'closed'")
    closed_issues = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM issues WHERE status != 'closed' AND merge_velocity_hours > 0 AND merge_velocity_hours <= 24")
    fast_merge_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT repo_name) FROM issues WHERE status != 'closed'")
    total_repos = cursor.fetchone()[0]
    
    cursor.execute("SELECT timestamp FROM crawl_history ORDER BY id DESC LIMIT 1")
    last_crawl_row = cursor.fetchone()
    last_crawl = last_crawl_row[0] if last_crawl_row else None
    
    conn.close()
    return {
        "total_issues": total_issues,
        "active_issues": active_issues,
        "closed_issues": closed_issues,
        "fast_merge_count": fast_merge_count,
        "total_repos": total_repos,
        "last_crawl": last_crawl
    }
