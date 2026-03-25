# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Citadel AI連携インターフェース.

Citadel AIのモデル監視データをJPGovAIのエビデンスとして
インポートする連携機能を提供する。

Citadel AIの主な機能:
- モデル品質スコア
- バイアス検出
- データドリフト検出
- 敵対的攻撃テスト
- 説明可能性レポート
- モデルカード生成
- アラート通知

本モジュールはインターフェース定義。
実API実装はCitadel AIのAPI公開後に追加する。
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any


# ── Citadel AI -> METI/ISO 要件マッピング ─────────────────

CITADEL_TO_REQUIREMENT_MAP: dict[str, dict[str, list[str]]] = {
    "model_quality": {
        "meti": ["C02-R02"],
        "iso42001": ["ISO-6.1.2"],
        "description": "モデルの品質が管理されている証拠",
    },
    "bias_detection": {
        "meti": ["C03-R01"],
        "iso42001": ["ISO-8.4"],
        "description": "公平性の定期的な評価の証拠",
    },
    "data_drift": {
        "meti": ["C02-R01"],
        "iso42001": ["ISO-8.2"],
        "description": "継続的なリスクモニタリングの証拠",
    },
    "adversarial_test": {
        "meti": ["C05-R01"],
        "iso42001": ["ISO-8.3"],
        "description": "セキュリティ対策の証拠",
    },
    "explainability": {
        "meti": ["C06-R02"],
        "iso42001": ["ISO-7.4"],
        "description": "透明性確保の証拠",
    },
    "model_card": {
        "meti": ["C06-R03"],
        "iso42001": ["ISO-7.5"],
        "description": "文書化の証拠",
    },
    "alert_history": {
        "meti": ["C05-R03"],
        "iso42001": ["ISO-10.1"],
        "description": "インシデント検知体制の証拠",
    },
}


# ── Data Models ──────────────────────────────────────────

class CitadelMonitoringReport:
    """Citadel AIの監視レポート（変換前のデータ構造）."""

    def __init__(
        self,
        report_id: str = "",
        model_id: str = "",
        model_name: str = "",
        report_type: str = "",
        timestamp: str = "",
        metrics: dict[str, Any] | None = None,
        summary: str = "",
        status: str = "normal",  # normal / warning / critical
        details: dict[str, Any] | None = None,
    ) -> None:
        self.report_id = report_id or str(uuid.uuid4())
        self.model_id = model_id
        self.model_name = model_name
        self.report_type = report_type
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.metrics = metrics or {}
        self.summary = summary
        self.status = status
        self.details = details or {}


class CitadelAlert:
    """Citadel AIのアラート（変換前のデータ構造）."""

    def __init__(
        self,
        alert_id: str = "",
        model_id: str = "",
        model_name: str = "",
        alert_type: str = "",
        severity: str = "medium",
        message: str = "",
        timestamp: str = "",
        metrics: dict[str, Any] | None = None,
    ) -> None:
        self.alert_id = alert_id or str(uuid.uuid4())
        self.model_id = model_id
        self.model_name = model_name
        self.alert_type = alert_type
        self.severity = severity
        self.message = message
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.metrics = metrics or {}


class EvidenceFromCitadel:
    """Citadel AIから変換されたエビデンス."""

    def __init__(
        self,
        source_report_id: str = "",
        source_type: str = "",
        requirement_ids: list[str] | None = None,
        title: str = "",
        description: str = "",
        evidence_data: dict[str, Any] | None = None,
        timestamp: str = "",
    ) -> None:
        self.id = str(uuid.uuid4())
        self.source_report_id = source_report_id
        self.source_type = source_type
        self.requirement_ids = requirement_ids or []
        self.title = title
        self.description = description
        self.evidence_data = evidence_data or {}
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換."""
        return {
            "id": self.id,
            "source_report_id": self.source_report_id,
            "source_type": self.source_type,
            "requirement_ids": self.requirement_ids,
            "title": self.title,
            "description": self.description,
            "evidence_data": self.evidence_data,
            "timestamp": self.timestamp,
        }


class IncidentFromCitadel:
    """Citadel AIのアラートから変換されたインシデント."""

    def __init__(
        self,
        source_alert_id: str = "",
        title: str = "",
        description: str = "",
        severity: str = "medium",
        incident_type: str = "quality",
        affected_system: str = "",
        related_requirements: list[str] | None = None,
        timestamp: str = "",
    ) -> None:
        self.id = str(uuid.uuid4())
        self.source_alert_id = source_alert_id
        self.title = title
        self.description = description
        self.severity = severity
        self.incident_type = incident_type
        self.affected_system = affected_system
        self.related_requirements = related_requirements or []
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換."""
        return {
            "id": self.id,
            "source_alert_id": self.source_alert_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "incident_type": self.incident_type,
            "affected_system": self.affected_system,
            "related_requirements": self.related_requirements,
            "timestamp": self.timestamp,
        }


# ── CitadelAPIClient (Interface) ─────────────────────────

class CitadelAPIClient:
    """Citadel AIのAPIクライアント（インターフェース定義）.

    実API実装はCitadel AIのAPI公開後に追加する。
    現時点ではメソッドシグネチャのみ定義。
    """

    def __init__(
        self,
        api_url: str = "",
        api_key: str = "",
    ) -> None:
        self.api_url = api_url
        self.api_key = api_key
        self._connected = bool(api_url and api_key)

    @property
    def is_connected(self) -> bool:
        """接続状態を返す."""
        return self._connected

    def get_monitoring_reports(
        self,
        model_id: str = "",
        report_type: str = "",
        since: str = "",
    ) -> list[CitadelMonitoringReport]:
        """監視レポートを取得（API未実装: 空リスト返却）."""
        return []

    def get_alerts(
        self,
        model_id: str = "",
        severity: str = "",
        since: str = "",
    ) -> list[CitadelAlert]:
        """アラートを取得（API未実装: 空リスト返却）."""
        return []

    def get_model_card(self, model_id: str) -> dict[str, Any]:
        """モデルカードを取得（API未実装: 空辞書返却）."""
        return {}


