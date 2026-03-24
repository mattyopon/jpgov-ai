# Copyright (c) 2026 Yutaro Maeda
# Licensed under the MIT License. See LICENSE file for details.

"""マルチ規制ダッシュボードサービス.

METI + ISO 42001 + AI推進法の3規制の準拠状況を一元管理する。
"""

from __future__ import annotations

from app.guidelines.ai_promotion_act import all_act_requirements
from app.models import (
    ComplianceStatus,
    GapAnalysisResult,
    ISOCheckResult,
    MultiRegulationDashboard,
    RegulationStatus,
)


def _calc_act_status(gap_result: GapAnalysisResult) -> RegulationStatus:
    """AI推進法の準拠状況をMETI結果から推定."""
    act_reqs = all_act_requirements()
    gap_map = {g.req_id: g for g in gap_result.gaps}

    compliant = 0
    partial = 0
    non_compliant = 0
    scores: list[float] = []

    for act_req in act_reqs:
        # METI要件のスコアから推定
        meti_scores = []
        for meti_id in act_req.meti_mapping:
            gap = gap_map.get(meti_id)
            if gap is not None:
                meti_scores.append(gap.current_score)

        if meti_scores:
            avg = sum(meti_scores) / len(meti_scores)
            scores.append(avg)
            if avg >= 3.0:
                compliant += 1
            elif avg >= 1.5:
                partial += 1
            else:
                non_compliant += 1
        else:
            non_compliant += 1
            scores.append(0.0)

    total = len(act_reqs)
    overall = sum(scores) / len(scores) if scores else 0.0
    rate = compliant / total if total > 0 else 0.0

    return RegulationStatus(
        regulation_name="AI推進法（2025年施行）",
        total_requirements=total,
        compliant_count=compliant,
        partial_count=partial,
        non_compliant_count=non_compliant,
        compliance_rate=round(rate, 3),
        overall_score=round(overall, 2),
    )


def _calc_meti_status(gap_result: GapAnalysisResult) -> RegulationStatus:
    """METI準拠状況."""
    total = gap_result.total_requirements
    rate = gap_result.compliant_count / total if total > 0 else 0.0
    scores = [g.current_score for g in gap_result.gaps]
    overall = sum(scores) / len(scores) if scores else 0.0

    return RegulationStatus(
        regulation_name="METI AI事業者ガイドライン v1.0",
        total_requirements=total,
        compliant_count=gap_result.compliant_count,
        partial_count=gap_result.partial_count,
        non_compliant_count=gap_result.non_compliant_count,
        compliance_rate=round(rate, 3),
        overall_score=round(overall, 2),
    )


def _calc_iso_status(iso_result: ISOCheckResult) -> RegulationStatus:
    """ISO 42001準拠状況."""
    total = iso_result.total_requirements
    rate = iso_result.compliant_count / total if total > 0 else 0.0

    return RegulationStatus(
        regulation_name="ISO/IEC 42001:2023 (AIMS)",
        total_requirements=total,
        compliant_count=iso_result.compliant_count,
        partial_count=iso_result.partial_count,
        non_compliant_count=iso_result.non_compliant_count,
        compliance_rate=round(rate, 3),
        overall_score=round(iso_result.overall_score, 2),
    )


def _collect_priority_actions(
    gap_result: GapAnalysisResult,
    iso_result: ISOCheckResult | None = None,
) -> list[dict]:
    """3規制横断の優先アクションを収集."""
    actions: list[dict] = []

    # METI未充足要件
    for gap in gap_result.gaps:
        if gap.status == ComplianceStatus.NON_COMPLIANT:
            actions.append({
                "source": "METI",
                "req_id": gap.req_id,
                "title": gap.title,
                "priority": gap.priority,
                "actions": gap.improvement_actions[:2],
            })

    # ISO未充足要件
    if iso_result:
        for item in iso_result.items:
            if item.status == ComplianceStatus.NON_COMPLIANT:
                actions.append({
                    "source": "ISO 42001",
                    "req_id": item.req_id,
                    "title": item.title,
                    "priority": "high",
                    "actions": [f"METI要件 {', '.join(item.meti_mapping)} の充足により改善"],
                })

    # 優先度でソート (high > medium > low)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    actions.sort(key=lambda a: priority_order.get(a.get("priority", "medium"), 1))

    return actions[:20]  # 上位20件


def build_multi_regulation_dashboard(
    organization_id: str,
    gap_result: GapAnalysisResult,
    iso_result: ISOCheckResult | None = None,
) -> MultiRegulationDashboard:
    """マルチ規制ダッシュボードを生成.

    Args:
        organization_id: 組織ID
        gap_result: METIギャップ分析結果
        iso_result: ISO 42001チェック結果（省略可能）

    Returns:
        MultiRegulationDashboard: ダッシュボードデータ
    """
    meti_status = _calc_meti_status(gap_result)
    act_status = _calc_act_status(gap_result)
    iso_status = _calc_iso_status(iso_result) if iso_result else None

    rates = [meti_status.compliance_rate, act_status.compliance_rate]
    if iso_status:
        rates.append(iso_status.compliance_rate)
    overall_rate = sum(rates) / len(rates) if rates else 0.0

    priority_actions = _collect_priority_actions(gap_result, iso_result)

    return MultiRegulationDashboard(
        organization_id=organization_id,
        meti_status=meti_status,
        iso_status=iso_status,
        act_status=act_status,
        overall_compliance_rate=round(overall_rate, 3),
        priority_actions=priority_actions,
    )
