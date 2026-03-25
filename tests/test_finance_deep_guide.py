# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for finance deep guide."""

from __future__ import annotations

from app.guidelines.finance_deep_guide import (
    FINANCIAL_AI_RISKS,
    FINANCIAL_AI_USE_CASES,
    FINANCIAL_REGULATORY_REQUIREMENTS,
    INSPECTION_FOCUS_AREAS,
    get_financial_regulatory_requirements,
    get_financial_risk,
    get_financial_risks,
    get_financial_use_cases,
    get_inspection_focus_areas,
    get_requirement_deep_guide,
)


class TestFinancialAIRisks:
    """金融業AIリスクのテスト."""

    def test_risks_exist(self):
        """リスクが存在すること."""
        risks = get_financial_risks()
        assert len(risks) >= 5

    def test_risk_categories(self):
        """5つのリスクカテゴリがあること."""
        categories = {r.category for r in FINANCIAL_AI_RISKS}
        assert "モデルリスク" in categories
        assert "データリスク" in categories
        assert "オペレーショナルリスク" in categories
        assert "コンダクトリスク" in categories
        assert "サイバーリスク" in categories

    def test_get_risk_by_id(self):
        """IDでリスクを取得できること."""
        risk = get_financial_risk("FIN-RISK-01")
        assert risk is not None
        assert risk.category == "モデルリスク"

    def test_get_risk_not_found(self):
        """存在しないIDでNone."""
        assert get_financial_risk("NONEXISTENT") is None

    def test_risks_have_actions(self):
        """各リスクに具体的アクションがあること."""
        for risk in FINANCIAL_AI_RISKS:
            assert len(risk.specific_actions) > 0, (
                f"{risk.risk_id} has no specific actions"
            )

    def test_risks_have_meti_mapping(self):
        """各リスクにMETIマッピングがあること."""
        for risk in FINANCIAL_AI_RISKS:
            assert len(risk.meti_mapping) > 0, (
                f"{risk.risk_id} has no METI mapping"
            )

    def test_case_studies_exist(self):
        """少なくとも1つの事例があること."""
        with_cases = [r for r in FINANCIAL_AI_RISKS if r.case_study]
        assert len(with_cases) >= 1


class TestRegulatoryRequirements:
    """金融規制要件のテスト."""

    def test_requirements_exist(self):
        """要件が存在すること."""
        reqs = get_financial_regulatory_requirements()
        assert len(reqs) >= 5

    def test_fsa_requirements(self):
        """金融庁の要件があること."""
        reqs = [r for r in FINANCIAL_REGULATORY_REQUIREMENTS if "金融庁" in r.regulation]
        assert len(reqs) >= 2

    def test_sr117_requirement(self):
        """SR 11-7の要件があること."""
        reqs = [r for r in FINANCIAL_REGULATORY_REQUIREMENTS if "SR 11-7" in r.regulation]
        assert len(reqs) >= 1

    def test_obligation_levels(self):
        """義務レベルがあること."""
        levels = {r.obligation_level for r in FINANCIAL_REGULATORY_REQUIREMENTS}
        assert "mandatory" in levels or "guideline" in levels


class TestFinancialUseCases:
    """ユースケースのテスト."""

    def test_use_cases_exist(self):
        """ユースケースが存在すること."""
        ucs = get_financial_use_cases()
        assert len(ucs) >= 5

    def test_high_risk_cases(self):
        """高リスクのユースケースがあること."""
        high = [u for u in FINANCIAL_AI_USE_CASES if u.risk_level == "high"]
        assert len(high) >= 3

    def test_use_cases_have_controls(self):
        """各ユースケースにコントロールがあること."""
        for uc in FINANCIAL_AI_USE_CASES:
            assert len(uc.required_controls) > 0, (
                f"{uc.use_case_id} has no controls"
            )


class TestInspectionFocusAreas:
    """検査ポイントのテスト."""

    def test_focus_areas_exist(self):
        """検査ポイントが存在すること."""
        areas = get_inspection_focus_areas()
        assert len(areas) >= 5

    def test_areas_have_evidence(self):
        """各ポイントにエビデンス要件があること."""
        for area in INSPECTION_FOCUS_AREAS:
            assert "expected_evidence" in area
            assert area["expected_evidence"]


class TestRequirementDeepGuide:
    """要件ディープガイドのテスト."""

    def test_c02_r01_guide(self):
        """C02-R01のガイドが取得できること."""
        guide = get_requirement_deep_guide("C02-R01")
        assert guide is not None
        assert "related_risks" in guide
        assert len(guide["related_risks"]) > 0

    def test_nonexistent_requirement(self):
        """存在しない要件でNone."""
        guide = get_requirement_deep_guide("C99-R99")
        assert guide is None