# ── Data Transformer ─────────────────────────────────────

class CitadelDataTransformer:
    """Citadel AIのデータをJPGovAI形式に変換.

    Citadel AIの出力形式 -> JPGovAIのエビデンス/インシデント形式。
    """

    @staticmethod
    def report_to_evidence(
        report: CitadelMonitoringReport,
    ) -> EvidenceFromCitadel:
        """監視レポートをエビデンスに変換.

        Args:
            report: Citadel AIの監視レポート

        Returns:
            JPGovAI形式のエビデンス
        """
        mapping = CITADEL_TO_REQUIREMENT_MAP.get(report.report_type, {})
        meti_reqs = mapping.get("meti", [])
        description_suffix = mapping.get("description", "")

        return EvidenceFromCitadel(
            source_report_id=report.report_id,
            source_type=report.report_type,
            requirement_ids=meti_reqs,
            title=f"Citadel AI: {report.model_name} - {report.report_type}",
            description=(
                f"{report.summary}\n"
                f"ステータス: {report.status}\n"
                f"エビデンスとしての価値: {description_suffix}"
            ),
            evidence_data={
                "model_id": report.model_id,
                "model_name": report.model_name,
                "metrics": report.metrics,
                "status": report.status,
            },
            timestamp=report.timestamp,
        )

    @staticmethod
    def alert_to_incident(
        alert: CitadelAlert,
    ) -> IncidentFromCitadel:
        """アラートをインシデントに変換.

        Args:
            alert: Citadel AIのアラート

        Returns:
            JPGovAI形式のインシデント
        """
        # アラートタイプからインシデントタイプへのマッピング
        type_map: dict[str, str] = {
            "bias_detected": "bias",
            "drift_detected": "quality",
            "adversarial_detected": "security_breach",
            "quality_degradation": "quality",
            "anomaly": "other",
        }
        incident_type = type_map.get(alert.alert_type, "other")

        # アラートタイプから関連要件へのマッピング
        mapping = CITADEL_TO_REQUIREMENT_MAP.get(
            alert.alert_type.replace("_detected", "").replace("_degradation", ""),
            {},
        )
        related_reqs = mapping.get("meti", [])

        return IncidentFromCitadel(
            source_alert_id=alert.alert_id,
            title=f"[Citadel AI] {alert.message}",
            description=(
                f"Citadel AIがモデル '{alert.model_name}' で異常を検知しました。\n"
                f"アラート種別: {alert.alert_type}\n"
                f"メトリクス: {json.dumps(alert.metrics, ensure_ascii=False) if alert.metrics else 'N/A'}"
            ),
            severity=alert.severity,
            incident_type=incident_type,
            affected_system=alert.model_name,
            related_requirements=related_reqs,
            timestamp=alert.timestamp,
        )

    @staticmethod
    def reports_to_evidence_batch(
        reports: list[CitadelMonitoringReport],
    ) -> list[EvidenceFromCitadel]:
        """複数レポートを一括でエビデンスに変換."""
        return [
            CitadelDataTransformer.report_to_evidence(r)
            for r in reports
        ]

    @staticmethod
    def alerts_to_incidents_batch(
        alerts: list[CitadelAlert],
    ) -> list[IncidentFromCitadel]:
        """複数アラートを一括でインシデントに変換."""
        return [
            CitadelDataTransformer.alert_to_incident(a)
            for a in alerts
        ]


# ── Integration Service ──────────────────────────────────

class CitadelIntegrationService:
    """Citadel AI連携サービス.

    Citadel AIのデータをJPGovAIのエビデンス/インシデントとして
    インポートする統合サービス。
    """

    def __init__(
        self,
        api_url: str = "",
        api_key: str = "",
    ) -> None:
        self.client = CitadelAPIClient(api_url, api_key)
        self.transformer = CitadelDataTransformer()

    def import_monitoring_reports(
        self,
        model_id: str = "",
        report_type: str = "",
        since: str = "",
    ) -> list[EvidenceFromCitadel]:
        """監視レポートをエビデンスとしてインポート.

        Args:
            model_id: モデルID（空=全モデル）
            report_type: レポート種別（空=全種別）
            since: この日時以降のレポートを取得

        Returns:
            変換されたエビデンスのリスト
        """
        reports = self.client.get_monitoring_reports(
            model_id=model_id,
            report_type=report_type,
            since=since,
        )
        return self.transformer.reports_to_evidence_batch(reports)

    def sync_alerts_as_incidents(
        self,
        model_id: str = "",
        severity: str = "",
        since: str = "",
    ) -> list[IncidentFromCitadel]:
        """アラートをインシデントとして同期.

        Args:
            model_id: モデルID（空=全モデル）
            severity: 重大度フィルタ
            since: この日時以降のアラートを取得

        Returns:
            変換されたインシデントのリスト
        """
        alerts = self.client.get_alerts(
            model_id=model_id,
            severity=severity,
            since=since,
        )
        return self.transformer.alerts_to_incidents_batch(alerts)

    def get_requirement_mapping(self) -> dict[str, dict[str, Any]]:
        """Citadel AI機能 -> JPGovAI要件のマッピングを取得."""
        return dict(CITADEL_TO_REQUIREMENT_MAP)
