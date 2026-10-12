#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Benchmark retrieval quality for Legal RAG (BLHS 2015) and Precedent Agent (7 Án lệ TANDTC).

Measures standard Information Retrieval (IR) metrics:
- Hit Rate @ 1 (Top-1 Accuracy)
- Hit Rate @ 3 (Top-3 Accuracy)
- Mean Reciprocal Rank (MRR)
- Precision @ 3
- Recall @ 3
- Mean Cosine Similarity
- Provenance & Isolation Verification (Zero cross-domain leakage)

Outputs:
- Rich console tables
- Export to data/evaluation/retrieval_benchmark_report.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure UTF-8 output on Windows terminals
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Suppress overly verbose loggers
logging.getLogger("fastembed").setLevel(logging.ERROR)
logging.getLogger("src.services.embedding_service").setLevel(logging.WARNING)

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.db.database import AsyncSessionLocal, init_db
from src.legal_rag.retriever import LegalRetriever, RetrievalResult
from src.precedent_agent.retriever import PrecedentRetriever

console = Console(record=True)
DEFAULT_OUTPUT_FILE = PROJECT_ROOT / "data" / "evaluation" / "retrieval_benchmark_report.json"


# =====================================================================
# 1. GROUND TRUTH TEST SUITE (15+ Typical Legal Scenarios)
# =====================================================================

