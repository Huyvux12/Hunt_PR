import os
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def load_env():
    """Tự động đọc file .env ở thư mục gốc nếu có (không cần thư viện ngoài)"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        except Exception as e:
            print(f"[!] Không đọc được file .env: {e}")

load_env()

def get_token():
    return os.getenv("CUSTOM_PAT", "").strip() or os.getenv("GITHUB_TOKEN", "").strip()

MIN_STARS = int(os.getenv("MIN_STARS", "100"))

def github_api(url):
    """Thực hiện request tới GitHub API với Authentication nếu có token"""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "100-PR-Agent-Hunter"
    }
    token = get_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 403:
            reset_ts = e.headers.get("x-ratelimit-reset")
            reset_info = f" (Reset lúc {datetime.fromtimestamp(int(reset_ts)).strftime('%H:%M:%S')})" if reset_ts else ""
            print(f"[CẢNH BÁO RATE LIMIT 403] Hết hạn ngạch API không có token{reset_info}. Hãy thêm GITHUB_TOKEN để có 5,000 req/h!")
        else:
            print(f"[LỖI API] HTTP {e.code} trên URL: {url}")
        return None
    except Exception as e:
        print(f"[LỖI KẾT NỐI] {e} trên URL: {url}")
        return None

def analyze_repo_pulls(repo_full_name, cache={}):
    """
    Phân tích tốc độ merge PR của người thật (loại bỏ Bot) trong 30 ngày gần đây
    """
    if repo_full_name in cache:
        return cache[repo_full_name]

    pulls_url = f"https://api.github.com/repos/{repo_full_name}/pulls?state=closed&sort=updated&direction=desc&per_page=15"
    pulls = github_api(pulls_url)
    if not pulls or not isinstance(pulls, list):
        cache[repo_full_name] = ("Không lấy được PRs", -1, False)
        return cache[repo_full_name]

    now = datetime.now(timezone.utc)
    human_merged_times = []
    has_recent_human_merge = False

    for pr in pulls:
        merged_at_str = pr.get("merged_at")
        if not merged_at_str:
            continue

        # Lọc bỏ bot (Dependabot, Renovate, v.v.)
        user = pr.get("user", {}) or {}
        user_type = user.get("type", "")
        user_login = user.get("login", "").lower()
        if user_type == "Bot" or "[bot]" in user_login or "dependabot" in user_login:
            continue

        merged_time = datetime.fromisoformat(merged_at_str.replace("Z", "+00:00"))
        created_time = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))

        # Phải có PR được merge trong vòng 30 ngày gần đây
        if (now - merged_time).total_seconds() <= 30 * 86400:
            has_recent_human_merge = True

        duration_hours = (merged_time - created_time).total_seconds() / 3600
        human_merged_times.append(duration_hours)

    if not has_recent_human_merge or not human_merged_times:
        cache[repo_full_name] = ("❌ Repo đóng băng (Không có PR người thật merge gần đây)", -1, False)
        return cache[repo_full_name]

    avg_hours = sum(human_merged_times) / len(human_merged_times)
    if avg_hours <= 24:
        verdict = f"🔥 CỰC DỄ (TB {avg_hours:.1f}h là merge)"
    elif avg_hours <= 72:
        verdict = f"✅ DỄ (TB {avg_hours/24:.1f} ngày là merge)"
    else:
        verdict = f"⚠️ TRUNG BÌNH (TB {avg_hours/24:.1f} ngày)"

    cache[repo_full_name] = (verdict, round(avg_hours, 1), True)
    return cache[repo_full_name]

def calculate_agent_score(issue_item, stars, avg_hours):
    """Tính điểm độ khả thi cho AI Coding Agent (0 - 100 điểm)"""
    score = 0
    body = issue_item.get("body") or ""
    labels = [l.get("name", "").lower() for l in issue_item.get("labels", [])]

    # 1. Có code mẫu hoặc traceback lỗi trong mô tả
    if "```" in body or "traceback" in body.lower() or "error" in body.lower():
        score += 25

    # 2. Nhãn thân thiện (good first issue, docs, tests, bug...)
    friendly_labels = ["good first issue", "documentation", "docs", "typo", "tests", "help wanted", "easy", "beginner"]
    if any(fl in " ".join(labels) for fl in friendly_labels):
        score += 25

    # 3. Vận tốc merge PR của repo
    if 0 < avg_hours <= 24:
        score += 25
    elif 0 < avg_hours <= 72:
        score += 15

    # 4. Độ dài mô tả issue súc tích (100 - 3500 ký tự)
    if 100 <= len(body) <= 3500:
        score += 15

    # 5. Repo uy tín
    if stars >= 500:
        score += 10

    return min(score, 100)

def crawl_issues(target_new_issues=15):
    """
    Chiến lược quét kết hợp:
    1. Quét tìm các Repository uy tín (> 500 stars, active) -> Lấy danh sách Issue từ repo
    2. Quét tìm Issue toàn cục theo nhãn thân thiện
    """
    crawled_issues = []
    scanned_total = 0

    # Chiến lược 1: Quét các Repositories active và uy tín trước (tiết kiệm API calls nhất)
    print("[*] Chiến lược 1: Khám phá các Repo uy tín (> 500 Stars, Active)...")
    repo_search_url = "https://api.github.com/search/repositories?q=stars:>500+language:python+archived:false&sort=updated&per_page=10"
    repo_data = github_api(repo_search_url)

    if repo_data and "items" in repo_data:
        for repo_item in repo_data["items"]:
            if len(crawled_issues) >= target_new_issues:
                break

            repo_name = repo_item["full_name"]
            stars = repo_item.get("stargazers_count", 0)

            # Lấy issues mở của repo này
            issues_url = f"https://api.github.com/repos/{repo_name}/issues?state=open&per_page=10"
            issues_list = github_api(issues_url)
            if not issues_list or not isinstance(issues_list, list):
                continue

            verdict, avg_hours, is_valid = analyze_repo_pulls(repo_name)
            if not is_valid:
                continue

            for item in issues_list:
                # Bỏ qua pull requests
                if "pull_request" in item or item.get("assignee") is not None:
                    continue

                scanned_total += 1
                body = item.get("body") or ""
                score = calculate_agent_score(item, stars, avg_hours)
                labels_list = [l.get("name", "") for l in item.get("labels", [])]

                crawled_issues.append({
                    "id": item["id"],
                    "repo_name": repo_name,
                    "repo_stars": stars,
                    "repo_url": repo_item["html_url"],
                    "issue_number": item["number"],
                    "title": item["title"],
                    "body": body,
                    "html_url": item["html_url"],
                    "comments_count": item.get("comments", 0),
                    "labels": labels_list,
                    "language": repo_item.get("language") or "Python",
                    "created_at": item["created_at"],
                    "updated_at": item["updated_at"],
                    "merge_velocity_hours": avg_hours,
                    "merge_verdict": verdict,
                    "agent_score": score,
                    "has_code_block": ("```" in body)
                })

    # Chiến lược 2: Quét Issue Search toàn cục nếu chưa đủ
    if len(crawled_issues) < target_new_issues:
        print("[*] Chiến lược 2: Quét Global Issue Search...")
        issue_query = 'is:open is:issue no:assignee comments:<=2 label:"good first issue","documentation" sort:updated-desc'
        search_url = f"https://api.github.com/search/issues?q={urllib.parse.quote(issue_query)}&per_page=20"
        global_issues = github_api(search_url)

        if global_issues and "items" in global_issues:
            for item in global_issues["items"]:
                if len(crawled_issues) >= target_new_issues:
                    break
                if "pull_request" in item:
                    continue

                repo_name = "/".join(item["repository_url"].split("/")[-2:])
                repo_info = github_api(f"https://api.github.com/repos/{repo_name}")
                if not repo_info:
                    continue
                stars = repo_info.get("stargazers_count", 0)
                if stars < MIN_STARS:
                    continue

                verdict, avg_hours, is_valid = analyze_repo_pulls(repo_name)
                if not is_valid:
                    continue

                scanned_total += 1
                body = item.get("body") or ""
                score = calculate_agent_score(item, stars, avg_hours)
                labels_list = [l.get("name", "") for l in item.get("labels", [])]

                crawled_issues.append({
                    "id": item["id"],
                    "repo_name": repo_name,
                    "repo_stars": stars,
                    "repo_url": f"https://github.com/{repo_name}",
                    "issue_number": item["number"],
                    "title": item["title"],
                    "body": body,
                    "html_url": item["html_url"],
                    "comments_count": item.get("comments", 0),
                    "labels": labels_list,
                    "language": repo_info.get("language") or "Python",
                    "created_at": item["created_at"],
                    "updated_at": item["updated_at"],
                    "merge_velocity_hours": avg_hours,
                    "merge_verdict": verdict,
                    "agent_score": score,
                    "has_code_block": ("```" in body)
                })

    return crawled_issues, scanned_total

def sync_closed_issues(max_check=25):
    """
    Tự động kiểm tra các issue cũ trong DB:
    Nếu issue đã bị đóng hoặc đã được merge PR trên GitHub -> cập nhật status = 'closed' trong DB.
    """
    from src.database import get_open_issues, mark_issue_closed
    
    open_issues = get_open_issues(limit=max_check)
    if not open_issues:
        return 0
        
    closed_count = 0
    print(f"\n[*] Đang kiểm tra trạng thái {len(open_issues)} issues trong DB xem có issue nào đã được giải quyết...")
    
    for issue in open_issues:
        repo_name = issue["repo_name"]
        issue_number = issue["issue_number"]
        issue_url = f"https://api.github.com/repos/{repo_name}/issues/{issue_number}"
        
        data = github_api(issue_url)
        if not data:
            continue
            
        state = data.get("state")
        if state == "closed":
            mark_issue_closed(issue["id"])
            closed_count += 1
            print(f"    [✔ ĐÃ GIẢI QUYẾT] #{issue_number} ({repo_name}) đã đóng trên GitHub -> Ẩn khỏi danh sách active!")

    return closed_count
