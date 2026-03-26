# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for AutoFix v2 — policy_templates integration, approval workflow."""

from __future__ import annotations

import pytest

from app.db.database import get_db, reset_db
from app.guidelines.meti_v1_1 import all_requirements
from app.knowledge.policy_templates import POLICY_TEMPLATES
from app.models import (
    AutoFixResult,
    ComplianceStatus,
    DocumentStatus,
    RequirementGap,
)
from app.services.autofix import AutoFixEngine


@pytest.fixture(autouse=True)
def _setup_db(tmp_path):
    """Use a temporary database for each test."""
    reset_db()
    db_url = f"sqlite:///{tmp_path}/test.db"
    db = get_db(db_url)
    db.create_tables()
    yield
    reset_db()


class TestPolicyTemplateIntegration:
    """AutoFixEngine が policy_templates.py の雛形文書を使用することを検証."""

    def setup_method(self):
        self.engine = AutoFixEngine()
        self.org_context = {
            "org_name": "雛形テスト株式会社",
            "industry": "金融・保険",
            "size": "large",
            "ai_usage": "production",
        }

    def test_fix_uses_policy_template_content(self):
        """fix_requirement should use policy_templates content for all 28 requirements."""
        for req in all_requirements():
            result = self.engine.fix_requirement(req.req_id, self.org_context)
            assert isinstance(result, AutoFixResult)
            assert len(result.generated_documents) >= 1
            # 主文書にorg_nameが含まれていること
            primary_doc = result.generated_documents[0]
            assert "雛形テスト株式会社" in primary_doc.content, (
                f"{req.req_id}: org_name not found in primary document"
            )

    def test_policy_template_replaces_industry(self):
        """Industry placeholder should be replaced in the generated document."""
        result = self.engine.fix_requirement("C01-R01", self.org_context)
        primary_doc = result.generated_documents[0]
        assert "金融・保険" in primary_doc.content

    def test_policy_template_documents_are_longer(self):
        """Documents from policy_templates should be substantially longer than old templates."""
        for req_id in list(POLICY_TEMPLATES.keys())[:5]:
            result = self.engine.fix_requirement(req_id, self.org_context)
            primary_doc = result.generated_documents[0]
            # 実用的な文書は少なくとも500文字以上
            assert len(primary_doc.content) >= 500, (
                f"{req_id}: document is too short ({len(primary_doc.content)} chars)"
            )

    def test_supplementary_documents_also_generated(self):
        """C01-R01 should have supplementary documents from autofix_definitions."""
        result = self.engine.fix_requirement("C01-R01", self.org_context)
        # C01-R01 has 3 documents in autofix_definitions: main + 2 supplementary
        assert len(result.generated_documents) >= 2, (
            f"Expected at least 2 documents for C01-R01, got {len(result.generated_documents)}"
        )


class TestApprovalWorkflow:
    """文書の承認ワークフロー（draft → approved）を検証."""

    def setup_method(self):
        self.engine = AutoFixEngine()
        self.org_context = {"org_name": "承認テスト株式会社"}

    def test_documents_default_to_draft(self):
        """Generated documents should default to DRAFT status."""
        result = self.engine.fix_requirement("C01-R01", self.org_context)
        for doc in result.generated_documents:
            assert doc.status == DocumentStatus.DRAFT

    def test_result_default_status_is_generated(self):
        """AutoFixResult should have 'generated' status by default."""
        result = self.engine.fix_requirement("C01-R01", self.org_context)
        assert result.status == "generated"

    def test_approve_single_document(self):
        """approve_document should change document status to APPROVED."""
        result = self.engine.fix_requirement("C01-R01", self.org_context)
        updated = self.engine.approve_document(result, document_index=0)
        assert updated.generated_documents[0].status == DocumentStatus.APPROVED

    def test_approve_all_documents_sets_completed(self):
        """approve_all_documents should set all docs to APPROVED and result to completed."""
        result = self.engine.fix_requirement("C01-R01", self.org_context)
        updated = self.engine.approve_all_documents(result)
        for doc in updated.generated_documents:
            assert doc.status == DocumentStatus.APPROVED
        assert updated.status == "completed"

    def test_partial_approval_keeps_generated_status(self):
        """Approving only some documents should keep status as 'generated'."""
        result = self.engine.fix_requirement("C01-R01", self.org_context)
        if len(result.generated_documents) > 1:
            updated = self.engine.approve_document(result, document_index=0)
            assert updated.status == "generated"

    def test_approve_invalid_index_no_error(self):
        """approve_document with invalid index should not raise."""
        result = self.engine.fix_requirement("C01-R01", self.org_context)
        updated = self.engine.approve_document(result, document_index=999)
        # Status should be unchanged or 'completed' only if all approved
        assert updated.status in ("generated", "completed")

    def test_approve_triggers_score_update_conceptual(self):
        """Approving all documents should change result status to 'completed'.

        This is the trigger for the UI to update the score from '要対応' to 'OK'.
        """
        result = self.engine.fix_requirement("C02-R01", self.org_context)
        updated = self.engine.approve_all_documents(result)
        assert updated.status == "completed"


class TestAutoFixV2AllRequirements:
    """全28要件が v2 エンジンで正常に動作することを検証."""

    def setup_method(self):
        self.engine = AutoFixEngine()
        self.org_context = {
            "org_name": "全件テスト株式会社",
            "industry": "製造",
            "ai_usage": "scaling",
        }

    def test_all_28_requirements_produce_valid_result(self):
        """All 28 requirements should produce valid AutoFixResult with v2 engine."""
        for req in all_requirements():
            result = self.engine.fix_requirement(req.req_id, self.org_context)
            assert isinstance(result, AutoFixResult)
            assert result.requirement_id == req.req_id
            assert len(result.generated_documents) >= 1
            assert len(result.tasks) >= 1
            assert result.status == "generated"
            # All documents should be DRAFT
            for doc in result.generated_documents:
                assert doc.status == DocumentStatus.DRAFT

    def test_all_28_can_be_approved(self):
        """All 28 requirements should be approvable."""
        for req in all_requirements():
            result = self.engine.fix_requirement(req.req_id, self.org_context)
            updated = self.engine.approve_all_documents(result)
            assert updated.status == "completed"

    def test_fix_all_gaps_uses_v2(self):
        """fix_all_gaps should use policy_templates for all gaps."""
        gaps = [
            RequirementGap(
                req_id="C01-R01",
                category_id="C01",
                title="人間の尊厳・自律の尊重",
                status=ComplianceStatus.NON_COMPLIANT,
                current_score=0.5,
            ),
            RequirementGap(
                req_id="C05-R01",
                category_id="C05",
                title="セキュリティ対策の実施",
                status=ComplianceStatus.PARTIAL,
                current_score=1.5,
            ),
            RequirementGap(
                req_id="C10-R02",
                category_id="C10",
                title="相互運用性・オープン性の確保",
                status=ComplianceStatus.COMPLIANT,
                current_score=3.5,
            ),
        ]
        results = self.engine.fix_all_gaps(gaps, self.org_context)
        assert len(results) == 2  # compliant skipped
        for r in results:
            assert "全件テスト株式会社" in r.generated_documents[0].content
