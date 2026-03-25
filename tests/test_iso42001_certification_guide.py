# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for ISO 42001 certification guide."""

from __future__ import annotations

from app.knowledge.iso42001_certification_guide import (
    CERTIFICATION_BODIES,
    CERTIFICATION_PHASES,
    COMMON_NONCONFORMITIES,
    get_all_required_documents,
    get_certification_bodies,
    get_certification_phase,
    get_certification_phases,
    get_certification_timelines,
    get_common_nonconformities,
    get_maintenance_audits,
)


class TestCertificationPhases:
    """認証プロセスのテスト."""

    def test_phases_exist(self):
        """フェーズが存在すること."""
        phases = get_certification_phases()
        assert len(phases) == 4

    def test_phases_ordered(self):
        """フェーズが順序通りであること."""
        phases = get_certification_phases()
        for i, phase in enumerate(phases, 1):
            assert phase.phase == i

    def test_get_phase_by_number(self):
        """フェーズ番号で取得できること."""
        phase = get_certification_phase(1)
        assert phase is not None
        assert phase.name == "ギャップ分析と計画策定"

    def test_get_phase_not_found(self):
        """存在しないフェーズ番号でNone."""
        assert get_certification_phase(99) is None

    def test_each_phase_has_tasks(self):
        """各フェーズにタスクがあること."""
        for phase in CERTIFICATION_PHASES:
            assert len(phase.tasks) > 0, f"Phase {phase.phase} has no tasks"

    def test_each_phase_has_documents(self):
        """各フェーズに必要文書があること."""
        for phase in CERTIFICATION_PHASES:
            assert len(phase.required_documents) > 0, (
                f"Phase {phase.phase} has no documents"
            )

    def test_each_phase_has_jpgovai_value(self):
        """各フェーズにJPGovAI付加価値があること."""
        for phase in CERTIFICATION_PHASES:
            assert phase.jpgovai_value, f"Phase {phase.phase} has no JPGovAI value"


class TestCommonNonconformities:
    """よくある不適合のテスト."""

    def test_nonconformities_count(self):
        """不適合が10件あること."""
        assert len(get_common_nonconformities()) == 10

    def test_nonconformities_ranked(self):
        """不適合がランク順であること."""
        ncs = get_common_nonconformities()
        for i, nc in enumerate(ncs, 1):
            assert nc.rank == i

    def test_nonconformity_fields(self):
        """各不適合に必須フィールドがあること."""
        for nc in COMMON_NONCONFORMITIES:
            assert nc.title, f"Rank {nc.rank} has no title"
            assert nc.description, f"Rank {nc.rank} has no description"
            assert nc.clause, f"Rank {nc.rank} has no clause"
            assert nc.prevention, f"Rank {nc.rank} has no prevention"
            assert nc.evidence_needed, f"Rank {nc.rank} has no evidence_needed"


class TestCertificationBodies:
    """認証機関のテスト."""

    def test_bodies_exist(self):
        """認証機関が存在すること."""
        bodies = get_certification_bodies()
        assert len(bodies) >= 3

    def test_bodies_have_cost(self):
        """各認証機関にコスト情報があること."""
        for body in CERTIFICATION_BODIES:
            assert body.typical_cost_range, f"{body.name} has no cost info"

    def test_sgs_exists(self):
        """SGSジャパンが含まれること."""
        bodies = get_certification_bodies()
        sgs = [b for b in bodies if b.code == "SGS"]
        assert len(sgs) == 1


class TestCertificationTimelines:
    """認証取得期間のテスト."""

    def test_timelines_by_size(self):
        """企業規模別の期間があること."""
        timelines = get_certification_timelines()
        sizes = {t.size for t in timelines}
        assert "small" in sizes
        assert "medium" in sizes
        assert "large" in sizes
        assert "enterprise" in sizes

    def test_larger_takes_longer(self):
        """大企業ほど期間が長いこと."""
        timelines = get_certification_timelines()
        size_order = {"small": 0, "medium": 1, "large": 2, "enterprise": 3}
        sorted_tl = sorted(timelines, key=lambda t: size_order.get(t.size, 0))
        for i in range(len(sorted_tl) - 1):
            assert sorted_tl[i].total_months_max <= sorted_tl[i + 1].total_months_max


class TestMaintenanceAudits:
    """認証維持のテスト."""

    def test_maintenance_exists(self):
        """維持審査情報が存在すること."""
        audits = get_maintenance_audits()
        assert len(audits) >= 2

    def test_surveillance_and_renewal(self):
        """サーベイランスと更新審査があること."""
        audits = get_maintenance_audits()
        types = {a.audit_type for a in audits}
        assert any("サーベイランス" in t for t in types)
        assert any("更新" in t for t in types)


class TestRequiredDocuments:
    """必要文書のテスト."""

    def test_all_required_documents(self):
        """全文書のリストが取得できること."""
        docs = get_all_required_documents()
        assert len(docs) > 10

    def test_no_duplicates(self):
        """文書に重複がないこと."""
        docs = get_all_required_documents()
        assert len(docs) == len(set(docs))
