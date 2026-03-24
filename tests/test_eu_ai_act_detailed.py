# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for EU AI Act detailed risk classification and obligations."""

from __future__ import annotations

from app.guidelines.eu_ai_act_detailed import (
    ANNEX_III_HIGH_RISK,
    RISK_LEVELS,
    all_conformity_steps,
    all_high_risk_use_cases,
    all_japan_checklist_items,
    get_eu_to_iso_mapping,
    get_eu_to_meti_mapping,
    get_high_risk_use_case,
    get_japan_checklist_by_category,
    get_risk_level_detail,
)


class TestRiskLevels:
    """EU AI Act risk level tests."""

    def test_four_risk_levels(self):
        assert len(RISK_LEVELS) == 4

    def test_risk_level_names(self):
        levels = {r.level for r in RISK_LEVELS}
        assert levels == {"unacceptable", "high", "limited", "minimal"}

    def test_get_risk_level(self):
        high = get_risk_level_detail("high")
        assert high is not None
        assert len(high.obligations) > 5
        assert len(high.articles) > 5

    def test_get_nonexistent_risk_level(self):
        assert get_risk_level_detail("nonexistent") is None

    def test_all_have_obligations(self):
        for level in RISK_LEVELS:
            assert len(level.obligations) > 0

    def test_all_have_articles(self):
        for level in RISK_LEVELS:
            assert len(level.articles) > 0


class TestAnnexIII:
    """Annex III high-risk AI tests."""

    def test_eight_categories(self):
        assert len(ANNEX_III_HIGH_RISK) == 8

    def test_category_numbers(self):
        numbers = {u.category_number for u in ANNEX_III_HIGH_RISK}
        assert numbers == {1, 2, 3, 4, 5, 6, 7, 8}

    def test_get_use_case(self):
        uc = get_high_risk_use_case("ANNEX3-1")
        assert uc is not None
        assert "生体認証" in uc.category

    def test_get_nonexistent_use_case(self):
        assert get_high_risk_use_case("ANNEX3-99") is None

    def test_all_have_examples(self):
        for uc in all_high_risk_use_cases():
            assert len(uc.examples) > 0, f"{uc.use_case_id} missing examples"

    def test_all_have_obligations(self):
        for uc in all_high_risk_use_cases():
            assert len(uc.key_obligations) > 0

    def test_unique_ids(self):
        ids = [u.use_case_id for u in ANNEX_III_HIGH_RISK]
        assert len(ids) == len(set(ids))


class TestConformityAssessment:
    """Conformity assessment steps tests."""

    def test_steps_exist(self):
        steps = all_conformity_steps()
        assert len(steps) >= 8

    def test_steps_sequential(self):
        steps = all_conformity_steps()
        for i, step in enumerate(steps):
            assert step.step_number == i + 1

    def test_all_have_documents(self):
        for step in all_conformity_steps():
            assert len(step.required_documents) > 0


class TestJapanChecklist:
    """Japan company checklist tests."""

    def test_checklist_exists(self):
        items = all_japan_checklist_items()
        assert len(items) >= 15

    def test_unique_check_ids(self):
        items = all_japan_checklist_items()
        ids = [i.check_id for i in items]
        assert len(ids) == len(set(ids))

    def test_categories(self):
        items = all_japan_checklist_items()
        categories = {i.category for i in items}
        assert "scope" in categories
        assert "classification" in categories
        assert "obligation" in categories

    def test_get_by_category(self):
        scope_items = get_japan_checklist_by_category("scope")
        assert len(scope_items) >= 2
        assert all(i.category == "scope" for i in scope_items)

    def test_eu_to_meti_mapping(self):
        mapping = get_eu_to_meti_mapping()
        assert isinstance(mapping, dict)
        assert len(mapping) > 0

    def test_eu_to_iso_mapping(self):
        mapping = get_eu_to_iso_mapping()
        assert isinstance(mapping, dict)
        assert len(mapping) > 0

    def test_all_have_guidance(self):
        for item in all_japan_checklist_items():
            assert len(item.guidance) > 0
            assert len(item.question) > 0
