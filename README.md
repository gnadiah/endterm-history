# 📚 Ôn tập Lịch Sử Việt Nam — TUI Quiz App

App TUI ôn trắc nghiệm Lịch Sử lớp 12, chạy trực tiếp trên terminal.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![TUI](https://img.shields.io/badge/TUI-Textual-green)

## ✨ Tính năng

- **Trắc nghiệm ABCD** — 113 câu từ Bài 10, Bài 11, Chủ đề 6
- **Trắc nghiệm Đúng/Sai** — 8 câu với ngữ liệu
- **Mix toàn bộ** — Làm trắc nghiệm trước, sau đó đúng/sai
- **Chọn theo bài** — Ôn riêng từng bài hoặc tất cả
- **Tráo câu hỏi** — Shuffle mỗi lần làm
- **Phản hồi tức thì** — Đáp án đúng/sai hiện ngay khi chọn
- **Làm lại câu sai** — Sau khi xem kết quả, ôn và làm lại chỉ câu sai
- **Lịch sử làm bài** — Tự động lưu từng lần làm
- **Hỗ trợ bàn phím + chuột**

## 🚀 Cài đặt

Yêu cầu: [uv](https://docs.astral.sh/uv/) và Python ≥ 3.10

```bash
# Clone repo
git clone <repo-url>
cd lich-su-quiz

# Cài đặt dependencies
uv sync
```

## ▶️ Chạy app

```bash
uv run quiz
# hoặc
uv run python -m quiz_app
```

## ⌨️ Phím tắt

| Màn hình           | Phím                | Chức năng              |
| ------------------ | ------------------- | ---------------------- |
| Menu               | `1` `2` `3` `4` `Q` | Chọn chế độ            |
| Chọn bài           | `0` `1` `2` `3`     | Chọn bài học           |
| Quiz (Trắc nghiệm) | `1` `2` `3` `4`     | Chọn A B C D           |
| Quiz (Đúng/Sai)    | `1` `2`             | Đúng / Sai             |
| Kết quả            | `R` `M`             | Làm lại câu sai / Menu |
| Mọi nơi            | `Esc`               | Quay lại               |

## 📁 Cấu trúc

```
├── pyproject.toml          # Project config (uv)
├── data/
│   ├── phan1_trac_nghiem.json   # 113 câu trắc nghiệm
│   └── phan2_dung_sai.json      # 8 câu đúng sai
├── quiz_app/
│   ├── __init__.py
│   ├── __main__.py         # Entry point
│   ├── app.py              # Main TUI app + screens
│   ├── data.py             # Data models + quiz session
│   ├── history.py          # History persistence
│   └── styles.tcss         # Textual CSS styles
```

## 📝 License

MIT
