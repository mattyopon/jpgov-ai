# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for the incident management service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.db.database import get_db, reset_db
from app.models import (
    IncidentCreate,
    IncidentRCACreate,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
    IncidentUpdate,
)
from app.services.incident_management import (
    create_incident,
    create_rca,
    get_incident,
    get_incident_stats,
    get_rca,
    get_regulatory_reportable_incidents,
    list_incidents,
    update_incident,
)


@pytest.fixture(autouse=True)
def _setup_db(tmp_path):
    """Use a temporary database for each test."""
    reset_db()
    db_url = f"sqlite:///{tmp_path}/test.db"
    db = get_db(db_url)
    db.create_tables()
    yield
    reset_db()


def _create_incident_data(
    org_id: str = "org-001",
    title: str = "テストインシデント",
    inc_type: IncidentType = IncidentType.HALLUCINATION,
    severity: IncidentSeverity = IncidentSeverity.HIGH,
) -> IncidentCreate:
    return IncidentCreate(
        organization_id=org_id,
        title=title,
        description="テスト説明",
        incident_type=inc_type,
        severity=severity,
        affected_system="チャットボット",
        impact_description="顧客10名に影響",
        detected_by="user-001",
        related_requirements=["R001", "R002"],
        regulatory_report_required=False,
    )


