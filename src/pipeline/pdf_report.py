from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas


class PdfReportBuilder:
    def __init__(self, output_path: Path) -> None:
        self.output_path = output_path

    def build(
        self,
        product_spec: Dict,
        budget_report: Dict,
        assignments: Dict[str, Dict[str, float]],
        sprint_summary: Dict[int, Dict[str, float]],
    ) -> None:
        pdf = canvas.Canvas(str(self.output_path), pagesize=LETTER)
        width, height = LETTER

        def heading(text: str, y_pos: float) -> float:
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(40, y_pos, text)
            return y_pos - 20

        def body(text: str, y_pos: float) -> float:
            pdf.setFont("Helvetica", 10)
            pdf.drawString(50, y_pos, text)
            return y_pos - 14

        y = height - 40
        y = heading("Product Overview", y)
        y = body(f"Title: {product_spec.get('title', 'N/A')}", y)
        y = body(f"Summary: {product_spec.get('summary', 'N/A')}", y)
        y -= 10

        y = heading("Key Features", y)
        for feature in product_spec.get("features", [])[:6]:
            y = body(f"• {feature}", y)
            if y < 80:
                pdf.showPage()
                y = height - 40
        y -= 10

        budget_pairs = [
            ("Engineering", budget_report.get("engineering_cost", 0), "Engineering Budget (USD)"),
            ("QA", budget_report.get("qa_cost", 0), "QA Budget (USD)"),
            ("Tools", budget_report.get("tools_cost", 0), "Licensing & Tools Budget (USD)"),
        ]

        y = heading("Budget", y)
        chart_origin_x = 60
        chart_width = 200
        bar_height = 12
        for label, cost, reference_key in budget_pairs:
            y = body(f"{label}: ${cost}", y)
            ref_value = budget_report.get("reference::" + reference_key, 0)
            if ref_value:
                fill_ratio = min(cost / ref_value, 1.5)
                bar_width = chart_width * fill_ratio
                pdf.setFillColor(colors.HexColor("#4C78A8"))
                pdf.rect(chart_origin_x, y + 4, min(bar_width, chart_width), bar_height, fill=1, stroke=0)
                if bar_width > chart_width:
                    pdf.setFillColor(colors.red)
                    pdf.rect(chart_origin_x + chart_width, y + 4, bar_width - chart_width, bar_height, fill=1, stroke=0)
                pdf.setFillColor(colors.black)
            if y < 80:
                pdf.showPage()
                y = height - 40
        y -= 10

        if budget_report.get("breakdown_pie"):
            y = heading("Budget Breakdown", y)
            for slice_info in budget_report["breakdown_pie"]:
                label = slice_info.get("label", "Segment")
                percent = slice_info.get("percent", 0)
                y = body(f"{label}: {percent}%", y)
                if y < 80:
                    pdf.showPage()
                    y = height - 40
            y -= 10

        y = heading("Assignments", y)
        for person, stats in assignments.items():
            y = body(
                f"{person}: {stats['total_hours']}h | ${stats['total_cost']}",
                y,
            )
            if y < 80:
                pdf.showPage()
                y = height - 40
        y -= 10

        y = heading("Sprint Summary", y)
        for sprint, summary in sprint_summary.items():
            y = body(f"Sprint {sprint}: {summary['tasks']} tasks, {round(summary['hours'], 2)}h", y)
            if y < 80:
                pdf.showPage()
                y = height - 40

        pdf.showPage()
        pdf.save()