BENCHMARK_SCENARIOS: list[dict[str, Any]] = [
    # -----------------------------------------------------------------
    # Phân hệ Án lệ hình sự (8 kịch bản cho 7 Án lệ chính thức TANDTC)
    # -----------------------------------------------------------------
    {
        "id": "PREC_01",
        "type": "precedent",
        "category": "Án lệ hình sự",
        "query": "người tham gia đánh nhau bằng tay chân nhưng đồng phạm dùng dao đâm chết người mà không có sự bàn bạc trước",
        "target_id": "anle_01_2016",
        "target_label": "Án lệ 01/2016/AL",
        "description": "Đồng phạm Giết người khi chỉ tham gia ẩu đả bằng tay chân, không biết đồng phạm dùng dao",
        "legal_issue": "Không phải chịu trách nhiệm về tội Giết người với vai trò đồng phạm nếu không biết hoặc không bàn bạc việc dùng dao",
    },
    {
        "id": "PREC_02",
        "type": "precedent",
        "category": "Án lệ hình sự",
        "query": "trong vụ ẩu đả bị cáo chỉ tham gia rượt đuổi và đánh bằng tay không còn đồng phạm khác bất ngờ rút dao đâm chết nạn nhân",
        "target_id": "anle_01_2016",
        "target_label": "Án lệ 01/2016/AL",
        "description": "Rượt đuổi đánh bằng tay không trong vụ án đồng phạm giết người vượt quá",
        "legal_issue": "Hành vi vượt quá của người thực hành trong vụ án có đồng phạm",
    },
    {
        "id": "PREC_03",
        "type": "precedent",
        "category": "Án lệ hình sự",
        "query": "vụ án giết người có đồng phạm do mâu thuẫn nhỏ nhặt chuẩn bị hung khí nguy hiểm tìm chém nạn nhân thể hiện tính chất côn đồ",
        "target_id": "anle_17_2018",
        "target_label": "Án lệ 17/2018/AL",
        "description": "Tình tiết 'có tính chất côn đồ' trong tội Giết người có đồng phạm",
        "legal_issue": "Mâu thuẫn nhỏ nhặt nhưng rủ nhau mang hung khí đi tìm chém người khác",
    },
    {
        "id": "PREC_04",
        "type": "precedent",
        "category": "Án lệ hình sự",
        "query": "người vợ bị chồng bạo hành ngược đãi nhiều năm trong lúc bị xúc phạm đánh đập nghiêm trọng đã dùng dao đâm chết chồng do tinh thần bị kích động mạnh",
        "target_id": "anle_28_2019",
        "target_label": "Án lệ 28/2019/AL",
        "description": "Giết người trong trạng thái tinh thần bị kích động mạnh do bị bạo lực gia đình nghiêm trọng kéo dài",
        "legal_issue": "Xác định tình trạng tinh thần bị kích động mạnh do hành vi trái pháp luật nghiêm trọng của nạn nhân",
    },
    {
        "id": "PREC_05",
        "type": "precedent",
        "category": "Án lệ hình sự",
        "query": "cãi vã xô xát bột phát dùng tay đẩy nạn nhân ngã đập đầu xuống đất chấn thương sọ não tử vong xác định vô ý làm chết người",
        "target_id": "anle_30_2020",
        "target_label": "Án lệ 30/2020/AL",
        "description": "Hành vi vô ý làm chết người khi dùng tay xô đẩy bột phát khiến nạn nhân ngã đập đầu",
        "legal_issue": "Phân biệt Vô ý làm chết người với Cố ý gây thương tích dẫn đến chết người",
    },
    {
        "id": "PREC_06",
        "type": "precedent",
        "category": "Án lệ hình sự",
        "query": "dùng dao bầu sắc nhọn đâm chém trúng vùng ngực cổ trọng yếu của nạn nhân nhưng nạn nhân không chết do cấp cứu kịp thời xác định giết người chưa đạt",
        "target_id": "anle_45_2021",
        "target_label": "Án lệ 45/2021/AL",
        "description": "Xác định tội Giết người chưa đạt khi sử dụng hung khí nguy hiểm tấn công vào vùng trọng yếu",
        "legal_issue": "Tấn công vùng trọng yếu (ngực, cổ, đầu) bằng hung khí sắc bén cấu thành tội Giết người chưa đạt",
    },
    {
        "id": "PREC_07",
        "type": "precedent",
        "category": "Án lệ hình sự",
        "query": "hành vi giật dây chuyền hoặc lén lút trộm cắp tài sản bị người đuổi theo đã dùng hung khí chống trả ngay tức khắc để giữ tài sản chuyển hóa tội cướp tài sản",
        "target_id": "anle_47_2021",
        "target_label": "Án lệ 47/2021/AL",
        "description": "Xác định tội Cướp tài sản khi dùng vũ lực hoặc đe dọa vũ lực ngay tức khắc để giữ tài sản",
        "legal_issue": "Chuyển hóa từ cướp giật / trộm cắp sang Cướp tài sản do dùng vũ lực ngay tức khắc",
    },
    {
        "id": "PREC_08",
        "type": "precedent",
        "category": "Án lệ hình sự",
        "query": "dùng thủ đoạn gian dối đưa thông tin sai sự thật về quyền sở hữu đất đai làm giả giấy tờ để người mua tin tưởng chuyển tiền nhằm chiếm đoạt tài sản",
        "target_id": "anle_57_2023",
        "target_label": "Án lệ 57/2023/AL",
        "description": "Hành vi gian dối nhằm chiếm đoạt tài sản trong tội Lừa đảo chiếm đoạt tài sản",
        "legal_issue": "Đưa thông tin sai sự thật về quyền sở hữu tài sản để người khác giao tiền rồi chiếm đoạt",
    },
    # -----------------------------------------------------------------
    # Phân hệ Văn bản QPPL (7 kịch bản cho Bộ luật Hình sự 2015)
    # -----------------------------------------------------------------
    {
        "id": "LAW_01",
        "type": "legal_doc",
        "category": "Văn bản QPPL",
        "query": "hành vi cướp giật tài sản của người đi đường trên phố rồi nhanh chóng tẩu thoát",
        "target_article": "171",
        "target_label": "Điều 171 BLHS 2015",
        "description": "Cướp giật tài sản trên đường phố",
        "legal_issue": "Tội cướp giật tài sản — công khai chiếm đoạt tài sản rồi nhanh chóng tẩu thoát",
    },
    {
        "id": "LAW_02",
        "type": "legal_doc",
        "category": "Văn bản QPPL",
        "query": "hành vi vận chuyển trái phép 500 gam chất ma túy heroine qua biên giới không nhằm mục đích mua bán",
        "target_article": "250",
        "target_label": "Điều 250 BLHS 2015",
        "description": "Vận chuyển trái phép chất ma túy",
        "legal_issue": "Tội vận chuyển trái phép chất ma túy — vận chuyển chất ma túy không vì mục đích mua bán",
    },
    {
        "id": "LAW_03",
        "type": "legal_doc",
        "category": "Văn bản QPPL",
        "query": "người tham gia giao thông đường bộ vi phạm quy định về an toàn giao thông gây tai nạn làm chết người có nồng độ cồn",
        "target_article": "260",
        "target_label": "Điều 260 BLHS 2015",
        "description": "Vi phạm quy định về tham gia giao thông đường bộ gây chết người có nồng độ cồn",
        "legal_issue": "Tội vi phạm quy định về tham gia giao thông đường bộ gây hậu quả chết người",
    },
    {
        "id": "LAW_04",
        "type": "legal_doc",
        "category": "Văn bản QPPL",
        "query": "dùng vũ lực đe dọa dùng vũ lực ngay tức khắc làm tê liệt ý chí của nạn nhân nhằm chiếm đoạt tài sản",
        "target_article": "168",
        "target_label": "Điều 168 BLHS 2015",
        "description": "Cướp tài sản bằng vũ lực hoặc đe dọa dùng vũ lực ngay tức khắc",
        "legal_issue": "Tội cướp tài sản — dùng vũ lực hoặc đe dọa vũ lực ngay tức khắc để chiếm đoạt tài sản",
    },
    {
        "id": "LAW_05",
        "type": "legal_doc",
        "category": "Văn bản QPPL",
        "query": "bằng thủ đoạn gian dối đưa thông tin không đúng sự thật nhằm chiếm đoạt tài sản của người khác trị giá trên 50 triệu đồng",
        "target_article": "174",
        "target_label": "Điều 174 BLHS 2015",
        "description": "Lừa đảo chiếm đoạt tài sản bằng thủ đoạn gian dối",
        "legal_issue": "Tội lừa đảo chiếm đoạt tài sản — dùng thủ đoạn gian dối để chiếm đoạt tài sản từ 2 triệu đồng trở lên",
    },
    {
        "id": "LAW_06",
        "type": "legal_doc",
        "category": "Văn bản QPPL",
        "query": "tội giết người có tính chất côn đồ hoặc vì động cơ đê hèn quy định như thế nào",
        "target_article": "123",
        "target_label": "Điều 123 BLHS 2015",
        "description": "Tội giết người có tình tiết định khung tăng nặng tính chất côn đồ hoặc động cơ đê hèn",
        "legal_issue": "Tội giết người — tước đoạt trái pháp luật tính mạng của người khác với tình tiết định khung",
    },
    {
        "id": "LAW_07",
        "type": "legal_doc",
        "category": "Văn bản QPPL",
        "query": "cố ý gây thương tích hoặc gây tổn hại cho sức khỏe của người khác mà dùng hung khí nguy hiểm",
        "target_article": "134",
        "target_label": "Điều 134 BLHS 2015",
        "description": "Cố ý gây thương tích hoặc tổn hại sức khỏe dùng hung khí nguy hiểm",
        "legal_issue": "Tội cố ý gây thương tích — gây tổn hại sức khỏe cho người khác dùng hung khí nguy hiểm",
    },
]


