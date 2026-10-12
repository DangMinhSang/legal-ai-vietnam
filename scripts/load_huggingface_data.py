"""Script nạp dữ liệu pháp luật từ HuggingFace vào SQLite database và sqlite-vec.

Sử dụng:
    # Nạp từ file mẫu BLHS 2015 đã tải sẵn (nhanh, offline):
    python scripts/load_huggingface_data.py --from-sample

    # Nạp từ Hugging Face Hub (stream các văn bản hình sự):
    python scripts/load_huggingface_data.py --dataset th1nhng0/vietnamese-legal-documents --limit 10 --keywords "hình sự" "100/2015"
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console
from rich.table import Table

from src.db.database import AsyncSessionLocal, init_db
from src.ingestion.huggingface_loader import HuggingFaceLoader

console = Console()


async def ingest_from_sample(loader: HuggingFaceLoader) -> None:
    """Nạp văn bản BLHS 2015 từ file mẫu HTML đã tải sẵn."""
    sample_path = PROJECT_ROOT / "data" / "sample" / "legal_documents" / "blhs_2015_raw.html"
    if not sample_path.exists():
        console.print(f"[bold red]Không tìm thấy file mẫu tại: {sample_path}[/bold red]")
        return

    console.print(f"[bold cyan]Đang đọc file mẫu: {sample_path}...[/bold cyan]")
    html_text = sample_path.read_text(encoding="utf-8")
    clean_text = loader._html_to_text(html_text)

    async with AsyncSessionLocal() as session:
        result = await loader.ingest_document(
            title="Bộ luật Hình sự số 100/2015/QH13",
            full_text=clean_text,
            doc_type="law",
            doc_number="100/2015/QH13",
            issuing_body="Quốc hội",
            effective_date=loader._parse_date("01/01/2018"),
            source_url="https://vbpl.vn/TW/Pages/vbpq-van-ban-goc.aspx?ItemID=96122",
            metadata={
                "source": "Bộ luật Hình sự 2015",
                "law_code": "BLHS_2015",
                "amended_by": "12/2017/QH14",
            },
            db_session=session,
        )
        await session.commit()

    if result.success:
        console.print(f"[bold green]✓ Đã nạp thành công BLHS 2015! ID: {result.document_id}[/bold green]")
    else:
        console.print(f"[bold red]✗ Lỗi khi nạp: {result.error}[/bold red]")


async def main(
    dataset_name: str,
    limit: int,
    keywords: list[str] | None = None,
    from_sample: bool = False,
) -> None:
    # Đảm bảo database đã khởi tạo
    await init_db()

    loader = HuggingFaceLoader()

    if from_sample:
        await ingest_from_sample(loader)
        return

    console.print(f"[bold cyan]Đang nạp dataset '{dataset_name}' (giới hạn: {limit})...[/bold cyan]")
    if keywords:
        console.print(f"[dim]Bộ lọc từ khoá: {keywords}[/dim]")

    async with AsyncSessionLocal() as session:
        results = await loader.ingest(
            dataset_name=dataset_name,
            max_samples=limit,
            filter_keywords=keywords,
            db_session=session,
        )
        await session.commit()

    table = Table(title="Kết quả Ingestion")
    table.add_column("STT", justify="right", style="cyan")
    table.add_column("Số hiệu / Tên", style="magenta")
    table.add_column("Trạng thái", style="green")
    table.add_column("Document ID", style="yellow")

    for i, res in enumerate(results, 1):
        status = "[green]Thành công[/green]" if res.success else f"[red]Lỗi: {res.error}[/red]"
        title = res.metadata.get("title", "N/A")[:50]
        table.add_row(str(i), title, status, res.document_id or "N/A")

    console.print(table)
    console.print(f"[bold green]✓ Hoàn thành: {len(results)} văn bản đã được xử lý.[/bold green]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load data from HuggingFace.")
    parser.add_argument("--dataset", type=str, default="th1nhng0/vietnamese-legal-documents")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--keywords", nargs="*", default=None, help="Từ khoá lọc văn bản")
    parser.add_argument(
        "--from-sample",
        action="store_true",
        help="Nạp nhanh từ file mẫu BLHS 2015 đã tải sẵn",
    )
    args = parser.parse_args()
    asyncio.run(main(args.dataset, args.limit, args.keywords, args.from_sample))
