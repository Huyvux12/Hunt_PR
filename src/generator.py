import os
import sys
import json
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.database import get_all_issues, get_stats

WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DATA_JSON_PATH = os.path.join(WEB_DIR, "data.json")
TRANSLATION_PROJECTS_PATH = os.path.join(DATA_DIR, "translation_projects.json")

def generate_static_data():
    os.makedirs(WEB_DIR, exist_ok=True)
    
    all_issues = get_all_issues(limit=300)
    stats = get_stats()
    
    # Lấy danh sách dự án dịch thuật Tiếng Việt
    translation_projects = []
    if os.path.exists(TRANSLATION_PROJECTS_PATH):
        try:
            with open(TRANSLATION_PROJECTS_PATH, "r", encoding="utf-8") as f:
                translation_projects = json.load(f)
        except Exception as e:
            print(f"[!] Không đọc được translation_projects.json: {e}")
            
    stats["total_translation_projects"] = len(translation_projects)

    # Lấy top 10 cho hôm nay dựa theo điểm Agent Score cao nhất
    top_10 = all_issues[:10]
    
    export_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": stats,
        "top_10": top_10,
        "issues": all_issues,
        "translation_projects": translation_projects
    }
    
    with open(DATA_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(export_payload, f, ensure_ascii=False, indent=2)
        
    print(f"[OK] Đã xuất {len(all_issues)} issues và Top 10 ra {DATA_JSON_PATH}")