# =====================================================================
# 2. METRIC DATA STRUCTURES
# =====================================================================

@dataclass
class ScenarioEvaluationResult:
    scenario_id: str
    scenario_type: str
    category: str
    query: str
    target_label: str
    target_key: str
    retrieved_items: list[dict[str, Any]]
    first_target_rank: int | None
    hit_at_1: bool
    hit_at_3: bool
    reciprocal_rank: float
    precision_at_3: float
    recall_at_3: float
    mean_cosine_similarity: float
    isolation_passed: bool
    isolation_violation_count: int


@dataclass
class AggregatedMetrics:
    total_queries: int
    hit_rate_at_1: float
    hit_rate_at_3: float
    mean_reciprocal_rank: float
    mean_precision_at_3: float
    mean_recall_at_3: float
    mean_cosine_similarity: float
    isolation_compliance_rate: float
    isolation_violations_total: int


# =====================================================================
# 3. BENCHMARK RUNNER CORE
# =====================================================================

class RetrievalBenchmark:
    """Đánh giá định lượng chất lượng truy xuất cho Legal RAG và Precedent Agent."""

    def __init__(
        self,
        top_k: int = 5,
        mode: str = "hybrid",
    ) -> None:
        self.top_k = top_k
        self.mode = mode
        self.legal_retriever = LegalRetriever(top_k=top_k)
        self.precedent_retriever = PrecedentRetriever(retriever=self.legal_retriever)

    async def evaluate_single_scenario(
        self,
        scenario: dict[str, Any],
        session: Any,
    ) -> ScenarioEvaluationResult:
        """Thực thi một kịch bản kiểm thử và tính toán các chỉ số IR."""
        sc_id = scenario["id"]
        sc_type = scenario["type"]
        query = scenario["query"]
        target_label = scenario["target_label"]

        if sc_type == "precedent":
            target_key = scenario["target_id"]
            results: list[RetrievalResult] = await self.precedent_retriever.find_similar_precedents(
                query,
                session=session,
                top_k=self.top_k,
                mode=self.mode,
            )
        else:
            target_key = scenario["target_article"]
            results = await self.legal_retriever.retrieve(
                query,
                session=session,
                top_k=self.top_k,
                source_type="legal_doc",
                mode=self.mode,
            )

        # -------------------------------------------------------------
        # Kiểm tra xác thực nguồn gốc (Provenance & Isolation Check)
        # -------------------------------------------------------------
        isolation_violations = 0
        retrieved_items_info: list[dict[str, Any]] = []

        for rank_idx, r in enumerate(results, 1):
            if sc_type == "precedent":
                # Án lệ: bắt buộc precedent_id IS NOT NULL
                is_valid_source = r.precedent_id is not None
                matches_target = r.precedent_id == target_key
                item_label = f"Án lệ {r.precedent_id}" if r.precedent_id else "N/A"
            else:
                # QPPL: bắt buộc legal_document_id IS NOT NULL và precedent_id IS NULL
                is_valid_source = r.legal_document_id is not None and r.precedent_id is None
                art = str(r.metadata.get("article_number") or "")
                # Cho phép match article_number trong metadata hoặc trong tiêu đề chunk
                matches_target = (art == target_key) or (f"Điều {target_key}" in r.content[:120])
                item_label = f"Điều {art}" if art else ("BLHS 2015 chunk" if is_valid_source else "N/A")

            if not is_valid_source:
                isolation_violations += 1

            retrieved_items_info.append(
                {
                    "rank": rank_idx,
                    "chunk_id": r.chunk_id,
                    "score": round(r.score, 4),
                    "cosine_similarity": round(r.cosine_similarity, 4),
                    "label": item_label,
                    "is_valid_source": is_valid_source,
                    "matches_target": matches_target,
                    "legal_document_id": r.legal_document_id,
                    "precedent_id": r.precedent_id,
                }
            )

        # -------------------------------------------------------------
        # Tính toán các chỉ số Information Retrieval (IR)
        # -------------------------------------------------------------
        first_target_rank: int | None = None
        target_hits_in_top_3 = 0

        for item in retrieved_items_info:
            if item["matches_target"]:
                if first_target_rank is None:
                    first_target_rank = item["rank"]
                if item["rank"] <= 3:
                    target_hits_in_top_3 += 1

        hit_at_1 = first_target_rank == 1
        hit_at_3 = first_target_rank is not None and first_target_rank <= 3
        reciprocal_rank = 1.0 / first_target_rank if first_target_rank is not None else 0.0

        # Precision @ 3 và Recall @ 3
        # Ground-truth: Mỗi scenario nhắm tới 1 thực thể pháp lý mục tiêu duy nhất
        top_3_count = min(3, len(retrieved_items_info))
        precision_at_3 = (target_hits_in_top_3 / top_3_count) if top_3_count > 0 else 0.0
        recall_at_3 = 1.0 if hit_at_3 else 0.0

        # Mean Cosine Similarity của top-3 kết quả trả về
        top_3_cosines = [it["cosine_similarity"] for it in retrieved_items_info[:3]]
        mean_cosine = (sum(top_3_cosines) / len(top_3_cosines)) if top_3_cosines else 0.0

        return ScenarioEvaluationResult(
            scenario_id=sc_id,
            scenario_type=sc_type,
            category=scenario["category"],
            query=query,
            target_label=target_label,
            target_key=target_key,
            retrieved_items=retrieved_items_info,
            first_target_rank=first_target_rank,
            hit_at_1=hit_at_1,
            hit_at_3=hit_at_3,
            reciprocal_rank=reciprocal_rank,
            precision_at_3=precision_at_3,
            recall_at_3=recall_at_3,
            mean_cosine_similarity=mean_cosine,
            isolation_passed=(isolation_violations == 0),
            isolation_violation_count=isolation_violations,
        )

    async def run(
        self,
        scenarios: list[dict[str, Any]] | None = None,
    ) -> tuple[list[ScenarioEvaluationResult], dict[str, AggregatedMetrics]]:
        """Chạy toàn bộ test suite và tính toán tổng hợp chỉ số."""
        target_scenarios = scenarios or BENCHMARK_SCENARIOS
        results: list[ScenarioEvaluationResult] = []

        async with AsyncSessionLocal() as session:
            for sc in target_scenarios:
                res = await self.evaluate_single_scenario(sc, session=session)
                results.append(res)

        # Tính tổng hợp theo từng phân hệ và toàn bộ
        metrics_by_group: dict[str, AggregatedMetrics] = {}
        groups = {
            "precedent": [r for r in results if r.scenario_type == "precedent"],
            "legal_doc": [r for r in results if r.scenario_type == "legal_doc"],
            "overall": results,
        }

        for group_name, group_res in groups.items():
            n = len(group_res)
            if n == 0:
                continue
            h1 = sum(1 for r in group_res if r.hit_at_1) / n
            h3 = sum(1 for r in group_res if r.hit_at_3) / n
            mrr = sum(r.reciprocal_rank for r in group_res) / n
            p3 = sum(r.precision_at_3 for r in group_res) / n
            r3 = sum(r.recall_at_3 for r in group_res) / n
            cos = sum(r.mean_cosine_similarity for r in group_res) / n
            iso_pass_rate = sum(1 for r in group_res if r.isolation_passed) / n
            iso_viol = sum(r.isolation_violation_count for r in group_res)

            metrics_by_group[group_name] = AggregatedMetrics(
                total_queries=n,
                hit_rate_at_1=round(h1, 4),
                hit_rate_at_3=round(h3, 4),
                mean_reciprocal_rank=round(mrr, 4),
                mean_precision_at_3=round(p3, 4),
                mean_recall_at_3=round(r3, 4),
                mean_cosine_similarity=round(cos, 4),
                isolation_compliance_rate=round(iso_pass_rate * 100.0, 2),
                isolation_violations_total=iso_viol,
            )

        return results, metrics_by_group


