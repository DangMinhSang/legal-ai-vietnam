"""Khởi chạy máy chủ Web Demo Hệ thống AI Phân tích & Hỗ trợ Xét xử Hình sự Việt Nam.

Chạy lệnh:
    python run_web.py
"""

from __future__ import annotations

import sys
import webbrowser
from pathlib import Path

# Đảm bảo mã hóa UTF-8 trên Windows Terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from rich.console import Console
from rich.panel import Panel

console = Console(legacy_windows=False)


def main() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]WEB DEMO - HỆ THỐNG AI XÉT XỬ HÌNH SỰ VIỆT NAM[/bold cyan]\n"
            "[white]Đại học Công nghệ Thông tin (UIT) - ĐHQG TP.HCM[/white]\n\n"
            "[bold green]✓ Đang khởi động Web Server tại: [underline]http://localhost:8000[/underline][/bold green]\n"
            "[yellow]• Giao diện gồm 2 khung nhập liệu: Thông tin cá nhân & Thông tin vụ án[/yellow]\n"
            "[cyan]• Swagger API Docs: [underline]http://localhost:8000/docs[/underline][/cyan]",
            border_style="cyan",
        )
    )

    try:
        # Tự động mở trình duyệt nếu có thể
        webbrowser.open("http://localhost:8000")
    except Exception:
        pass

    uvicorn.run("src.api.main:create_app", factory=True, host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
