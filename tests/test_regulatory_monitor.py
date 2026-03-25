# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for the regulatory monitor service."""

from __future__ import annotations

import pytest

from app.db.database import get_db, reset_db
from app.models import RegulatoryUpdateCreate
from app.services.regulatory_monitor import (
    analyze_all_impacts,
    analyze_impact,
    delete_update,
    get_update,
    list_updates,
    register_update,
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


def _make_update_data(
    regulation_name: str = "METI AI事業者ガイドライン",
    title: str = "v1.2改訂",
    severity: str = "medium",
    affected: list[str] | None = None,
) -> RegulatoryUpdateCreate:
    """Create a mock regulatory update."""
    return RegulatoryUpdateCreate(
        regulation_name=regulation_name,
        title=title,
        description="テスト用の規制変更です",
        change_type="amendment",
        affected_requirements=affected if affected is not None else ["C01-R01", "C02-R01"],
        effective_date="2026-07-01",
        deadline="2026-09-30",
        severity=severity,
        created_by="admin",
    )


class TestRegulatoryMonitor:
    """Regulatory monitor tests."""

    def test_register_update(self):
        """Should register a regulatory update."""
        data = _make_update_data()
        update = register_update(data)
        assert update.regulation_name == "METI AI事業者ガイドライン"
        assert update.title == "v1.2改訂"
        assert update.severity == "medium"
        assert len(update.affected_requirements) == 2

    def test_register_preserves_fields(self):
        """All fields should be preserved on registration."""
        data = _make_update_data()
        update = register_update(data)
        assert update.description == "テスト用の規制変更です"
        assert update.change_type == "amendment"
        assert update.effective_date == "2026-07-01"
        assert update.deadline == "2026-09-30"
        assert update.created_by == "admin"

    def test_get_update(self):
        """Should retrieve a specific update."""
        data = _make_update_data()
        created = register_update(data)
        fetched = get_update(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.title == created.title

    def test_get_update_not_found(self):
        """Should return None for non-existent update."""
        result = get_update("nonexistent-id")
        assert result is None

    def test_list_updates_empty(self):
        """Should return empty list when no updates exist."""
        result = list_updates()
        assert result == []

    def test_list_updates_multiple(self):
        """Should list all updates."""
        register_update(_make_update_data(title="Update 1"))
        register_update(_make_update_data(title="Update 2"))
        register_update(_make_update_data(title="Update 3"))
        result = list_updates()
        assert len(result) == 3

    def test_list_updates_filter_by_regulation(self):
        """Should filter by regulation name."""
        register_update(_make_update_data(regulation_name="METI"))
        register_update(_make_update_data(regulation_name="ISO 42001"))
        register_update(_make_update_data(regulation_name="METI"))

        meti = list_updates(regulation_name="METI")
        assert len(meti) == 2
        iso = list_updates(regulation_name="ISO 42001")
        assert len(iso) == 1

    def test_list_updates_filter_by_severity(self):
        """Should filter by severity."""
        register_update(_make_update_data(severity="high"))
        register_update(_make_update_data(severity="medium"))
        register_update(_make_update_data(severity="high"))

        high = list_updates(severity="high")
        assert len(high) == 2

    def test_delete_update(self):
        """Should delete an update."""
        data = _make_update_data()
        created = register_update(data)
        success = delete_update(created.id)
        assert success is True
        assert get_update(created.id) is None

    def test_delete_update_not_found(self):
        """Should return False for non-existent update."""
        success = delete_update("nonexistent-id")
        assert success is False

    def test_analyze_impact_basic(self):
        """Should analyze impact of a regulatory update."""
        data = _make_update_data(affected=["C01-R01", "C02-R01"])
        update = register_update(data)

        scores = {"C01-R01": 2.0, "C02-R01": 1.0}
        impact = analyze_impact(update.id, "org-001", current_scores=scores)

        assert impact is not None
        assert impact.organization_id == "org-001"
        assert impact.regulation_name == "METI AI事業者ガイドライン"
        assert len(impact.affected_requirements) == 2

    def test_analyze_impact_with_low_scores(self):
        """Should flag heavy impact for low scores."""
        data = _make_update_data(affected=["C01-R01"])
        update = register_update(data)

        scores = {"C01-R01": 0.5}
        impact = analyze_impact(update.id, "org-001", current_scores=scores)

        assert impact is not None
        assert "重大" in impact.estimated_impact or "スコア" in impact.estimated_impact

    def test_analyze_impact_with_high_scores(self):
        """Should indicate minimal impact for high scores."""
        data = _make_update_data(affected=["C01-R01"])
        update = register_update(data)

        scores = {"C01-R01": 3.8}
        impact = analyze_impact(update.id, "org-001", current_scores=scores)

        assert impact is not None
        assert "影響なし" in impact.estimated_impact or "軽微" in impact.estimated_impact

    def test_analyze_impact_generates_actions(self):
        """Should generate recommended actions."""
        data = _make_update_data(affected=["C01-R01"])
        update = register_update(data)

        scores = {"C01-R01": 1.5}
        impact = analyze_impact(update.id, "org-001", current_scores=scores)

        assert impact is not None
        assert len(impact.recommended_actions) > 0

    def test_analyze_impact_not_found(self):
        """Should return None for non-existent update."""
        impact = analyze_impact("nonexistent", "org-001")
        assert impact is None

    def test_analyze_impact_empty_affected(self):
        """Should handle empty affected requirements."""
        data = _make_update_data(affected=[])
        update = register_update(data)

        impact = analyze_impact(update.id, "org-001", current_scores={})
        assert impact is not None
        assert "未指定" in impact.estimated_impact

    def test_analyze_all_impacts(self):
        """Should analyze all updates at once."""
        register_update(_make_update_data(severity="high", title="High impact"))
        register_update(_make_update_data(severity="medium", title="Medium impact"))

        report = analyze_all_impacts("org-001", current_scores={"C01-R01": 2.0, "C02-R01": 1.5})
        assert report.total_updates == 2
        assert report.high_severity_count == 1
        assert len(report.impacts) == 2

    def test_analyze_all_impacts_empty(self):
        """Should return empty report when no updates exist."""
        report = analyze_all_impacts("org-001")
        assert report.total_updates == 0
        assert len(report.impacts) == 0

    def test_impact_includes_deadline(self):
        """Impact should include the deadline from the update."""
        data = _make_update_data()
        update = register_update(data)

        impact = analyze_impact(update.id, "org-001", current_scores={"C01-R01": 2.0})
        assert impact is not None
        assert impact.deadline == "2026-09-30"

    def test_impact_includes_severity(self):
        """Impact should include severity."""
        data = _make_update_data(severity="high")
        update = register_update(data)

        impact = analyze_impact(update.id, "org-001", current_scores={})
        assert impact is not None
        assert impact.severity == "high"

    def test_analyze_impact_no_scores_provided(self):
        """Should work even when no scores are provided."""
        data = _make_update_data(affected=["C01-R01"])
        update = register_update(data)

        # No current_scores and no gap analysis in DB
        impact = analyze_impact(update.id, "org-001")
        assert impact is not None