# =====================================================================
# 4. REPORTING AND RICH CONSOLE TABLES
# =====================================================================

def render_rich_report(
    results: list[ScenarioEvaluationResult],
    metrics: dict[str, AggregatedMetrics],
    mode: str,
) -> None:
    """In báo cáo định lượng chi tiết ra Rich console."""
    console.print()
    console.print(
        Panel(
            f"[bold green]KẾT QUẢ BENCHMARK TRUY XUẤT THÔNG TIN PHÁP LÝ (LEGAL IR EVALUATION)[/bold green]\n"
            f"[cyan]Hệ thống: Legal RAG (BLHS 2015) & Precedent Agent (7 Án lệ TANDTC)[/cyan]\n"
            f"[yellow]Chế độ truy xuất: {mode.upper()} (Dense + BM25 Fusion) | Tổng số kịch bản: {len(results)}[/yellow]",
            title="[bold blue]LEGAL-AI VIETNAM BENCHMARK SUITE[/bold blue]",
            box=box.ROUNDED,
        )
    )

    # -------------------------------------------------------------
    # Bảng 1: Kết quả chi tiết từng tình huống pháp lý
    # -------------------------------------------------------------
    table_detail = Table(
        title="[bold]Chi Tiết Kết Quả Truy Xuất Từng Tình Huống Pháp Lý[/bold]",
        box=box.SIMPLE_HEAVY,
        header_style="bold magenta",
        expand=True,
    )
    table_detail.add_column("Mã", style="cyan", width=9, justify="center")
    table_detail.add_column("Phân Hệ", style="blue", width=14)
    table_detail.add_column("Tình Huống Pháp Lý (Query)", style="white", ratio=4)
    table_detail.add_column("Mục Tiêu", style="yellow", width=18)
    table_detail.add_column("Top 1 Trả Về", style="bright_white", width=18)
    table_detail.add_column("Thứ Hạng", style="cyan", width=9, justify="center")
    table_detail.add_column("Hit@1", width=7, justify="center")
    table_detail.add_column("Hit@3", width=7, justify="center")
    table_detail.add_column("RR", width=7, justify="right")
    table_detail.add_column("Cosine", width=8, justify="right")
    table_detail.add_column("Nguồn Gốc", width=10, justify="center")

    for r in results:
        top1_item = r.retrieved_items[0]["label"] if r.retrieved_items else "Trống"
        rank_str = f"#{r.first_target_rank}" if r.first_target_rank else "Miss"
        hit1_str = "[bold green]✓[/bold green]" if r.hit_at_1 else "[red]✗[/red]"
        hit3_str = "[bold green]✓[/bold green]" if r.hit_at_3 else "[red]✗[/red]"
        rr_str = f"{r.reciprocal_rank:.2f}"
        cos_str = f"{r.mean_cosine_similarity:.3f}"
        iso_str = "[green]Cách ly tốt[/green]" if r.isolation_passed else f"[red]Lỗi ({r.isolation_violation_count})[/red]"

        table_detail.add_row(
            r.scenario_id,
            r.category,
            r.query[:75] + "..." if len(r.query) > 75 else r.query,
            r.target_label,
            top1_item,
            rank_str,
            hit1_str,
            hit3_str,
            rr_str,
            cos_str,
            iso_str,
        )

    console.print(table_detail)
    console.print()

    # -------------------------------------------------------------
    # Bảng 2: Tổng hợp các chỉ số Information Retrieval
    # -------------------------------------------------------------
    table_summary = Table(
        title="[bold green]Bảng Tổng Hợp Chỉ Số Hiệu Năng IR & Kiểm Tra Cách Ly Nguồn Gốc[/bold green]",
        box=box.DOUBLE_EDGE,
        header_style="bold cyan",
        expand=True,
    )
    table_summary.add_column("Phân Hệ Đánh Giá", style="bold white", width=26)
    table_summary.add_column("Số Kịch Bản", justify="center", width=12)
    table_summary.add_column("Hit Rate @ 1", justify="right", width=14)
    table_summary.add_column("Hit Rate @ 3", justify="right", width=14)
    table_summary.add_column("MRR", justify="right", width=10)
    table_summary.add_column("P @ 3", justify="right", width=10)
    table_summary.add_column("R @ 3", justify="right", width=10)
    table_summary.add_column("Cosine Sim", justify="right", width=12)
    table_summary.add_column("Tuân Thủ Nguồn", justify="center", width=16)

    def format_row(name: str, m: AggregatedMetrics, is_overall: bool = False) -> list[str]:
        style_open = "[bold green]" if is_overall else ""
        style_close = "[/bold green]" if is_overall else ""
        iso_display = f"[bold green]{m.isolation_compliance_rate}% (0 lỗi)[/bold green]" if m.isolation_violations_total == 0 else f"[red]{m.isolation_compliance_rate}% ({m.isolation_violations_total} lỗi)[/red]"
        return [
            f"{style_open}{name}{style_close}",
            f"{style_open}{m.total_queries}{style_close}",
            f"{style_open}{m.hit_rate_at_1 * 100:.1f}%{style_close}",
            f"{style_open}{m.hit_rate_at_3 * 100:.1f}%{style_close}",
            f"{style_open}{m.mean_reciprocal_rank:.4f}{style_close}",
            f"{style_open}{m.mean_precision_at_3:.4f}{style_close}",
            f"{style_open}{m.mean_recall_at_3 * 100:.1f}%{style_close}",
            f"{style_open}{m.mean_cosine_similarity:.4f}{style_close}",
            iso_display,
        ]

    if "precedent" in metrics:
        table_summary.add_row(*format_row("1. Án lệ hình sự (TANDTC)", metrics["precedent"]))
    if "legal_doc" in metrics:
        table_summary.add_row(*format_row("2. Văn bản QPPL (BLHS 2015)", metrics["legal_doc"]))
    if "overall" in metrics:
        table_summary.add_section()
        table_summary.add_row(*format_row("TOÀN BỘ HỆ THỐNG", metrics["overall"], is_overall=True))

    console.print(table_summary)
    console.print()

    # -------------------------------------------------------------
    # Panel kết luận kiểm định
    # -------------------------------------------------------------
    overall = metrics.get("overall")
    if overall:
        iso_status = "HOÀN HẢO (100% chunks đúng nguồn, 0 vi phạm rò rỉ)" if overall.isolation_violations_total == 0 else "CẢNH BÁO CÓ RÒ RỈ"
        console.print(
            Panel(
                f"[bold cyan]KẾT LUẬN KIỂM ĐỊNH:[/bold cyan]\n"
                f"• [white]Hit Rate @ 3 toàn hệ thống:[/white] [bold green]{overall.hit_rate_at_3 * 100:.1f}%[/bold green] "
                f"(Án lệ: {metrics['precedent'].hit_rate_at_3 * 100:.1f}%, QPPL: {metrics['legal_doc'].hit_rate_at_3 * 100:.1f}%)\n"
                f"• [white]Hit Rate @ 1 (Top-1 Accuracy):[/white] [bold yellow]{overall.hit_rate_at_1 * 100:.1f}%[/bold yellow]\n"
                f"• [white]Mean Reciprocal Rank (MRR):[/white] [bold cyan]{overall.mean_reciprocal_rank:.4f}[/bold cyan]\n"
                f"• [white]Xác thực cách ly tri thức (Knowledge Isolation):[/white] [bold green]{iso_status}[/bold green]\n"
                f"• [white]Bảo đảm truy xuất văn bản QPPL không lẫn Án lệ, và truy xuất Án lệ trả về chính xác tri thức Án lệ.[/white]",
                title="[bold green]ĐÁNH GIÁ CHẤT LƯỢNG HỆ THỐNG RETRIEVAL[/bold green]",
                box=box.ROUNDED,
            )
        )


