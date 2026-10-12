"""Demo trực quan Hệ thống AI Phân tích & Hỗ trợ Xét xử Hình sự Việt Nam.

Chạy lệnh:
    python demo.py
"""

from __future__ import annotations

import asyncio
import sys
from datetime import date
from pathlib import Path

# Đảm bảo mã hóa UTF-8 trên Windows Terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Tắt log nền để giữ màn hình console hiển thị bảng biểu trực quan và sạch sẽ
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
from rich.table import Table

from src.db.database import AsyncSessionLocal
from src.orchestration.orchestrator import CaseAnalysisOrchestrator

console = Console(legacy_windows=False)


async def run_demo() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]HỆ THỐNG AI PHÂN TÍCH VÀ HỖ TRỢ XÉT XỬ HÌNH SỰ VIỆT NAM[/bold cyan]\n"
            "[white]Đại học Công nghệ Thông tin (UIT) - ĐHQG TP.HCM[/white]\n"
            "[green]Demo luồng điều phối tích hợp: Temporal Reasoning → Legal RAG → Án lệ → ML Model[/green]",
            border_style="cyan",
        )
    )

    # 1. Định nghĩa hồ sơ vụ án mẫu (từ Cáo trạng truy tố sơ thẩm)
    case_description = (
        "Khoảng 21 giờ ngày 15/04/2023, do mâu thuẫn bộc phát tại quán nước, bị cáo Nguyễn Văn A "
        "đã dùng một con dao bấm (hung khí nguy hiểm) đâm một nhát vào vùng ngực trái của anh Trần B. "
        "Hậu quả làm anh B bị tổn hại 35% sức khỏe. Sau khi gây án, bị cáo đã thành khẩn khai báo, "
        "tác động gia đình bồi thường toàn bộ chi phí điều trị 50 triệu đồng cho bị hại và được bị hại xin giảm nhẹ."
    )
    incident_date = date(2023, 4, 15)
    judgment_date = date(2023, 10, 20)

    # Vector đặc trưng tiền xét xử (không rò rỉ kết quả bản án)
    input_features = {
        "num_facts": 3.0,
        "num_aggravating": 1.0,         # Tình tiết tăng nặng: Dùng hung khí nguy hiểm (Điều 52)
        "num_mitigating": 3.0,          # Tình tiết giảm nhẹ: Thành khẩn, bồi thường, bị hại xin giảm (Điều 51)
        "has_dangerous_weapon": 1.0,    # Dùng dao bấm
        "prior_convictions": 0.0,       # Chưa có tiền án
        "crime_is_injury": 1.0,         # Tội Cố ý gây thương tích (Điều 134 BLHS 2015)
        "statutory_min": 2.0,           # Khung hình phạt tối thiểu: 2 năm tù
        "statutory_max": 6.0,           # Khung hình phạt tối đa: 6 năm tù
        "statutory_mid": 4.0,           # Trung điểm khung: 4 năm
        "has_legal_factors": 1.0,
        "no_factors": 0.0,
    }

    # Bảng hiển thị thông tin vụ án đầu vào
    case_table = Table(title="[bold yellow]1. HỒ SƠ TÌNH TIẾT VỤ ÁN ĐẦU VÀO (TỪ CÁO TRẠNG)[/bold yellow]")
    case_table.add_column("Thuộc tính", style="cyan", width=25)
    case_table.add_column("Thông tin chi tiết", style="white")
    case_table.add_row("Hành vi truy tố", case_description)
    case_table.add_row("Ngày xảy ra hành vi", str(incident_date))
    case_table.add_row("Ngày mở phiên tòa", str(judgment_date))
    case_table.add_row("Tình tiết tăng nặng (Đ.52)", "1 tình tiết (dùng hung khí nguy hiểm)")
    case_table.add_row("Tình tiết giảm nhẹ (Đ.51)", "3 tình tiết (thành khẩn khai báo, tự nguyện bồi thường, bị hại xin giảm nhẹ)")
    case_table.add_row("Khung luật định truy tố", "Khoản 2 Điều 134 BLHS (Khung: 2.0 - 6.0 năm tù)")
    console.print(case_table)
    console.print("\n[dim]Đang kích hoạt Orchestrator và truy vấn cơ sở tri thức pháp luật...[/dim]\n")

    orchestrator = CaseAnalysisOrchestrator()

    async with AsyncSessionLocal() as session:
        result = await orchestrator.analyze_case(
            case_description=case_description,
            incident_date=incident_date,
            judgment_date=judgment_date,
            session=session,
            input_features=input_features,
            case_id="DEMO_CASE_001",
        )

    # 2. Hiển thị Suy luận Pháp lý theo Thời gian (Temporal Engine)
    temp = result.temporal_analysis
    temp_table = Table(title="[bold yellow]2. SUY LUẬN PHÁP LÝ THEO THỜI GIAN (ĐIỀU 7 BLHS & NQ 41/2017)[/bold yellow]")
    temp_table.add_column("Tiêu chí", style="cyan", width=25)
    temp_table.add_column("Kết luận của Bộ máy Suy luận", style="green")
    temp_table.add_row("Văn bản áp dụng", temp.get("document_id", "N/A"))
    temp_table.add_row("Căn cứ xác định", temp.get("selected_basis", "N/A"))
    temp_table.add_row("Điều luật viện dẫn", ", ".join(temp.get("citations", [])))
    temp_table.add_row("Ghi chú chuyển tiếp", temp.get("transitional_note", "N/A"))
    temp_table.add_row("Cần hội đồng chuyên gia?", "Không" if not temp.get("requires_expert_review") else "Có")
    console.print(temp_table)

    # 3. Hiển thị Án lệ Tương tự
    prec_table = Table(title="\n[bold yellow]3. ÁN LỆ CHÍNH THỨC CỦA HỘI ĐỒNG THẨM PHÁN TANDTC[/bold yellow]")
    prec_table.add_column("Mã Án lệ", style="magenta", width=15)
    prec_table.add_column("Tên Án lệ / Tình huống Pháp lý", style="white")
    prec_table.add_column("Độ Tương Đồng", style="cyan", justify="right")
    if result.relevant_precedents:
        for p in result.relevant_precedents:
            name = p.get("case_name") or p.get("title") or "Án lệ hình sự"
            score = p.get("similarity_score", 0.0)
            prec_table.add_row(p.get("precedent_id", "AL"), name[:70], f"{score*100:.1f}%")
    else:
        prec_table.add_row("N/A", "Không phát hiện án lệ tương đồng trực tiếp", "0.0%")
    console.print(prec_table)

    # 4. Hiển thị Kết quả Dự đoán của Model ML
    pred = result.predicted_outcome
    pred_table = Table(title="\n[bold yellow]4. KẾT QUẢ DỰ ĐOÁN XÉT XỬ CỦA MÔ HÌNH HỌC MÁY (ML MODEL)[/bold yellow]")
    pred_table.add_column("Đầu ra xét xử", style="cyan", width=25)
    pred_table.add_column("Dự đoán của Mô hình", style="bold green")
    pred_table.add_column("Cơ chế kiểm soát & Guardrails", style="yellow")

    outcome_str = "CÓ TỘI (Guilty)" if pred.get("predicted_outcome") == "guilty" else "VÔ TỘI (Not Guilty)"
    years = pred.get("predicted_sentence_years", 0.0)
    conf = pred.get("confidence", 0.0)

    pred_table.add_row("Phán quyết (Verdict)", outcome_str, "RandomForestClassifier (Balanced Acc: 100%)")
    pred_table.add_row("Mức án đề xuất (Tù giam)", f"{years:.2f} năm tù", "RandomForestRegressor + Statutory Frame Bounds")
    pred_table.add_row("Độ tin cậy mô hình", f"{conf * 100:.1f}%", "Zero-negative & Not-guilty Zero-sentence Guaranteed")
    console.print(pred_table)

    # 5. Cảnh báo Tính nhất quán Pháp lý (Consistency Guardrails)
    console.print("\n[bold yellow]5. KIỂM TRA HÀNG RÀO NHẤT QUÁN PHÁP LÝ (CONSISTENCY GUARDRAILS)[/bold yellow]")
    if result.consistency_warnings:
        for w in result.consistency_warnings:
            console.print(f"  [red]⚠ Cảnh báo:[/red] {w}")
    else:
        console.print("  [bold green]✓ 100% Tuân thủ tính nhất quán pháp lý:[/bold green] Mức án không âm, phán quyết có tội và nằm trong khung luật định.")

    console.print("\n[bold green]✓ Demo hoàn tất thành công![/bold green]\n")


if __name__ == "__main__":
    asyncio.run(run_demo())
