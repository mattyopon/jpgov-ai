"""レポート生成サービス.

AI Governance Mark申請用の自己評価レポートをAI生成し、PDF出力する。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from fpdf import FPDF

from app.db.database import ReportRow, get_db
from app.models import (
    AssessmentResult,
    ComplianceStatus,
    EvidenceSummary,
    GapAnalysisResult,
    ReportResponse,
)


REPORTS_DIR = Path("reports")


class JapaneseReport(FPDF):
    """日本語対応PDFレポート."""

    def __init__(self) -> None:
        super().__init__()
        # fpdf2はUnicodeをサポート。日本語フォントがない場合はフォールバック
        self.add_page()
        self.set_auto_page_break(auto=True, margin=15)

    def _add_title(self, title: str) -> None:
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 12, title, new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(5)

    def _add_section(self, title: str) -> None:
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def _add_text(self, text: str) -> None:
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def _add_table_row(self, cols: list[str], widths: list[int], bold: bool = False) -> None:
        style = "B" if bold else ""
        self.set_font("Helvetica", style, 9)
        for col, w in zip(cols, widths):
            self.cell(w, 7, col, border=1)
        self.ln()


def _status_label(status: ComplianceStatus) -> str:
    labels = {
        ComplianceStatus.COMPLIANT: "Compliant",
        ComplianceStatus.PARTIAL: "Partial",
        ComplianceStatus.NON_COMPLIANT: "Non-Compliant",
        ComplianceStatus.NOT_ASSESSED: "Not Assessed",
    }
    return labels.get(status, str(status.value))


def _maturity_label(level: int) -> str:
    labels = {
        1: "Level 1 - Initial",
        2: "Level 2 - Repeatable",
        3: "Level 3 - Defined",
        4: "Level 4 - Managed",
        5: "Level 5 - Optimized",
    }
    return labels.get(level, f"Level {level}")


async def generate_report(
    assessment: AssessmentResult,
    gap_analysis: GapAnalysisResult,
    evidence_summary: EvidenceSummary | None = None,
    organization_name: str = "",
) -> ReportResponse:
    """自己評価レポートを生成しPDF出力.

    Args:
        assessment: 診断結果
        gap_analysis: ギャップ分析結果
        evidence_summary: エビデンス充足率サマリー
        organization_name: 組織名

    Returns:
        ReportResponse: レポート情報
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    report_id = str(uuid.uuid4())
    filename = f"ai_governance_report_{report_id[:8]}.pdf"
    filepath = REPORTS_DIR / filename

    pdf = JapaneseReport()

    # Title
    pdf._add_title("AI Governance Self-Assessment Report")
    pdf._add_text(
        f"Organization: {organization_name or assessment.organization_id}"
    )
    pdf._add_text(
        f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    )
    pdf._add_text(
        "Based on: METI AI Guidelines for Business (v1.0, April 2024)"
    )
    pdf.ln(5)

    # 1. Executive Summary
    pdf._add_section("1. Executive Summary")
    pdf._add_text(
        f"Overall Maturity: {_maturity_label(assessment.maturity_level)}"
    )
    pdf._add_text(f"Overall Score: {assessment.overall_score:.2f} / 4.00")
    pdf._add_text(
        f"Requirements Status: "
        f"Compliant={gap_analysis.compliant_count}, "
        f"Partial={gap_analysis.partial_count}, "
        f"Non-Compliant={gap_analysis.non_compliant_count}"
    )
    pdf.ln(3)

    # 2. Category Scores
    pdf._add_section("2. Category Assessment Results")
    widths = [20, 80, 25, 25, 30]
    pdf._add_table_row(["ID", "Category", "Score", "Max", "Maturity"], widths, bold=True)
    for cs in assessment.category_scores:
        pdf._add_table_row(
            [cs.category_id, cs.category_title[:30], f"{cs.score:.2f}", "4.00", f"Level {cs.maturity_level}"],
            widths,
        )
    pdf.ln(5)

    # 3. Gap Analysis
    pdf._add_section("3. Gap Analysis - Non-Compliant Requirements")
    non_compliant = [g for g in gap_analysis.gaps if g.status == ComplianceStatus.NON_COMPLIANT]
    if non_compliant:
        widths2 = [25, 60, 30, 25, 40]
        pdf._add_table_row(["Req ID", "Title", "Status", "Score", "Priority"], widths2, bold=True)
        for gap in non_compliant:
            pdf._add_table_row(
                [gap.req_id, gap.title[:25], _status_label(gap.status), f"{gap.current_score:.2f}", gap.priority],
                widths2,
            )
    else:
        pdf._add_text("No non-compliant requirements found.")
    pdf.ln(3)

    # 4. Partial Compliance
    pdf._add_section("4. Gap Analysis - Partially Compliant Requirements")
    partial = [g for g in gap_analysis.gaps if g.status == ComplianceStatus.PARTIAL]
    if partial:
        widths2 = [25, 60, 30, 25, 40]
        pdf._add_table_row(["Req ID", "Title", "Status", "Score", "Priority"], widths2, bold=True)
        for gap in partial:
            pdf._add_table_row(
                [gap.req_id, gap.title[:25], _status_label(gap.status), f"{gap.current_score:.2f}", gap.priority],
                widths2,
            )
    else:
        pdf._add_text("No partially compliant requirements found.")
    pdf.ln(3)

    # 5. Evidence Coverage
    if evidence_summary:
        pdf._add_section("5. Evidence Coverage")
        pdf._add_text(
            f"Overall Coverage: {evidence_summary.coverage_rate:.0%} "
            f"({evidence_summary.requirements_with_evidence}/{evidence_summary.total_requirements})"
        )
        widths3 = [20, 80, 30, 30]
        pdf._add_table_row(["ID", "Category", "Covered", "Total"], widths3, bold=True)
        for cat_id, info in evidence_summary.by_category.items():
            pdf._add_table_row(
                [cat_id, str(info.get("title", ""))[:30], str(info.get("covered", 0)), str(info.get("total", 0))],
                widths3,
            )
        pdf.ln(3)

    # 6. Improvement Recommendations
    pdf._add_section("6. Improvement Recommendations")
    if gap_analysis.ai_recommendations:
        # PDF doesn't handle Japanese well without font, so keep ASCII-safe
        rec_text = gap_analysis.ai_recommendations[:2000]
        pdf._add_text(rec_text)
    pdf.ln(3)

    # 7. Appendix
    pdf._add_section("7. Appendix - All Requirements Status")
    widths4 = [25, 70, 30, 25]
    pdf._add_table_row(["Req ID", "Title", "Status", "Score"], widths4, bold=True)
    for gap in gap_analysis.gaps:
        pdf._add_table_row(
            [gap.req_id, gap.title[:28], _status_label(gap.status), f"{gap.current_score:.2f}"],
            widths4,
        )

    # Save PDF
    pdf.output(str(filepath))

    # DB保存
    db = get_db()
    with db.get_session() as session:
        row = ReportRow(
            id=report_id,
            organization_id=assessment.organization_id,
            assessment_id=assessment.id,
            gap_analysis_id=gap_analysis.id,
            filename=filename,
        )
        session.add(row)
        session.commit()

    return ReportResponse(
        id=report_id,
        organization_id=assessment.organization_id,
        filename=filename,
        content_preview=f"AI Governance Report - Maturity Level {assessment.maturity_level}",
    )
