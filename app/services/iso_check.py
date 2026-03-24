# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""ISO/IEC 42001 (AIMS) 対応チェックサービス.

ISO 42001の要求事項に対する準拠状況を評価し、
METI AI事業者ガイドラインとのクロスマッピングを提供する。
"""

from __future__ import annotations

from app.guidelines.iso42001 import (
    ISO_CLAUSES,
    all_iso_requirements,
    get_iso_to_meti_mapping,
)
from app.guidelines.meti_v1_1 import get_requirement as get_meti_requirement
from app.models import (
    ComplianceStatus,
    GapAnalysisResult,
    ISOCheckItem,
    ISOCheckResult,
    ISOClauseSummary,
)


def _meti_status_to_score(gap_result: GapAnalysisResult, meti_ids: list[str]) -> float:
    """METI要件のギャップ分析結果からISO対応スコアを推定."""
    if not meti_ids or not gap_result.gaps:
        return 0.0
    gap_map = {g.req_id: g for g in gap_result.gaps}
    scores = []
    for meti_id in meti_ids:
        gap = gap_map.get(meti_id)
        if gap is not None:
            scores.append(gap.current_score)
    return sum(scores) / len(scores) if scores else 0.0


def _score_to_status(score: float) -> ComplianceStatus:
    """スコアからISO準拠状態を判定."""
    if score >= 3.0:
        return ComplianceStatus.COMPLIANT
    elif score >= 1.5:
        return ComplianceStatus.PARTIAL
    elif score > 0.0:
        return ComplianceStatus.NON_COMPLIANT
    return ComplianceStatus.NOT_ASSESSED


def run_iso_check(gap_result: GapAnalysisResult) -> ISOCheckResult:
    """METI準拠状況の結果を使ってISO 42001の準拠状況を評価.

    Args:
        gap_result: METIギャップ分析結果

    Returns:
        ISOCheckResult: ISO 42001チェック結果
    """
    iso_to_meti = get_iso_to_meti_mapping()
    all_reqs = all_iso_requirements()

    items: list[ISOCheckItem] = []
    clause_scores: dict[str, list[float]] = {}

    for req in all_reqs:
        meti_ids = iso_to_meti.get(req.req_id, [])
        score = _meti_status_to_score(gap_result, meti_ids)
        status = _score_to_status(score)

        # METI要件名を取得
        meti_titles = []
        for mid in meti_ids:
            mr = get_meti_requirement(mid)
            if mr:
                meti_titles.append(f"{mid}: {mr.title}")

        items.append(
            ISOCheckItem(
                req_id=req.req_id,
                clause=req.clause,
                title=req.title,
                description=req.description,
                status=status,
                score=round(score, 2),
                meti_mapping=meti_ids,
                meti_mapping_titles=meti_titles,
            )
        )

        clause_id = req.clause.split(".")[0]
        clause_scores.setdefault(clause_id, []).append(score)

    # 条項別サマリー
    clause_summaries: list[ISOClauseSummary] = []
    for clause in ISO_CLAUSES:
        scores = clause_scores.get(clause.clause_id, [])
        avg = sum(scores) / len(scores) if scores else 0.0
        total = len(clause.requirements)
        compliant = sum(
            1 for item in items
            if item.clause.startswith(clause.clause_id + ".")
            or item.clause == clause.clause_id
            if item.status == ComplianceStatus.COMPLIANT
        )
        clause_summaries.append(
            ISOClauseSummary(
                clause_id=clause.clause_id,
                title=clause.title,
                total_requirements=total,
                compliant_count=compliant,
                avg_score=round(avg, 2),
                status=_score_to_status(avg),
            )
        )

    # 全体集計
    total = len(items)
    c_count = sum(1 for i in items if i.status == ComplianceStatus.COMPLIANT)
    p_count = sum(1 for i in items if i.status == ComplianceStatus.PARTIAL)
    nc_count = sum(1 for i in items if i.status == ComplianceStatus.NON_COMPLIANT)
    na_count = sum(1 for i in items if i.status == ComplianceStatus.NOT_ASSESSED)
    all_scores = [i.score for i in items]
    overall = sum(all_scores) / len(all_scores) if all_scores else 0.0

    return ISOCheckResult(
        organization_id=gap_result.organization_id,
        gap_analysis_id=gap_result.id,
        total_requirements=total,
        compliant_count=c_count,
        partial_count=p_count,
        non_compliant_count=nc_count,
        not_assessed_count=na_count,
        overall_score=round(overall, 2),
        items=items,
        clause_summaries=clause_summaries,
    )
