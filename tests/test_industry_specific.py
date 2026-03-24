# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for industry-specific AI governance guidelines."""

from __future__ import annotations

from app.guidelines.industry_specific import (
    ALL_INDUSTRY_GUIDELINES,
    SUPPORTED_INDUSTRIES,
    all_industry_requirement_ids,
    all_industry_requirements,
    get_guideline,
    get_industry_check_questions,
    get_industry_guidelines,
    get_industry_requirement,
    get_industry_to_meti_mapping,
)


class TestIndustryGuidelines:
    """Industry-specific guideline tests."""

    def test_supported_industries(self):
        assert len(SUPPORTED_INDUSTRIES) == 4
        assert "financial" in SUPPORTED_INDUSTRIES
        assert "healthcare" in SUPPORTED_INDUSTRIES
        assert "automotive" in SUPPORTED_INDUSTRIES
        assert "hr" in SUPPORTED_INDUSTRIES

    def test_all_guidelines_exist(self):
        assert len(ALL_INDUSTRY_GUIDELINES) >= 5

    def test_get_financial_guidelines(self):
        guidelines = get_industry_guidelines("financial")
        assert len(guidelines) >= 2

    def test_get_healthcare_guidelines(self):
        guidelines = get_industry_guidelines("healthcare")
        assert len(guidelines) >= 2

    def test_get_automotive_guidelines(self):
        guidelines = get_industry_guidelines("automotive")
        assert len(guidelines) >= 1

    def test_get_hr_guidelines(self):
        guidelines = get_industry_guidelines("hr")
        assert len(guidelines) >= 1

    def test_get_nonexistent_industry(self):
        guidelines = get_industry_guidelines("nonexistent")
        assert guidelines == []

    def test_get_guideline_by_id(self):
        g = get_guideline("FIN-FSA")
        assert g is not None
        assert g.industry == "financial"
        assert len(g.requirements) > 0

    def test_get_nonexistent_guideline(self):
        assert get_guideline("NONEXIST") is None


class TestIndustryRequirements:
    """Industry-specific requirement tests."""

    def test_requirements_exist(self):
        reqs = all_industry_requirements()
        assert len(reqs) >= 10

    def test_unique_req_ids(self):
        ids = all_industry_requirement_ids()
        assert len(ids) == len(set(ids))

    def test_get_requirement(self):
        req = get_industry_requirement("FIN-01")
        assert req is not None
        assert req.title == "AI利用のガバナンス体制"

    def test_get_nonexistent_requirement(self):
        assert get_industry_requirement("NONEXIST") is None

    def test_all_have_meti_mapping(self):
        for req in all_industry_requirements():
            assert isinstance(req.meti_mapping, list)
            assert len(req.meti_mapping) > 0, f"{req.req_id} missing METI mapping"

    def test_all_have_source(self):
        for req in all_industry_requirements():
            assert len(req.source) > 0


class TestIndustryCheckQuestions:
    """Industry-specific check questions tests."""

    def test_financial_check_questions(self):
        questions = get_industry_check_questions("financial")
        assert len(questions) > 0
        assert all("question" in q for q in questions)

    def test_healthcare_check_questions(self):
        questions = get_industry_check_questions("healthcare")
        assert len(questions) > 0

    def test_empty_industry_no_questions(self):
        questions = get_industry_check_questions("nonexistent")
        assert questions == []


class TestIndustryMappings:
    """Industry-to-METI mapping tests."""

    def test_financial_to_meti(self):
        mapping = get_industry_to_meti_mapping("financial")
        assert isinstance(mapping, dict)
        assert len(mapping) > 0

    def test_healthcare_to_meti(self):
        mapping = get_industry_to_meti_mapping("healthcare")
        assert isinstance(mapping, dict)
        assert len(mapping) > 0

    def test_empty_industry_mapping(self):
        mapping = get_industry_to_meti_mapping("nonexistent")
        assert mapping == {}