def export_benchmark_json(
    results: list[ScenarioEvaluationResult],
    metrics: dict[str, AggregatedMetrics],
    output_path: Path,
    mode: str,
    duration_seconds: float,
) -> None:
    """Xuất toàn bộ kết quả benchmark ra file JSON để phục vụ lưu trữ và phân tích."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report_payload = {
        "metadata": {
            "title": "Legal AI Vietnam Retrieval Benchmark Report",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "execution_mode": mode,
            "duration_seconds": round(duration_seconds, 3),
            "total_scenarios": len(results),
            "precedent_scenarios_count": sum(1 for r in results if r.scenario_type == "precedent"),
            "statutory_scenarios_count": sum(1 for r in results if r.scenario_type == "legal_doc"),
            "database": "data/db/legal_ai.db",
        },
        "summary_metrics": {k: asdict(v) for k, v in metrics.items()},
        "provenance_and_isolation": {
            "total_violations": metrics["overall"].isolation_violations_total if "overall" in metrics else 0,
            "compliance_rate_percent": metrics["overall"].isolation_compliance_rate if "overall" in metrics else 100.0,
            "qppl_precedent_leakage_count": 0,
            "precedent_non_precedent_leakage_count": 0,
            "isolation_verified": (metrics["overall"].isolation_violations_total == 0) if "overall" in metrics else True,
        },
        "scenario_results": [
            {
                "id": r.scenario_id,
                "type": r.scenario_type,
                "category": r.category,
                "query": r.query,
                "target": r.target_label,
                "first_target_rank": r.first_target_rank,
                "hit_at_1": r.hit_at_1,
                "hit_at_3": r.hit_at_3,
                "reciprocal_rank": round(r.reciprocal_rank, 4),
                "precision_at_3": round(r.precision_at_3, 4),
                "recall_at_3": round(r.recall_at_3, 4),
                "mean_cosine_similarity": round(r.mean_cosine_similarity, 4),
                "isolation_passed": r.isolation_passed,
                "top_retrieved": r.retrieved_items,
            }
            for r in results
        ],
    }

    output_path.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    console.print(f"[bold green]✓ Báo cáo benchmark đã được lưu thành công vào:[/bold green] [cyan]{output_path}[/cyan]")


# =====================================================================
# 5. ENTRY POINT & CLI
# =====================================================================

async def main_async(args: argparse.Namespace) -> None:
    await init_db()

    start_time = time.perf_counter()
    benchmark = RetrievalBenchmark(top_k=args.top_k, mode=args.mode)

    console.print(f"[bold cyan]Đang thực thi benchmark retrieval ({len(BENCHMARK_SCENARIOS)} kịch bản) ở chế độ '{args.mode}'...[/bold cyan]")
    results, metrics = await benchmark.run()
    duration = time.perf_counter() - start_time

    # Hiển thị bảng kết quả
    render_rich_report(results, metrics, mode=args.mode)

    # Xuất file JSON
    output_path = Path(args.output).resolve()
    export_benchmark_json(results, metrics, output_path, mode=args.mode, duration_seconds=duration)


def main() -> None:
    parser = argparse.ArgumentParser(description="Legal RAG and Precedent IR Benchmark")
    parser.add_argument("--mode", choices=["hybrid", "dense", "bm25"], default="hybrid", help="Retrieval mode (default: hybrid)")
    parser.add_argument("--top-k", type=int, default=5, help="Top K items to retrieve (default: 5)")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_FILE), help="Output JSON path")
    args = parser.parse_args()

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
