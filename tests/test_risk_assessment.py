# Copyright (c) 2026 Yutaro Maeda
# Licensed under the MIT License. See LICENSE file for details.

"""Tests for the risk assessment service."""

from __future__ import annotations

import pytest

from app.db.database import get_db, reset_db
from app.models import RiskLevel
from app.services.risk_assessment import (
    classify_risk,
    get_risk_questions,
    run_risk_assessment,
    get_risk_assessment,
    list_risk_assessments,
)


@pytest.fixture(autouse=True)
def _setup_db(tmp_path):
    reset_db()
    db_url = f"sqlite:///{tmp_path}/test.db"
    db = get_db(db_url)
    db.create_tables()
    yield
    reset_db()


class TestRiskClassification:
    """Risk classification tests."""

    def test_no_risks_is_minimal(self):
        result = classify_risk({})
        assert result == RiskLevel.MINIMAL

    def test_high_risk_biometric(self):
        result = classify_risk({"biometric_identification": True})
        assert result == RiskLevel.HIGH

    def test_high_risk_employment(self):
        result = classify_risk({"employment": True})
        assert result == RiskLevel.HIGH

    def test_limited_risk_chatbot(self):
        result = classify_risk({"chatbot": True})
        assert result == RiskLevel.LIMITED

    def test_limited_risk_content_gen(self):
        result = classify_risk({"content_generation": True})
        assert result == RiskLevel.LIMITED

    def test_high_overrides_limited(self):
        result = classify_risk({
            "chatbot": True,
            "healthcare": True,
        })
        assert result == RiskLevel.HIGH

    def test_all_false_is_minimal(self):
        result = classify_risk({
            "biometric_identification": False,
            "chatbot": False,
        })
        assert result == RiskLevel.MINIMAL


class TestRiskAssessment:
    """Risk assessment service tests."""

    def test_risk_questions_not_empty(self):
        questions = get_risk_questions()
        assert len(questions) > 0

    def test_run_minimal_risk(self):
        result = run_risk_assessment(
            organization_id="org-001",
            system_name="Internal Tool",
            system_description="Simple internal tool",
            answers={},
        )
        assert result.overall_risk_level == RiskLevel.MINIMAL
        assert len(result.additional_requirements) > 0

    def test_run_high_risk(self):
        result = run_risk_assessment(
            organization_id="org-001",
            system_name="Credit Scoring AI",
            system_description="AI for credit scoring",
            answers={"credit_scoring": True},
        )
        assert result.overall_risk_level == RiskLevel.HIGH
        assert len(result.additional_requirements) > 5

    def test_persistence(self):
        result = run_risk_assessment(
            organization_id="org-001",
            system_name="Test System",
            system_description="",
            answers={"chatbot": True},
        )
        loaded = get_risk_assessment(result.id)
        assert loaded is not None
        assert loaded.system_name == "Test System"
        assert loaded.overall_risk_level == RiskLevel.LIMITED

    def test_list_assessments(self):
        run_risk_assessment("org-001", "System A", "", {"chatbot": True})
        run_risk_assessment("org-001", "System B", "", {"healthcare": True})
        results = list_risk_assessments("org-001")
        assert len(results) == 2

    def test_items_populated(self):
        result = run_risk_assessment(
            organization_id="org-001",
            system_name="Test",
            system_description="",
            answers={"chatbot": True, "healthcare": False},
        )
        assert len(result.items) > 0
        chatbot_item = next((i for i in result.items if i.question_key == "chatbot"), None)
        assert chatbot_item is not None
        assert chatbot_item.answer is True
