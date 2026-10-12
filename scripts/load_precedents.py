"""Script nạp và đánh chỉ mục các Án lệ chính thức của Hội đồng Thẩm phán TANDTC.

Thực hiện:
1. Đọc các file JSON trong data/sample/precedents/
2. Thêm bản ghi Precedent vào cơ sở dữ liệu
3. Sử dụng PrecedentIndexer để phân đoạn (LegalChunker) và đánh chỉ mục vector vào vec_text_chunks
4. Đảm bảo tri thức Án lệ được phân biệt tuyệt đối với Văn bản QPPL và Bản án thường
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console
from rich.table import Table
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import AsyncSessionLocal, init_db
from src.db.models import Precedent, TextChunk
from src.precedent_agent.indexer import PrecedentIndexer

console = Console()
PRECEDENTS_DIR = PROJECT_ROOT / "data" / "sample" / "precedents"


def parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        return None


async def load_precedent_file(
    file_path: Path,
    indexer: PrecedentIndexer,
    session: AsyncSession,
) -> dict[str, Any]:
    data = json.loads(file_path.read_text(encoding="utf-8"))

    prec_id = data.get("id") or file_path.stem
    precedent_number = data.get("precedent_number", "UNKNOWN/AL")
    title = data.get("title", "")
    pub_date = parse_date(data.get("publication_date"))

    # Kiểm tra tồn tại
    res = await session.execute(
        select(Precedent).where(Precedent.precedent_number == precedent_number)
    )
    existing_prec = res.scalar_one_or_none()

    if existing_prec is None:
        prec = Precedent(
            id=prec_id,
            precedent_number=precedent_number,
            title=title,
            legal_issue_summary=data.get("legal_issue_summary"),
            legal_solution=data.get("legal_solution"),
            full_text=data.get("full_text"),
            legal_domain=data.get("legal_domain", "criminal"),
            publication_date=pub_date,
            source_judgment_ref=data.get("source_judgment_ref"),
            source_url=data.get("source_url", "https://anle.toaan.gov.vn"),
            meta={
                "applicable_articles": data.get("applicable_articles", []),
                "file_name": file_path.name,
            },
        )
        session.add(prec)
        await session.flush()
    else:
        existing_prec.title = title
        existing_prec.legal_issue_summary = data.get("legal_issue_summary")
        existing_prec.legal_solution = data.get("legal_solution")
        existing_prec.full_text = data.get("full_text")
        existing_prec.legal_domain = data.get("legal_domain", "criminal")
        existing_prec.publication_date = pub_date
        existing_prec.source_judgment_ref = data.get("source_judgment_ref")
        existing_prec.source_url = data.get("source_url", "https://anle.toaan.gov.vn")
        existing_prec.meta = {
            "applicable_articles": data.get("applicable_articles", []),
            "file_name": file_path.name,
        }
        prec = existing_prec

    # Xóa các chunk cũ trong vec_text_chunks và text_chunks để tránh trùng lặp khi re-index
    old_chunk_stmt = select(TextChunk.id).where(TextChunk.precedent_id == prec.id)
    old_chunk_ids = (await session.execute(old_chunk_stmt)).scalars().all()
    if old_chunk_ids:
        for cid in old_chunk_ids:
            await session.execute(
                text("DELETE FROM vec_text_chunks WHERE chunk_id = :id"),
                {"id": cid},
            )
        await session.execute(
            delete(TextChunk).where(TextChunk.precedent_id == prec.id)
        )
        await session.flush()

    # Đánh chỉ mục vector
    chunk_ids = await indexer.index_precedent(prec, session=session)

    return {
        "id": prec.id,
        "precedent_number": precedent_number,
        "title": title[:40] + "..." if len(title) > 40 else title,
        "date": str(pub_date.date()) if pub_date else "N/A",
        "chunks_indexed": len(chunk_ids),
    }


async def main() -> None:
    await init_db()
    indexer = PrecedentIndexer()

    json_files = sorted(
        [
            p
            for p in PRECEDENTS_DIR.glob("*.json")
            if not p.name.endswith("_sample.json")
        ]
    )
    if not json_files:
        console.print("[yellow]Không tìm thấy file án lệ nào trong data/sample/precedents/[/yellow]")
        return

    console.print(f"[bold cyan]Đang nạp {len(json_files)} án lệ vào hệ thống...[/bold cyan]")

    results = []
    async with AsyncSessionLocal() as session:
        for f in json_files:
            try:
                res = await load_precedent_file(f, indexer, session)
                results.append(res)
            except Exception as e:
                console.print(f"[bold red]Lỗi khi nạp {f.name}: {e}[/bold red]")
        await session.commit()

    table = Table(title="Kết Quả Nạp Án Lệ Hình Sự")
    table.add_column("STT", justify="right", style="cyan")
    table.add_column("Số Án Lệ", style="magenta")
    table.add_column("Tiêu Đề", style="white")
    table.add_column("Ngày Công Bố", style="green")
    table.add_column("Số Chunk Vector", justify="right", style="blue")

    for i, r in enumerate(results, 1):
        table.add_row(
            str(i),
            r["precedent_number"],
            r["title"],
            r["date"],
            str(r["chunks_indexed"]),
        )

    console.print(table)
    console.print(f"[bold green]✓ Hoàn thành nạp và index {len(results)} án lệ vào DB và sqlite-vec![/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
