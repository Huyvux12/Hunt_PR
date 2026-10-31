# 🎯 Hunt-PR: Automated Daily 10-PR Pipeline for AI Coding Agents

Hệ thống tự động săn lùng và tuyển chọn các GitHub Issue chất lượng cao mỗi giờ, phục vụ cho quy trình cày **100 PRs/tuần bằng AI Agent (Claude Code, Antigravity, Aider)** theo phong cách của Boris Cherny (tác giả Claude Code tại Anthropic).

---

## 🌟 Tính Năng Nổi Bật

1. **Bộ lọc thông minh chuyên dụng cho AI Agent (Agent-Friendly)**:
   - **Loại bỏ bot PR**: Tự động lọc Dependabot/Renovate để tính chính xác tốc độ merge của người thật.
   - **Kiểm tra độ "sống" của repo**: Chỉ lấy repo có PR do người thật merge trong 30 ngày qua (tránh repo đóng băng).
   - **Ưu tiên Issue có Code/Traceback**: Nhận diện dấu ` ``` ` và error log để AI định vị file cần sửa nhanh nhất.
   - **Tối ưu tỷ lệ duyệt**: Ưu tiên các nhãn `good first issue`, `documentation`, `tests`, `typo`.
2. **Lưu trữ SQLite tự động**: Tránh trùng lặp khi quét nhiều lần, lưu lịch sử tiến độ.
3. **Dashboard Web tĩnh GitHub Pages**:
   - Giao diện Dark Mode hiện đại, responsive.
   - Nút **"Copy Prompt Claude Code"** 1-click (được chuẩn hóa sẵn prompt giải quyết issue, viết test, commit).
   - Nút **"Copy Git Worktree"** để checkout branch nhanh chóng.
4. **Tự động hóa 100% qua GitHub Actions**: Tự crawl mỗi 1 giờ, lưu DB và deploy trực tiếp lên GitHub Pages.

---

## 📁 Cấu Trúc Dự Án

```text
hunt-pr/
├── .github/workflows/
│   └── crawl_and_deploy.yml   # Workflow GitHub Actions chạy định kỳ 1h/lần
├── src/
│   ├── crawler.py             # Thu thập API GitHub, lọc bot, chấm điểm Agent Score
│   ├── database.py            # Quản lý SQLite DB, deduplication
│   └── generator.py           # Xuất dữ liệu ra web/data.json
├── web/
│   ├── index.html             # Giao diện Dashboard (Tailwind CSS)
│   └── data.json              # Dữ liệu tĩnh cho GitHub Pages
├── data/
│   └── issues.db              # Cơ sở dữ liệu SQLite
├── main.py                    # File thực thi chính
├── pyproject.toml / requirements.txt
└── README.md
```

---

## 🚀 Hướng Dẫn Thiết Lập Đẩy Lên GitHub

### Bước 1: Khởi tạo Git và đẩy lên Repository của bạn

```bash
git init
git add .
git commit -m "feat: initial hunt-pr pipeline"
git branch -M main
git remote add origin https://github.com/<username>/<repo-name>.git
git push -u origin main
```

### Bước 2: Bật tính năng GitHub Pages

1. Vào repo trên GitHub: **Settings** -> **Pages**.
2. Tại mục **Build and deployment** -> **Source**: Chọn **GitHub Actions**.

### Bước 3 (Khuyến khích): Thêm GitHub Token để tăng giới hạn API

Mặc định GitHub Actions cung cấp token sẵn có (`GITHUB_TOKEN`), nhưng nếu muốn quét thoải mái (5,000 requests/giờ):
1. Vào **Settings** -> **Secrets and variables** -> **Actions**.
2. Nhấn **New repository secret**.
3. Name: `CUSTOM_PAT` (Personal Access Token tạo tại *GitHub Settings -> Developer settings -> Personal access tokens (classic)* với quyền `public_repo`).
4. Value: dán token của bạn vào.

---

## 💻 Chạy Thử Nghiệm Tại Local

```bash
# Sử dụng uv
uv run main.py

# Hoặc dùng Python thuần (không cần cài thêm thư viện ngoài)
python main.py
```

Sau khi chạy xong, bạn có thể mở trực tiếp file `web/index.html` trên trình duyệt để trải nghiệm Dashboard!