class TestIncidentCRUD:
    """Incident CRUD tests."""

    def test_create_incident(self):
        """Should create an incident."""
        data = _create_incident_data()
        incident = create_incident(data, actor_id="user-001")
        assert incident.organization_id == "org-001"
        assert incident.title == "テストインシデント"
        assert incident.incident_type == IncidentType.HALLUCINATION
        assert incident.severity == IncidentSeverity.HIGH
        assert incident.status == IncidentStatus.OPEN
        assert incident.detected_by == "user-001"
        assert "R001" in incident.related_requirements

    def test_get_incident(self):
        """Should retrieve an incident."""
        data = _create_incident_data()
        created = create_incident(data)
        fetched = get_incident(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.title == "テストインシデント"

    def test_get_incident_not_found(self):
        """Should return None for non-existent incident."""
        assert get_incident("nonexistent") is None

    def test_update_incident_status(self):
        """Should update incident status."""
        created = create_incident(_create_incident_data())
        updated = update_incident(
            created.id,
            IncidentUpdate(status=IncidentStatus.INVESTIGATING),
        )
        assert updated is not None
        assert updated.status == IncidentStatus.INVESTIGATING

    def test_update_incident_severity(self):
        """Should update incident severity."""
        created = create_incident(_create_incident_data())
        updated = update_incident(
            created.id,
            IncidentUpdate(severity=IncidentSeverity.CRITICAL),
        )
        assert updated is not None
        assert updated.severity == IncidentSeverity.CRITICAL

    def test_update_incident_resolved(self):
        """Should mark incident as resolved."""
        created = create_incident(_create_incident_data())
        now = datetime.now(timezone.utc).isoformat()
        updated = update_incident(
            created.id,
            IncidentUpdate(
                status=IncidentStatus.RESOLVED,
                resolved_at=now,
            ),
        )
        assert updated is not None
        assert updated.status == IncidentStatus.RESOLVED
        assert updated.resolved_at == now

    def test_update_incident_not_found(self):
        """Should return None for non-existent incident."""
        assert update_incident("nonexistent", IncidentUpdate(status=IncidentStatus.CLOSED)) is None

    def test_update_regulatory_report_sent(self):
        """Should update regulatory report status."""
        data = _create_incident_data()
        data.regulatory_report_required = True
        created = create_incident(data)
        updated = update_incident(
            created.id,
            IncidentUpdate(regulatory_report_sent=True),
        )
        assert updated is not None
        assert updated.regulatory_report_sent is True

    def test_list_incidents(self):
        """Should list incidents for an organization."""
        create_incident(_create_incident_data(title="Inc 1"))
        create_incident(_create_incident_data(title="Inc 2"))
        create_incident(_create_incident_data(org_id="org-002", title="Inc 3"))

        incidents = list_incidents("org-001")
        assert len(incidents) == 2

    def test_list_incidents_filter_status(self):
        """Should filter incidents by status."""
        inc1 = create_incident(_create_incident_data(title="Open"))
        inc2 = create_incident(_create_incident_data(title="Resolved"))
        update_incident(inc2.id, IncidentUpdate(status=IncidentStatus.RESOLVED))

        open_incidents = list_incidents("org-001", status=IncidentStatus.OPEN)
        assert len(open_incidents) == 1
        assert open_incidents[0].title == "Open"

    def test_list_incidents_filter_severity(self):
        """Should filter incidents by severity."""
        create_incident(_create_incident_data(severity=IncidentSeverity.HIGH))
        create_incident(_create_incident_data(severity=IncidentSeverity.LOW))

        high = list_incidents("org-001", severity=IncidentSeverity.HIGH)
        assert len(high) == 1

    def test_list_incidents_filter_type(self):
        """Should filter incidents by type."""
        create_incident(_create_incident_data(inc_type=IncidentType.BIAS))
        create_incident(_create_incident_data(inc_type=IncidentType.HALLUCINATION))

        bias = list_incidents("org-001", incident_type=IncidentType.BIAS)
        assert len(bias) == 1


class TestIncidentStats:
    """Incident statistics tests."""

    def test_empty_stats(self):
        """Should return empty stats for org with no incidents."""
        stats = get_incident_stats("org-001")
        assert stats.total_count == 0
        assert stats.open_count == 0
        assert stats.avg_resolution_hours == 0.0

    def test_stats_by_severity(self):
        """Should compute severity distribution."""
        create_incident(_create_incident_data(severity=IncidentSeverity.HIGH))
        create_incident(_create_incident_data(severity=IncidentSeverity.HIGH))
        create_incident(_create_incident_data(severity=IncidentSeverity.LOW))

        stats = get_incident_stats("org-001")
        assert stats.total_count == 3
        assert stats.by_severity.get("high") == 2
        assert stats.by_severity.get("low") == 1

    def test_stats_by_type(self):
        """Should compute type distribution."""
        create_incident(_create_incident_data(inc_type=IncidentType.HALLUCINATION))
        create_incident(_create_incident_data(inc_type=IncidentType.BIAS))
        create_incident(_create_incident_data(inc_type=IncidentType.BIAS))

        stats = get_incident_stats("org-001")
        assert stats.by_type.get("hallucination") == 1
        assert stats.by_type.get("bias") == 2

    def test_stats_open_count(self):
        """Should count open incidents."""
        inc1 = create_incident(_create_incident_data())
        inc2 = create_incident(_create_incident_data())
        update_incident(inc2.id, IncidentUpdate(status=IncidentStatus.RESOLVED))

        stats = get_incident_stats("org-001")
        assert stats.open_count == 1

    def test_stats_avg_resolution_time(self):
        """Should compute average resolution time."""
        now = datetime.now(timezone.utc)
        inc = create_incident(_create_incident_data())

        # Simulate resolved 2 hours later
        resolved_time = (now + timedelta(hours=2)).isoformat()
        update_incident(
            inc.id,
            IncidentUpdate(
                status=IncidentStatus.RESOLVED,
                resolved_at=resolved_time,
            ),
        )

        stats = get_incident_stats("org-001")
        assert stats.avg_resolution_hours > 0


class TestIncidentRCA:
    """RCA (Root Cause Analysis) tests."""

    def test_create_rca(self):
        """Should create an RCA."""
        inc = create_incident(_create_incident_data())
        rca = create_rca(
            IncidentRCACreate(
                incident_id=inc.id,
                root_cause="プロンプトインジェクション",
                contributing_factors=["入力フィルタリング不足"],
                corrective_actions=["入力バリデーション追加"],
                preventive_actions=["定期的なペネトレーションテスト"],
                lessons_learned="入力検証の重要性",
            )
        )
        assert rca.incident_id == inc.id
        assert rca.root_cause == "プロンプトインジェクション"
        assert len(rca.corrective_actions) == 1

    def test_get_rca(self):
        """Should retrieve an RCA by incident ID."""
        inc = create_incident(_create_incident_data())
        create_rca(
            IncidentRCACreate(
                incident_id=inc.id,
                root_cause="テスト原因",
            )
        )
        rca = get_rca(inc.id)
        assert rca is not None
        assert rca.root_cause == "テスト原因"

    def test_get_rca_not_found(self):
        """Should return None for non-existent RCA."""
        assert get_rca("nonexistent") is None


class TestRegulatoryReporting:
    """Regulatory incident reporting tests."""

    def test_get_regulatory_reportable(self):
        """Should return only incidents requiring regulatory reporting."""
        # Not required
        create_incident(_create_incident_data(title="Normal"))
        # Required
        data = _create_incident_data(title="Reportable")
        data.regulatory_report_required = True
        create_incident(data)

        reportable = get_regulatory_reportable_incidents("org-001")
        assert len(reportable) == 1
        assert reportable[0].title == "Reportable"
        assert reportable[0].regulatory_report_required is True

    def test_no_regulatory_incidents(self):
        """Should return empty list when no regulatory incidents."""
        create_incident(_create_incident_data())
        reportable = get_regulatory_reportable_incidents("org-001")
        assert len(reportable) == 0
