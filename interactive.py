"""Giao diện Tương tác Terminal với 2 Khung Nhập Liệu Duy Nhất:
1. Thông tin cá nhân (có thể nhiều người gồm bị cáo và bị hại)
2. Thông tin vụ án

Chạy lệnh:
    python interactive.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Đảm bảo UTF-8 trên Windows Terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Tắt các log nền
import logging
import warnings
warnings.filterwarnings("ignore")
try:
    from loguru import logger
    logger.remove()
except ImportError:
    pass
logging.getLogger().setLevel(logging.ERROR)

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from src.db.database import AsyncSessionLocal
from src.orchestration.case_parser import parse_two_inputs
from src.orchestration.orchestrator import CaseAnalysisOrchestrator

console = Console(legacy_windows=False)

DEFAULT_PERSONAL = (
    "- Bị cáo: Nguyễn Văn An (SN 1995), chưa có tiền án tiền sự.\n"
    "- Bị hại: Trần Quốc Bình (SN 1998), tỷ lệ tổn hại sức khỏe 35%."
)

DEFAULT_CASE = (
    "Khoảng 21 giờ ngày 15/04/2023, do mâu thuẫn bộc phát tại quán nước, bị cáo Nguyễn Văn An "
    "đã dùng dao bấm (hung khí nguy hiểm) đâm vào ngực anh Trần Quốc Bình làm anh Bình bị tổn hại 35% sức khỏe. "
    "Sau khi gây án, bị cáo đã thành khẩn khai báo, tự nguyện bồi thường 50.000.000 đồng và được gia đình bị hại xin giảm nhẹ hình phạt."
)


def get_multiline_input(prompt_title: str, default_text: str) -> str:
    """Thu thập nhập liệu từ người dùng, hỗ trợ bấm Enter để dùng mẫu."""
    console.print(Panel(f"[bold cyan]{prompt_title}[/bold cyan]\n[dim](Nhấn Enter trực tiếp để dùng dữ liệu mẫu bên dưới, hoặc nhập nội dung của bạn)[/dim]", border_style="cyan"))
    console.print(f"[dim]Dữ liệu mẫu gợi ý:[/dim]\n[yellow]{default_text}[/yellow]\n")

    val = Prompt.ask("[bold green]Nhập nội dung[/bold green] (Enter = Dùng mẫu trên)", default="USE_DEFAULT")
    if val == "USE_DEFAULT" or not val.strip():
        return default_text
    return val.strip()


async def main() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]HỆ THỐNG AI PHÂN TÍCH & DỰ ĐOÁN XÉT XỬ HÌNH SỰ VIỆT NAM[/bold cyan]\n"
            "[white]Đại học Công nghệ Thông tin (UIT) - ĐHQG TP.HCM[/white]\n"
            "[green]Chế độ nhập liệu 2 Khung: Thông tin cá nhân & Thông tin vụ án[/green]",
            border_style="cyan",
        )
    )

    # 1. Khung nhập 1: Thông tin cá nhân
    personal_info = get_multiline_input(
        "KHUNG 1: THÔNG TIN CÁ NHÂN (Bị cáo, Bị hại - có thể nhiều người)",
        DEFAULT_PERSONAL,
    )

    console.print()

    # 2. Khung nhập 2: Thông tin vụ án
    case_info = get_multiline_input(
        "KHUNG 2: THÔNG TIN VỤ ÁN (Diễn biến hành vi, công cụ, hậu quả, tình tiết)",
        DEFAULT_CASE,
    )

    console.print("\n[bold magenta]Đang phân tích 2 khung dữ liệu và kích hoạt hệ thống...[/bold magenta]\n")

    # Phân tích cấu trúc từ 2 khung
    parsed = parse_two_inputs(personal_info, case_info)

    orchestrator = CaseAnalysisOrchestrator()

    async with AsyncSessionLocal() as session:
        result = await orchestrator.analyze_case(
            case_description=parsed.combined_description,
            incident_date=parsed.incident_date,
            judgment_date=parsed.judgment_date,
            session=session,
            input_features=parsed.features,
        )

    # Bảng 1: Đương sự & Tình tiết
    t_parties = Table(title="[bold yellow]1. ĐƯƠNG SỰ & TÌNH TIẾT ĐÃ NHẬN DIỆN[/bold yellow]")
    t_parties.add_column("Vai trò", style="magenta", width=12)
    t_parties.add_column("Họ và tên / Chi tiết", style="white")
    t_parties.add_column("Tiền án", style="cyan", justify="right")
    for p in parsed.parties:
        t_parties.add_row(p.role, p.name + (f" ({p.details})" if p.details != p.name else ""), str(p.prior_convictions))
    console.print(t_parties)

    # Bảng 2: Tình tiết tăng nặng / giảm nhẹ
    t_factors = Table(title="\n[bold yellow]2. TÌNH TIẾT ĐIỀU 51 / ĐIỀU 52 BLHS[/bold yellow]")
    t_factors.add_column("Loại tình tiết", style="cyan", width=20)
    t_factors.add_column("Chi tiết áp dụng", style="white")
    agg_str = "\n".join([f"• {a}" for a in parsed.aggravating_factors]) or "Không có"
    mit_str = "\n".join([f"✓ {m}" for m in parsed.mitigating_factors]) or "Không có"
    t_factors.add_row("Tăng nặng (Điều 52)", agg_str)
    t_factors.add_row("Giảm nhẹ (Điều 51)", mit_str)
    t_factors.add_row("Tội danh truy tố", f"{parsed.detected_crime_name} (Điều {', '.join(parsed.detected_articles)} BLHS)")
    console.print(t_factors)

    # Bảng 3: Suy luận thời gian & Án lệ
    t_temp = Table(title="\n[bold yellow]3. SUY LUẬN THỜI GIAN (Đ.7 BLHS) & ÁN LỆ TANDTC[/bold yellow]")
    t_temp.add_column("Nguồn tri thức", style="cyan", width=25)
    t_temp.add_column("Kết luận pháp lý", style="green")
    t_temp.add_row("Văn bản áp dụng", str(result.temporal_analysis.get("document_id", "BLHS_2015")))
    t_temp.add_row("Căn cứ thời điểm", f"Ngày xảy ra hành vi: {parsed.incident_date}")
    t_temp.add_row("Ghi chú chuyển tiếp", str(result.temporal_analysis.get("transitional_note", "N/A")))

    prec_names = [p.get("precedent_id", "AL") for p in result.relevant_precedents]
    t_temp.add_row("Án lệ liên quan", ", ".join(prec_names) if prec_names else "Không có án lệ tương đồng trực tiếp")
    console.print(t_temp)

    # Bảng 4: Kết quả dự đoán
    pred = result.predicted_outcome
    t_pred = Table(title="\n[bold yellow]4. DỰ ĐOÁN XÉT XỬ CỦA MÔ HÌNH HỌC MÁY (RANDOM FOREST)[/bold yellow]")
    t_pred.add_column("Đầu ra xét xử", style="cyan", width=25)
    t_pred.add_column("Kết quả dự đoán", style="bold green")
    t_pred.add_column("Cơ chế kiểm soát", style="yellow")

    outcome = "CÓ TỘI (Guilty)" if pred.get("predicted_outcome") == "guilty" else "VÔ TỘI (Not Guilty)"
    years = pred.get("predicted_sentence_years", 0.0)
    conf = pred.get("confidence", 0.0)

    t_pred.add_row("Phán quyết (Verdict)", outcome, "RandomForestClassifier (100% Balanced Acc)")
    t_pred.add_row("Mức án đề xuất", f"{years:.2f} năm tù", f"Khung luật định: {parsed.features.get('statutory_min', 0)} - {parsed.features.get('statutory_max', 0)} năm")
    t_pred.add_row("Độ tin cậy", f"{conf * 100:.1f}%", "Hàng rào nhất quán: Không án âm, vô tội = 0 năm")
    console.print(t_pred)

    console.print("\n[bold green]✓ Phân tích hoàn tất thành công![/bold green]\n")


if __name__ == "__main__":
    asyncio.run(main())
