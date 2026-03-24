# Copyright (c) 2026 Yutaro Maeda
# Licensed under the MIT License. See LICENSE file for details.

"""Tests for the policy generator service."""

from __future__ import annotations

import pytest

from app.models import PolicyType
from app.services.policy_generator import (
    generate_all_policies,
    generate_policy,
    get_available_policy_types,
)


class TestPolicyGenerator:
    """Policy generator tests."""

    def test_available_types(self):
        types = get_available_policy_types()
        assert len(types) == 5
        type_values = {t["type"] for t in types}
        assert "ai_usage" in type_values
        assert "risk_management" in type_values
        assert "ethics" in type_values
        assert "data_management" in type_values
        assert "incident_response" in type_values

    def test_generate_ai_usage(self):
        doc = generate_policy(PolicyType.AI_USAGE, "Test Corp", "org-001")
        assert doc.title == "AI利用ポリシー"
        assert "Test Corp" in doc.full_text
        assert len(doc.sections) > 0
        assert doc.organization_id == "org-001"

    def test_generate_risk_management(self):
        doc = generate_policy(PolicyType.RISK_MANAGEMENT, "Test Corp")
        assert doc.title == "AIリスク管理方針"
        assert len(doc.sections) > 0

    def test_generate_ethics(self):
        doc = generate_policy(PolicyType.ETHICS, "Test Corp")
        assert doc.title == "AI倫理方針"

    def test_generate_data_management(self):
        doc = generate_policy(PolicyType.DATA_MANAGEMENT, "Test Corp")
        assert doc.title == "データ管理方針"

    def test_generate_incident_response(self):
        doc = generate_policy(PolicyType.INCIDENT_RESPONSE, "Test Corp")
        assert doc.title == "AIインシデント対応手順書"

    def test_generate_all(self):
        docs = generate_all_policies("Test Corp", "org-001")
        assert len(docs) == 5
        titles = {d.title for d in docs}
        assert "AI利用ポリシー" in titles
        assert "AIリスク管理方針" in titles

    def test_full_text_has_sections(self):
        doc = generate_policy(PolicyType.AI_USAGE, "Sample Inc")
        for section in doc.sections:
            assert section["heading"] in doc.full_text

    def test_org_name_substitution(self):
        doc = generate_policy(PolicyType.AI_USAGE, "MyCompany株式会社")
        assert "MyCompany株式会社" in doc.full_text

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError):
            generate_policy("invalid_type", "Test Corp")  # type: ignore[arg-type]
