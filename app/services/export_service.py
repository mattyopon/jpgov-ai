# Copyright (c) 2026 Yutaro Maeda
# Licensed under the MIT License. See LICENSE file for details.

"""エクスポートサービス.

全データのCSV/JSONエクスポート、
ISO 42001認証申請用の文書パッケージ一括生成、
METI報告用フォーマットでのエクスポートを提供する。
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone

from app.models import (
    AssessmentResult,
    ExportFormat,
    ExportPackage,
    GapAnalysisResult,
    ISOCheckResult,
)


def _assessment_to_rows(assessment: AssessmentResult) -> list[dict]:
    """Assessment結果をCSV用の行に変換."""
    rows = []
    for cs in assessment.category_scores:
        rows.append({
            "category_id": cs.category_id,
            "category_title": cs.category_title,
            "score": cs.score,
            "max_score": cs.max_score,
            "maturity_level": cs.maturity_level,
            "question_count": cs.question_count,
        })
    return rows


def _gaps_to_rows(gap_result: GapAnalysisResult) -> list[dict]:
    """ギャップ分析結果をCSV用の行に変換."""
    rows = []
    for gap in gap_result.gaps:
        rows.append({
            "req_id": gap.req_id,
            "category_id": gap.category_id,
            "title": gap.title,
            "status": gap.status.value,
            "current_score": gap.current_score,
            "priority": gap.priority,
            "gap_description": gap.gap_description,
            "improvement_actions": "; ".join(gap.improvement_actions),
        })
    return rows


def _iso_check_to_rows(iso_result: ISOCheckResult) -> list[dict]:
    """ISO チェック結果をCSV用の行に変換."""
    rows = []
    for item in iso_result.items:
        rows.append({
            "req_id": item.req_id,
            "clause": item.clause,
            "title": item.title,
            "status": item.status.value,
            "score": item.score,
            "meti_mapping": "; ".join(item.meti_mapping),
        })
    return rows


def export_to_csv(rows: list[dict]) -> str:
    """辞書のリストをCSV文字列に変換."""
    if not rows:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def export_to_json(data: dict | list) -> str:
    """データをJSON文字列に変換."""
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def export_assessment(
    assessment: AssessmentResult,
    fmt: ExportFormat = ExportFormat.JSON,
) -> str:
    """Assessment結果をエクスポート."""
    if fmt == ExportFormat.CSV:
        return export_to_csv(_assessment_to_rows(assessment))
    return export_to_json(assessment.model_dump())


def export_gap_analysis(
    gap_result: GapAnalysisResult,
    fmt: ExportFormat = ExportFormat.JSON,
) -> str:
    """ギャップ分析結果をエクスポート."""
    if fmt == ExportFormat.CSV:
        return export_to_csv(_gaps_to_rows(gap_result))
    return export_to_json(gap_result.model_dump())


def export_iso_check(
    iso_result: ISOCheckResult,
    fmt: ExportFormat = ExportFormat.JSON,
) -> str:
    """ISO チェック結果をエクスポート."""
    if fmt == ExportFormat.CSV:
        return export_to_csv(_iso_check_to_rows(iso_result))
    return export_to_json(iso_result.model_dump())


def generate_iso_certification_package(
    assessment: AssessmentResult,
    gap_result: GapAnalysisResult,
    iso_result: ISOCheckResult,
    organization_name: str = "",
) -> ExportPackage:
    """ISO 42001認証申請用の文書パッケージを生成.

    Args:
        assessment: 診断結果
        gap_result: ギャップ分析結果
        iso_result: ISO チェック結果
        organization_name: 組織名

    Returns:
        ExportPackage: 文書パッケージ
    """
    now = datetime.now(timezone.utc).strftime("%Y%m%d")

    files: dict[str, str] = {
        f"01_assessment_results_{now}.json": export_assessment(assessment, ExportFormat.JSON),
        f"02_assessment_results_{now}.csv": export_assessment(assessment, ExportFormat.CSV),
        f"03_gap_analysis_{now}.json": export_gap_analysis(gap_result, ExportFormat.JSON),
        f"04_gap_analysis_{now}.csv": export_gap_analysis(gap_result, ExportFormat.CSV),
        f"05_iso42001_check_{now}.json": export_iso_check(iso_result, ExportFormat.JSON),
        f"06_iso42001_check_{now}.csv": export_iso_check(iso_result, ExportFormat.CSV),
    }

    # サマリー文書
    summary_lines = [
        "# ISO/IEC 42001 認証申請パッケージ",
        "",
        f"**組織名**: {organization_name or assessment.organization_id}",
        f"**作成日**: {datetime.now(timezone.utc).strftime('%Y年%m月%d日')}",
        "",
        "## 1. 診断結果サマリー",
        f"- 総合スコア: {assessment.overall_score:.2f} / 4.00",
        f"- 成熟度レベル: Level {assessment.maturity_level}",
        "",
        "## 2. ギャップ分析サマリー",
        f"- 充足: {gap_result.compliant_count}件",
        f"- 部分充足: {gap_result.partial_count}件",
        f"- 未充足: {gap_result.non_compliant_count}件",
        "",
        "## 3. ISO 42001 準拠状況",
        f"- 全要求事項: {iso_result.total_requirements}件",
        f"- 充足: {iso_result.compliant_count}件",
        f"- 部分充足: {iso_result.partial_count}件",
        f"- 未充足: {iso_result.non_compliant_count}件",
        f"- 総合スコア: {iso_result.overall_score:.2f} / 4.00",
        "",
        "## 4. 含まれるファイル",
    ]
    for filename in sorted(files.keys()):
        summary_lines.append(f"- {filename}")

    files[f"00_summary_{now}.md"] = "\n".join(summary_lines)

    return ExportPackage(
        organization_id=assessment.organization_id,
        package_type="iso42001_certification",
        files=files,
    )


def generate_meti_report_package(
    assessment: AssessmentResult,
    gap_result: GapAnalysisResult,
    organization_name: str = "",
) -> ExportPackage:
    """METI報告用フォーマットでエクスポート.

    Args:
        assessment: 診断結果
        gap_result: ギャップ分析結果
        organization_name: 組織名

    Returns:
        ExportPackage: 文書パッケージ
    """
    now = datetime.now(timezone.utc).strftime("%Y%m%d")

    files: dict[str, str] = {
        f"meti_assessment_{now}.csv": export_assessment(assessment, ExportFormat.CSV),
        f"meti_gap_analysis_{now}.csv": export_gap_analysis(gap_result, ExportFormat.CSV),
        f"meti_full_data_{now}.json": export_to_json({
            "assessment": assessment.model_dump(),
            "gap_analysis": gap_result.model_dump(),
        }),
    }

    # METI報告用サマリー
    summary_lines = [
        "# METI AI事業者ガイドライン 準拠状況報告",
        "",
        f"**組織名**: {organization_name or assessment.organization_id}",
        f"**報告日**: {datetime.now(timezone.utc).strftime('%Y年%m月%d日')}",
        "**対象ガイドライン**: AI事業者ガイドライン（第1.0版）",
        "",
        "## 総合評価",
        f"- 総合スコア: {assessment.overall_score:.2f} / 4.00",
        f"- 成熟度レベル: Level {assessment.maturity_level}",
        "",
        "## カテゴリ別評価",
    ]
    for cs in assessment.category_scores:
        summary_lines.append(f"- {cs.category_id} {cs.category_title}: {cs.score:.2f} (Level {cs.maturity_level})")

    summary_lines.extend([
        "",
        "## ギャップ分析",
        f"- 充足: {gap_result.compliant_count}件",
        f"- 部分充足: {gap_result.partial_count}件",
        f"- 未充足: {gap_result.non_compliant_count}件",
    ])

    files[f"meti_summary_{now}.md"] = "\n".join(summary_lines)

    return ExportPackage(
        organization_id=assessment.organization_id,
        package_type="meti_report",
        files=files,
    )
