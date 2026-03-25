# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for Citadel AI integration."""

from __future__ import annotations

from app.services.citadel_integration import (
    CITADEL_TO_REQUIREMENT_MAP,
    CitadelAlert,
    CitadelAPIClient,
    CitadelDataTransformer,
    CitadelIntegrationService,
    CitadelMonitoringReport,
    EvidenceFromCitadel,
    IncidentFromCitadel,
)


class TestCitadelToRequirementMap:
    """マッピングのテスト."""

    def test_mapping_exists(self):
        """マッピングが存在すること."""
        assert len(CITADEL_TO_REQUIREMENT_MAP) >= 7

    def test_all_have_meti(self):
        """全エントリにMETIマッピングがあること."""
        for key, value in CITADEL_TO_REQUIREMENT_MAP.items():
            assert "meti" in value, f"{key} has no meti mapping"
            assert len(value["meti"]) > 0

    def test_all_have_description(self):
        """全エントリに説明があること."""
        for key, value in CITADEL_TO_REQUIREMENT_MAP.items():
            assert "description" in value, f"{key} has no description"

    def test_key_types(self):
        """想定されるキーが含まれること."""
        assert "model_quality" in CITADEL_TO_REQUIREMENT_MAP
        assert "bias_detection" in CITADEL_TO_REQUIREMENT_MAP
        assert "data_drift" in CITADEL_TO_REQUIREMENT_MAP
        assert "adversarial_test" in CITADEL_TO_REQUIREMENT_MAP
        assert "explainability" in CITADEL_TO_REQUIREMENT_MAP


class TestCitadelAPIClient:
    """APIクライアントのテスト（インターフェース）."""

    def test_create_client(self):
        """クライアントが作成できること."""
        client = CitadelAPIClient()
        assert client.is_connected is False

    def test_connected_client(self):
        """接続済みクライアント."""
        client = CitadelAPIClient(api_url="https://api.citadel.ai", api_key="test")
        assert client.is_connected is True

    def test_empty_results(self):
        """未実装APIは空リストを返すこと."""
        client = CitadelAPIClient()
        assert client.get_monitoring_reports() == []
        assert client.get_alerts() == []
        assert client.get_model_card("model-1") == {}


class TestCitadelDataTransformer:
    """データ変換のテスト."""

    def test_report_to_evidence(self):
        """レポートをエビデンスに変換できること."""
        report = CitadelMonitoringReport(
            model_id="model-1",
            model_name="与信モデルA",
            report_type="bias_detection",
            summary="バイアス検出なし",
            status="normal",
            metrics={"statistical_parity_diff": 0.02},
        )

        evidence = CitadelDataTransformer.report_to_evidence(report)
        assert isinstance(evidence, EvidenceFromCitadel)
        assert "C03-R01" in evidence.requirement_ids
        assert "与信モデルA" in evidence.title
        assert evidence.source_type == "bias_detection"

    def test_alert_to_incident(self):
        """アラートをインシデントに変換できること."""
        alert = CitadelAlert(
            model_id="model-1",
            model_name="チャットボットAI",
            alert_type="bias_detected",
            severity="high",
            message="年齢に基づくバイアスを検出",
            metrics={"statistical_parity_diff": 0.15},
        )

        incident = CitadelDataTransformer.alert_to_incident(alert)
        assert isinstance(incident, IncidentFromCitadel)
        assert incident.severity == "high"
        assert incident.incident_type == "bias"
        assert "チャットボットAI" in incident.description

    def test_batch_conversion(self):
        """バッチ変換が動作すること."""
        reports = [
            CitadelMonitoringReport(
                model_name=f"Model {i}",
                report_type="model_quality",
            )
            for i in range(3)
        ]
        evidences = CitadelDataTransformer.reports_to_evidence_batch(reports)
        assert len(evidences) == 3

    def test_evidence_to_dict(self):
        """エビデンスが辞書に変換できること."""
        report = CitadelMonitoringReport(
            model_name="TestModel",
            report_type="data_drift",
        )
        evidence = CitadelDataTransformer.report_to_evidence(report)
        data = evidence.to_dict()
        assert "id" in data
        assert "requirement_ids" in data
        assert "title" in data

    def test_incident_to_dict(self):
        """インシデントが辞書に変換できること."""
        alert = CitadelAlert(
            model_name="TestModel",
            alert_type="drift_detected",
            severity="medium",
            message="drift",
        )
        incident = CitadelDataTransformer.alert_to_incident(alert)
        data = incident.to_dict()
        assert "id" in data
        assert "severity" in data
        assert "incident_type" in data

    def test_unknown_alert_type(self):
        """不明なアラートタイプでもインシデントに変換できること."""
        alert = CitadelAlert(
            model_name="TestModel",
            alert_type="unknown_type",
            severity="low",
            message="unknown",
        )
        incident = CitadelDataTransformer.alert_to_incident(alert)
        assert incident.incident_type == "other"


class TestCitadelIntegrationService:
    """統合サービスのテスト."""

    def test_create_service(self):
        """サービスが作成できること."""
        service = CitadelIntegrationService()
        assert service.client is not None
        assert service.transformer is not None

    def test_import_empty(self):
        """未接続時は空リスト."""
        service = CitadelIntegrationService()
        result = service.import_monitoring_reports()
        assert result == []

    def test_sync_empty(self):
        """未接続時は空リスト."""
        service = CitadelIntegrationService()
        result = service.sync_alerts_as_incidents()
        assert result == []

    def test_get_mapping(self):
        """マッピングが取得できること."""
        service = CitadelIntegrationService()
        mapping = service.get_requirement_mapping()
        assert "model_quality" in mapping
        assert "bias_detection" in mapping
