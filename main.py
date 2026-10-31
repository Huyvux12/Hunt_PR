import sys
import os

# Đảm bảo in tiếng Việt chuẩn trên Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.database import init_db, save_issue, record_crawl_log, get_stats
from src.crawler import crawl_issues
from src.generator import generate_static_data

def main():
    print("=" * 60)
    print("🚀 BẮT ĐẦU QUY TRÌNH SĂN ISSUE (HUNT-PR PIPELINE)")
    print("=" * 60)

    # 1. Khởi tạo Database SQLite
    init_db()

    # 2. Quét Issue với các tiêu chuẩn thông minh
    target_issues = 15
    print(f"\n[*] Đang quét các Issue tiềm năng từ GitHub (Mục tiêu: {target_issues} issues mới)...")
    
    try:
        crawled_issues, scanned_total = crawl_issues(target_new_issues=target_issues)
    except Exception as e:
        print(f"[X] Lỗi trong quá trình quét: {e}")
        record_crawl_log(0, 0, status="error", message=str(e))
        return

    # 3. Lưu vào Database (tự động loại bỏ trùng lặp)
    new_added = 0
    updated = 0
    for issue in crawled_issues:
        is_new = save_issue(issue)
        if is_new:
            new_added += 1
        else:
            updated += 1

    record_crawl_log(scanned_total, new_added, status="success")
    print(f"\n[+] Kết quả quét:")
    print(f"    - Tổng issue đã duyệt qua: {scanned_total}")
    print(f"    - Issue mới thêm vào DB: {new_added}")
    print(f"    - Issue đã có sẵn (cập nhật): {updated}")

    # 4. Xuất dữ liệu cho Web tĩnh GitHub Pages
    print("\n[*] Đang sinh dữ liệu tĩnh web/data.json...")
    generate_static_data()

    # 5. In bảng thống kê
    stats = get_stats()
    print("\n" + "=" * 60)
    print("📊 THỐNG KÊ TOÀN BỘ HỆ THỐNG:")
    print(f"    - Tổng số Issue trong DB: {stats['total_issues']}")
    print(f"    - Số Issue merge cực nhanh (<= 24h): {stats['fast_merge_count']}")
    print(f"    - Số Repo uy tín đã quét: {stats['total_repos']}")
    print("=" * 60)
    print("🎉 Hoàn tất quy trình!")

if __name__ == "__main__":
    main()
