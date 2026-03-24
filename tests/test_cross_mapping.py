# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for cross-framework mapping matrix."""

from __future__ import annotations

from app.guidelines.cross_mapping import (
    CROSS_MAPPING,
    all_cross_mappings,
    get_compliance_synergies,
    get_coverage_matrix,
    get_cross_mapping_entry,
    get_frameworks_for_meti_requirement,
)


class TestCrossMapping:
    """Cross-mapping matrix tests."""

    def test_mappings_exist(self):
        mappings = all_cross_mappings()
        assert len(mappings) >= 10

    def test_unique_theme_ids(self):
        ids = [m.theme_id for m in CROSS_MAPPING]
        assert len(ids) == len(set(ids))

    def test_get_entry(self):
        entry = get_cross_mapping_entry("CM-01")
        assert entry is not None
        assert "ガバナンス" in entry.theme
        assert len(entry.meti_ids) > 0
        assert len(entry.iso_ids) > 0

    def test_get_nonexistent_entry(self):
        assert get_cross_mapping_entry("CM-99") is None

    def test_all_entries_have_meti(self):
        for entry in all_cross_mappings():
            assert len(entry.meti_ids) > 0, f"{entry.theme_id} missing METI IDs"

    def test_all_entries_have_theme(self):
        for entry in all_cross_mappings():
            assert len(entry.theme) > 0
            assert len(entry.description) > 0

    def test_frameworks_for_meti_c02_r01(self):
        """C02-R01 (リスクアセスメント) should map to multiple frameworks."""
        result = get_frameworks_for_meti_requirement("C02-R01")
        assert len(result["iso"]) > 0
        assert len(result["nist"]) > 0

    def test_frameworks_for_nonexistent_meti(self):
        result = get_frameworks_for_meti_requirement("C99-R99")
        assert result["iso"] == []
        assert result["nist"] == []
        assert result["eu_articles"] == []
        assert result["act"] == []


class TestComplianceSynergies:
    """Compliance synergy analysis tests."""

    def test_synergies_returned(self):
        synergies = get_compliance_synergies()
        assert len(synergies) > 0

    def test_synergies_have_required_keys(self):
        synergies = get_compliance_synergies()
        for s in synergies:
            assert "meti_id" in s
            assert "total_mapped_frameworks" in s
            assert "details" in s

    def test_synergies_sorted_descending(self):
        synergies = get_compliance_synergies()
        totals = [s["total_mapped_frameworks"] for s in synergies]
        assert totals == sorted(totals, reverse=True)

    def test_high_synergy_requirements(self):
        """Some METI requirements should map to 3+ frameworks."""
        synergies = get_compliance_synergies()
        high_synergy = [s for s in synergies if s["total_mapped_frameworks"] >= 3]
        assert len(high_synergy) > 0


class TestCoverageMatrix:
    """Coverage matrix tests."""

    def test_matrix_returned(self):
        matrix = get_coverage_matrix()
        assert isinstance(matrix, dict)
        assert len(matrix) > 0

    def test_matrix_has_all_frameworks(self):
        matrix = get_coverage_matrix()
        for theme_id, data in matrix.items():
            assert "meti" in data
            assert "iso" in data
            assert "nist" in data
            assert "eu" in data
            assert "act" in data
