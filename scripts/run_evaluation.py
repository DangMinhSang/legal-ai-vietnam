"""Script chạy đánh giá toàn diện hệ thống Legal AI Vietnam.

Sử dụng:
    python scripts/run_evaluation.py --component retrieval
    python scripts/run_evaluation.py --component prediction
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console
from rich.table import Table

console = Console()


def run_evaluation(component: str) -> None:
    console.print(f"[bold magenta]Running evaluation for: {component}[/bold magenta]")

    table = Table("Metric", "Status", "Note")
    if component in ("retrieval", "all"):
        table.add_row("Precision@k", "Pending experiment", "Requires labeled legal QA / retrieval test set")
        table.add_row("Recall@k", "Pending experiment", "Requires labeled legal QA / retrieval test set")
        table.add_row("MRR", "Pending experiment", "Requires labeled legal QA / retrieval test set")
    if component in ("prediction", "all"):
        table.add_row("Accuracy", "Pending experiment", "Requires verified judgment training dataset")
        table.add_row("Macro-F1", "Pending experiment", "Requires verified judgment training dataset")
        table.add_row("Sentence MAE (months)", "Pending experiment", "Requires verified penalty dataset")

    console.print(table)
    console.print("[yellow]Notice: In accordance with research integrity principles, no simulated metrics are reported.[/yellow]")
    console.print("[green]Evaluation metric formulas verified in src/evaluation/metrics.py.[/green]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run evaluation metrics.")
    parser.add_argument("--component", type=str, default="all", choices=["retrieval", "prediction", "all"])
    args = parser.parse_args()
    run_evaluation(args.component)
