"""Script nạp tập bản án hình sự mẫu vào SQLite và đánh chỉ mục vector.

Thực hiện:
1. Đọc tất cả các file JSON trong data/sample/judgments/
2. Tạo bản ghi JudgmentDocument và JudgmentOutcome
3. Tạo bản ghi Case và các CaseFact tương ứng (phục vụ Feature Extraction và ML training)
4. Sử dụng CaseIndexer để phân đoạn và đánh chỉ mục vào vec_text_chunks
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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.case_retrieval.indexer import CaseIndexer
from src.db.database import AsyncSessionLocal, init_db
from src.db.models import Case, CaseFact, JudgmentDocument, JudgmentOutcome

console = Console()
PROJECT_ROOT = Path(__file__).resolve().parents[1]
JUDGMENTS_DIR = PROJECT_ROOT / "data" / "sample" / "judgments"


def parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        return None


async def load_judgment_file(
    file_path: Path,
    indexer: CaseIndexer,
    session: AsyncSession,
) -> dict[str, Any]:
    data = json.loads(file_path.read_text(encoding="utf-8"))

    doc_id = data.get("id") or file_path.stem
    case_number = data.get("case_number") or data.get("judgment_number")
    j_date = parse_date(data.get("judgment_date"))

    # 1. Kiểm tra tồn tại của JudgmentDocument
    res = await session.execute(
        select(JudgmentDocument).where(JudgmentDocument.id == doc_id)
    )
    existing_doc = res.scalar_one_or_none()

    if existing_doc is None:
        doc = JudgmentDocument(
            id=doc_id,
            judgment_number=case_number,
            judgment_type=data.get("judgment_type", "first_instance"),
            legal_domain=data.get("legal_domain", "criminal"),
            court_name=data.get("court"),
            court_level=data.get("court_level", "district"),
            judgment_date=j_date,
            full_text=data.get("full_text") or data.get("facts_summary"),
            meta={
                "crime_type": data.get("crime_type"),
                "applicable_articles": data.get("applicable_articles", []),
                "facts_summary": data.get("facts_summary"),
                "defendant": data.get("defendant", {}),
            },
        )
        session.add(doc)
        await session.flush()
    else:
        doc = existing_doc

    # 2. Tạo JudgmentOutcome
    outcome_str = data.get("verdict", "guilty")
    sentence_desc = f"{data.get('sentence_type')}: {data.get('sentence_years', 0)} năm"
    outcome_record = JudgmentOutcome(
        judgment_id=doc.id,
        party="accused",
        outcome=outcome_str,
        sentence=sentence_desc,
        meta={
            "sentence_years": data.get("sentence_years", 0.0),
            "sentence_type": data.get("sentence_type"),
            "suspended": data.get("suspended", False),
        },
    )
    session.add(outcome_record)

    # 3. Tạo Case và CaseFact phục vụ Feature Builder & ML Training
    case_code = f"CASE-{doc_id}"
    res_case = await session.execute(
        select(Case).where(Case.case_code == case_code)
    )
    existing_case = res_case.scalar_one_or_none()

    if existing_case is None:
        case = Case(
            case_code=case_code,
            title=f"Vụ án {case_number} - {data.get('crime_type')}",
            legal_domain="criminal",
            status="first_instance",
            incident_date=j_date,
            first_instance_judgment_id=doc.id,
            meta={"judgment_file": file_path.name},
        )
        session.add(case)
        await session.flush()

        # Tạo CaseFacts
        facts_to_add: list[CaseFact] = []
        # Charge
        facts_to_add.append(
            CaseFact(
                case_id=case.id,
                fact_type="charge",
                description=f"Truy tố về {data.get('crime_type')} theo Điều {', '.join(data.get('applicable_articles', []))}",
                confidence=1.0,
            )
        )
        # Summary
        if data.get("facts_summary"):
            facts_to_add.append(
                CaseFact(
                    case_id=case.id,
                    fact_type="evidence",
                    description=data["facts_summary"],
                    confidence=0.9,
                )
            )
        # Aggravating factors
        for agg in data.get("aggravating_factors", []):
            facts_to_add.append(
                CaseFact(
                    case_id=case.id,
                    fact_type="aggravating",
                    description=agg,
                    confidence=0.95,
                )
            )
        # Mitigating factors
        for mit in data.get("mitigating_factors", []):
            facts_to_add.append(
                CaseFact(
                    case_id=case.id,
                    fact_type="mitigating",
                    description=mit,
                    confidence=0.95,
                )
            )
        session.add_all(facts_to_add)

    # 4. Đánh chỉ mục vector dùng CaseIndexer
    chunk_ids = await indexer.index_judgment(doc, session=session)

    return {
        "id": doc.id,
        "case_number": case_number,
        "crime_type": data.get("crime_type"),
        "date": str(j_date.date()) if j_date else "N/A",
        "verdict": outcome_str,
        "chunks_indexed": len(chunk_ids),
    }


async def main() -> None:
    await init_db()
    indexer = CaseIndexer()

    json_files = sorted(JUDGMENTS_DIR.glob("*.json"))
    if not json_files:
        console.print("[yellow]Không tìm thấy file bản án nào trong data/sample/judgments/[/yellow]")
        return

    console.print(f"[bold cyan]Đang nạp {len(json_files)} bản án vào hệ thống...[/bold cyan]")

    results = []
    async with AsyncSessionLocal() as session:
        for f in json_files:
            try:
                res = await load_judgment_file(f, indexer, session)
                results.append(res)
            except Exception as e:
                console.print(f"[bold red]Lỗi khi nạp {f.name}: {e}[/bold red]")
        await session.commit()

    table = Table(title="Kết Quả Nạp Bản Án Hình Sự")
    table.add_column("STT", justify="right", style="cyan")
    table.add_column("Số Bản Án", style="magenta")
    table.add_column("Tội Danh", style="white")
    table.add_column("Ngày Xử", style="green")
    table.add_column("Kết Quả", style="yellow")
    table.add_column("Số Chunk Vector", justify="right", style="blue")

    for i, r in enumerate(results, 1):
        table.add_row(
            str(i),
            r["case_number"] or "N/A",
            r["crime_type"] or "N/A",
            r["date"],
            r["verdict"],
            str(r["chunks_indexed"]),
        )

    console.print(table)
    console.print(f"[bold green]✓ Hoàn thành nạp {len(results)} bản án vào DB và sqlite-vec![/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
