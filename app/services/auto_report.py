# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""月次自動レポートサービス.

毎月のレポートを自動生成するロジック:
- 今月のスコア変動
- 新規発見Gapと対応状況
- インシデント件数と対応状況
- エビデンスカバレッジ率
- 業界ベンチマークとの比較
- 次月のアクション推奨
"""

from __future__ import annotations

import json

from app.db.database import MonthlyReportRow, get_db
from app.models import MonthlyReport


def generate_monthly_report(
    organization_id: str,
    year: int,
    month: int,
    score_summary: dict | None = None,
    gap_summary: dict | None = None,
    incident_summary: dict | None = None,
    evidence_coverage: float = 0.0,
    benchmark_comparison: dict | None = None,
    recommendations: list[str] | None = None,
) -> MonthlyReport:
    """月次レポートを生成.

    Args:
        organization_id: 組織ID
        year: 年
        month: 月
        score_summary: スコア変動サマリー
        gap_summary: Gap対応サマリー
        incident_summary: インシデントサマリー
        evidence_coverage: エビデンスカバレッジ率
        benchmark_comparison: ベンチマーク比較
        recommendations: アクション推奨

    Returns:
        MonthlyReport: 生成されたレポート
    """
    report = MonthlyReport(
        organization_id=organization_id,
        year=year,
        month=month,
        score_summary=score_summary or {},
        gap_summary=gap_summary or {},
        incident_summary=incident_summary or {},
        evidence_coverage=evidence_coverage,
        benchmark_comparison=benchmark_comparison or {},
        recommendations=recommendations or [],
    )

    db = get_db()
    with db.get_session() as session:
        row = MonthlyReportRow(
            id=report.id,
            organization_id=report.organization_id,
            year=report.year,
            month=report.month,
            report_json=json.dumps(
                {
                    "score_summary": report.score_summary,
                    "gap_summary": report.gap_summary,
                    "incident_summary": report.incident_summary,
                    "evidence_coverage": report.evidence_coverage,
                    "benchmark_comparison": report.benchmark_comparison,
                    "recommendations": report.recommendations,
                },
                ensure_ascii=False,
            ),
            generated_at=report.generated_at,
        )
        session.add(row)
        session.commit()

    return report


def get_monthly_report(
    organization_id: str,
    year: int,
    month: int,
) -> MonthlyReport | None:
    """月次レポートを取得.

    Args:
        organization_id: 組織ID
        year: 年
        month: 月

    Returns:
        MonthlyReport | None: レポート、またはNone
    """
    db = get_db()
    with db.get_session() as session:
        row = (
            session.query(MonthlyReportRow)
            .filter_by(organization_id=organization_id, year=year, month=month)
            .first()
        )
        if row is None:
            return None
        return _row_to_model(row)


def list_monthly_reports(organization_id: str) -> list[MonthlyReport]:
    """月次レポート一覧を取得.

    Args:
        organization_id: 組織ID

    Returns:
        list[MonthlyReport]: レポートリスト
    """
    db = get_db()
    with db.get_session() as session:
        rows = (
            session.query(MonthlyReportRow)
            .filter_by(organization_id=organization_id)
            .order_by(MonthlyReportRow.year.desc(), MonthlyReportRow.month.desc())
            .all()
        )
        return [_row_to_model(r) for r in rows]


def build_monthly_report_data(
    organization_id: str,
    year: int,
    month: int,
) -> MonthlyReport:
    """月次レポートデータを収集して生成.

    各サービスからデータを集約し、レポートを自動生成する。

    Args:
        organization_id: 組織ID
        year: 年
        month: 月

    Returns:
        MonthlyReport: 自動生成されたレポート
    """
    # スコアサマリー
    score_summary = _collect_score_summary(organization_id)

    # Gapサマリー
    gap_summary = _collect_gap_summary(organization_id)

    # インシデントサマリー
    incident_summary = _collect_incident_summary(organization_id)

    # エビデンスカバレッジ
    evidence_coverage = _collect_evidence_coverage(organization_id)

    # ベンチマーク比較
    benchmark_comparison = _collect_benchmark_comparison(organization_id)

    # アクション推奨
    recommendations = _generate_recommendations(
        score_summary, gap_summary, incident_summary, evidence_coverage,
    )

    return generate_monthly_report(
        organization_id=organization_id,
        year=year,
        month=month,
        score_summary=score_summary,
        gap_summary=gap_summary,
        incident_summary=incident_summary,
        evidence_coverage=evidence_coverage,
        benchmark_comparison=benchmark_comparison,
        recommendations=recommendations,
    )


def _collect_score_summary(organization_id: str) -> dict:
    """スコア変動サマリーを収集."""
    try:
        from app.services.timeline import get_timeline
        timeline = get_timeline(organization_id)
        entries = timeline.entries
        if not entries:
            return {"current_score": 0.0, "trend": "no_data"}

        latest = entries[-1]
        previous = entries[-2] if len(entries) > 1 else None
        delta = latest.delta_from_previous

        return {
            "current_score": latest.overall_score,
            "current_level": latest.maturity_level,
            "delta": delta,
            "trend": timeline.trend,
            "data_points": len(entries),
        }
    except Exception:
        return {"current_score": 0.0, "trend": "no_data"}


def _collect_gap_summary(organization_id: str) -> dict:
    """Gapサマリーを収集."""
    try:
        from app.services.task_manager import get_board_summary
        board = get_board_summary(organization_id)
        return {
            "total_tasks": board.total,
            "todo": board.todo_count,
            "in_progress": board.in_progress_count,
            "done": board.done_count,
            "overdue": board.overdue_count,
        }
    except Exception:
        return {}


def _collect_incident_summary(organization_id: str) -> dict:
    """インシデントサマリーを収集."""
    try:
        from app.services.incident_management import get_incident_stats
        stats = get_incident_stats(organization_id)
        return {
            "total": stats.total_count,
            "open": stats.open_count,
            "by_severity": stats.by_severity,
            "by_type": stats.by_type,
            "avg_resolution_hours": stats.avg_resolution_hours,
        }
    except Exception:
        return {}


def _collect_evidence_coverage(organization_id: str) -> float:
    """エビデンスカバレッジを収集."""
    try:
        from app.services.evidence import get_evidence_coverage_rate
        return get_evidence_coverage_rate(organization_id)
    except Exception:
        return 0.0


def _collect_benchmark_comparison(organization_id: str) -> dict:
    """ベンチマーク比較を収集."""
    # ベンチマークデータは業界情報が必要なので、空を返す
    return {}


def _generate_recommendations(
    score_summary: dict,
    gap_summary: dict,
    incident_summary: dict,
    evidence_coverage: float,
) -> list[str]:
    """アクション推奨を生成."""
    recommendations: list[str] = []

    # スコアに基づく推奨
    delta = score_summary.get("delta", 0)
    if delta < 0:
        recommendations.append(
            "成熟度スコアが低下しています。低下領域のギャップ分析を再実行してください。"
        )
    elif delta == 0 and score_summary.get("current_score", 0) > 0:
        recommendations.append(
            "スコアが横ばいです。改善タスクの進捗を確認してください。"
        )

    # タスクに基づく推奨
    overdue = gap_summary.get("overdue", 0)
    if overdue > 0:
        recommendations.append(
            f"期限超過のタスクが{overdue}件あります。優先的に対応してください。"
        )

    todo = gap_summary.get("todo", 0)
    if todo > 5:
        recommendations.append(
            f"未着手タスクが{todo}件あります。担当者を割り当ててください。"
        )

    # インシデントに基づく推奨
    open_incidents = incident_summary.get("open", 0)
    if open_incidents > 0:
        recommendations.append(
            f"未解決のインシデントが{open_incidents}件あります。対応を進めてください。"
        )

    # エビデンスに基づく推奨
    if evidence_coverage < 0.5:
        recommendations.append(
            f"エビデンスカバレッジが{evidence_coverage:.0%}です。"
            "不足している要件のエビデンスを優先的にアップロードしてください。"
        )
    elif evidence_coverage < 0.8:
        recommendations.append(
            f"エビデンスカバレッジが{evidence_coverage:.0%}です。"
            "80%以上を目指してください。"
        )

    if not recommendations:
        recommendations.append("良好な状態です。引き続き定期レビューを実施してください。")

    return recommendations


def _row_to_model(row: MonthlyReportRow) -> MonthlyReport:
    """DBの行をモデルに変換."""
    data = json.loads(row.report_json)
    return MonthlyReport(
        id=row.id,
        organization_id=row.organization_id,
        year=row.year,
        month=row.month,
        score_summary=data.get("score_summary", {}),
        gap_summary=data.get("gap_summary", {}),
        incident_summary=data.get("incident_summary", {}),
        evidence_coverage=data.get("evidence_coverage", 0.0),
        benchmark_comparison=data.get("benchmark_comparison", {}),
        recommendations=data.get("recommendations", []),
        generated_at=row.generated_at,
    )
