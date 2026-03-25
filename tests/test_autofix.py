# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for the AutoFix (auto-remediation) feature."""

from __future__ import annotations

import pytest

from app.db.database import get_db, reset_db
from app.guidelines.meti_v1_1 import ASSESSMENT_QUESTIONS, all_requirements
from app.knowledge.autofix_definitions import (
    AUTOFIX_DEFINITIONS,
    all_autofix_requirement_ids,
    get_autofix_definition,
)
from app.models import (
    AnswerItem,
    AutoFixResult,
    AutoFixTask,
    ChecklistItem,
    ComplianceStatus,
    DocumentStatus,
    GeneratedDocument,
    RequirementGap,
    SelfCheckItem,
)
from app.services.assessment import run_assessment
from app.services.autofix import AutoFixEngine
from app.services.gap_analysis import run_gap_analysis


@pytest.fixture(autouse=True)
def _setup_db(tmp_path):
    """Use a temporary database for each test."""
    reset_db()
    db_url = f"sqlite:///{tmp_path}/test.db"
    db = get_db(db_url)
    db.create_tables()
    yield
    reset_db()


def _make_answers(score: int) -> list[AnswerItem]:
    return [
        AnswerItem(question_id=q.question_id, selected_index=score)
        for q in ASSESSMENT_QUESTIONS
    ]


# ── AutoFix定義のテスト ──

class TestAutoFixDefinitions:
    """AutoFix definitions cover all 28 requirements."""

    def test_all_28_requirements_have_definitions(self):
        """All 28 requirements should have AutoFix definitions."""
        all_reqs = all_requirements()
        assert len(all_reqs) == 28
        for req in all_reqs:
            defn = get_autofix_definition(req.req_id)
            assert defn is not None, f"Missing AutoFix definition for {req.req_id}"

    def test_definitions_have_documents(self):
        """Each definition should have at least one document."""
        for req_id, defn in AUTOFIX_DEFINITIONS.items():
            assert len(defn.documents) >= 1, f"{req_id} has no documents"

    def test_definitions_have_tasks(self):
        """Each definition should have at least one task."""
        for req_id, defn in AUTOFIX_DEFINITIONS.items():
            assert len(defn.tasks) >= 1, f"{req_id} has no tasks"

    def test_definitions_have_self_check(self):
        """Each definition should have at least one self-check question."""
        for req_id, defn in AUTOFIX_DEFINITIONS.items():
            assert len(defn.self_check_questions) >= 1, (
                f"{req_id} has no self-check questions"
            )

    def test_all_autofix_requirement_ids(self):
        """all_autofix_requirement_ids should return sorted list."""
        ids = all_autofix_requirement_ids()
        assert len(ids) == 28
        assert ids == sorted(ids)

    def test_document_templates_have_placeholders(self):
        """Document templates should contain org_name and date placeholders."""
        for req_id, defn in AUTOFIX_DEFINITIONS.items():
            for doc in defn.documents:
                assert "{org_name}" in doc.template or "{date}" in doc.template, (
                    f"{req_id}/{doc.title} has no placeholders"
                )

    def test_task_definitions_have_valid_depends_on(self):
        """Task depends_on references should be valid indices."""
        for req_id, defn in AUTOFIX_DEFINITIONS.items():
            num_tasks = len(defn.tasks)
            for i, task in enumerate(defn.tasks):
                for dep in task.depends_on:
                    assert 0 <= dep < i, (
                        f"{req_id} task {i} depends_on {dep} is invalid "
                        f"(must be < {i})"
                    )


# ── AutoFixEngineのテスト ──

class TestAutoFixEngine:
    """AutoFixEngine tests."""

    def setup_method(self):
        self.engine = AutoFixEngine()
        self.org_context = {
            "org_name": "テスト株式会社",
            "industry": "IT・通信",
            "size": "medium",
        }

    def test_fix_requirement_returns_result(self):
        """fix_requirement should return an AutoFixResult."""
        result = self.engine.fix_requirement("C01-R01", self.org_context)
        assert isinstance(result, AutoFixResult)
        assert result.requirement_id == "C01-R01"
        assert result.requirement_title == "人間の尊厳・自律の尊重"
        assert result.status == "generated"

    def test_fix_requirement_generates_documents(self):
        """fix_requirement should generate documents with org_name filled in."""
        result = self.engine.fix_requirement("C01-R01", self.org_context)
        assert len(result.generated_documents) >= 1
        has_org_name = False
        for doc in result.generated_documents:
            assert isinstance(doc, GeneratedDocument)
            assert doc.title
            assert doc.content
            assert doc.doc_type in ("policy", "checklist", "template", "procedure")
            assert doc.status == DocumentStatus.DRAFT
            if "テスト株式会社" in doc.content:
                has_org_name = True
        # At least one document should contain the org name
        assert has_org_name, "No document contains the org name"

    def test_fix_requirement_generates_tasks(self):
        """fix_requirement should generate tasks."""
        result = self.engine.fix_requirement("C01-R01", self.org_context)
        assert len(result.tasks) >= 1
        for task in result.tasks:
            assert isinstance(task, AutoFixTask)
            assert task.title
            assert task.assignee_role
            assert task.deadline_days > 0

    def test_fix_requirement_generates_checklist(self):
        """fix_requirement should generate a checklist."""
        result = self.engine.fix_requirement("C01-R01", self.org_context)
        assert len(result.checklist) >= 1
        for item in result.checklist:
            assert isinstance(item, ChecklistItem)
            assert item.text
            assert item.checked is False

    def test_fix_requirement_generates_self_check(self):
        """fix_requirement should generate self-check questions."""
        result = self.engine.fix_requirement("C01-R01", self.org_context)
        assert len(result.self_check_questions) >= 1
        for sc in result.self_check_questions:
            assert isinstance(sc, SelfCheckItem)
            assert sc.question
            assert sc.expected_answer == "yes"

    def test_fix_requirement_without_org_context(self):
        """fix_requirement should work without org_context."""
        result = self.engine.fix_requirement("C01-R01")
        assert isinstance(result, AutoFixResult)
        # Default org name should be used
        assert result.generated_documents[0].content is not None

    def test_fix_all_gaps_skips_compliant(self):
        """fix_all_gaps should skip compliant requirements."""
        gaps = [
            RequirementGap(
                req_id="C01-R01",
                category_id="C01",
                title="人間の尊厳・自律の尊重",
                status=ComplianceStatus.COMPLIANT,
                current_score=3.5,
            ),
            RequirementGap(
                req_id="C02-R01",
                category_id="C02",
                title="リスクアセスメントの実施",
                status=ComplianceStatus.NON_COMPLIANT,
                current_score=0.5,
            ),
            RequirementGap(
                req_id="C03-R01",
                category_id="C03",
                title="バイアス評価の実施",
                status=ComplianceStatus.PARTIAL,
                current_score=1.8,
            ),
        ]
        results = self.engine.fix_all_gaps(gaps, self.org_context)
        assert len(results) == 2  # compliant is skipped
        req_ids = [r.requirement_id for r in results]
        assert "C01-R01" not in req_ids
        assert "C02-R01" in req_ids
        assert "C03-R01" in req_ids

    def test_fix_all_gaps_empty(self):
        """fix_all_gaps with no gaps should return empty list."""
        results = self.engine.fix_all_gaps([], self.org_context)
        assert results == []

    def test_fix_all_gaps_all_compliant(self):
        """fix_all_gaps when all are compliant should return empty."""
        gaps = [
            RequirementGap(
                req_id="C01-R01",
                category_id="C01",
                title="test",
                status=ComplianceStatus.COMPLIANT,
                current_score=4.0,
            ),
        ]
        results = self.engine.fix_all_gaps(gaps, self.org_context)
        assert results == []

    def test_generate_policy_document(self):
        """generate_policy_document should return Markdown content."""
        content = self.engine.generate_policy_document("C01-R01", self.org_context)
        assert isinstance(content, str)
        assert len(content) > 0
        assert "テスト株式会社" in content

    def test_generate_checklist(self):
        """generate_checklist should return a list of ChecklistItem."""
        items = self.engine.generate_checklist("C01-R01")
        assert isinstance(items, list)
        assert len(items) >= 1
        assert all(isinstance(i, ChecklistItem) for i in items)

    def test_generate_evidence_template(self):
        """generate_evidence_template should return template content."""
        content = self.engine.generate_evidence_template("C02-R01", self.org_context)
        assert isinstance(content, str)
        assert len(content) > 0

    def test_generate_task_plan(self):
        """generate_task_plan should return tasks with roles and deadlines."""
        tasks = self.engine.generate_task_plan("C01-R01", self.org_context)
        assert isinstance(tasks, list)
        assert len(tasks) >= 1
        for task in tasks:
            assert isinstance(task, AutoFixTask)
            assert task.title
            assert task.assignee_role
            assert task.deadline_days > 0

    def test_all_requirements_can_be_fixed(self):
        """All 28 requirements should produce a valid AutoFixResult."""
        for req in all_requirements():
            result = self.engine.fix_requirement(req.req_id, self.org_context)
            assert isinstance(result, AutoFixResult)
            assert result.requirement_id == req.req_id
            assert len(result.generated_documents) >= 1
            assert len(result.tasks) >= 1

    def test_fix_requirement_c02_r01_has_risk_template(self):
        """C02-R01 should generate a risk assessment template."""
        result = self.engine.fix_requirement("C02-R01", self.org_context)
        doc_titles = [d.title for d in result.generated_documents]
        assert "AIリスクアセスメントシート" in doc_titles

    def test_fix_requirement_c04_r01_has_privacy_policy(self):
        """C04-R01 should generate a privacy policy."""
        result = self.engine.fix_requirement("C04-R01", self.org_context)
        doc_types = [d.doc_type for d in result.generated_documents]
        assert "policy" in doc_types

    def test_fix_requirement_c05_r01_has_security_docs(self):
        """C05-R01 should generate threat modeling and security checklist."""
        result = self.engine.fix_requirement("C05-R01", self.org_context)
        doc_titles = [d.title for d in result.generated_documents]
        assert "AI脅威モデリングシート" in doc_titles
        assert "AIセキュリティチェックリスト" in doc_titles


# ── 統合テスト ──

class TestAutoFixIntegration:
    """Integration tests with gap analysis."""

    @pytest.mark.asyncio
    async def test_autofix_from_assessment(self):
        """AutoFix should work with real gap analysis results."""
        # Run assessment with all zeros (worst case)
        assessment = run_assessment("org-test", _make_answers(0))
        gap_result = await run_gap_analysis(assessment)

        engine = AutoFixEngine()
        org_context = {"org_name": "統合テスト株式会社"}

        results = engine.fix_all_gaps(gap_result.gaps, org_context)

        # All should be non-compliant → all should have fixes
        assert len(results) == 28
        for r in results:
            assert isinstance(r, AutoFixResult)
            assert len(r.generated_documents) >= 1
            assert len(r.tasks) >= 1

    @pytest.mark.asyncio
    async def test_autofix_perfect_score_no_fixes(self):
        """Perfect score should produce no AutoFix results."""
        assessment = run_assessment("org-test", _make_answers(4))
        gap_result = await run_gap_analysis(assessment)

        engine = AutoFixEngine()
        results = engine.fix_all_gaps(gap_result.gaps)

        # All compliant → no fixes needed
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_autofix_partial_score(self):
        """Partial scores should produce fixes only for non-compliant items."""
        assessment = run_assessment("org-test", _make_answers(2))
        gap_result = await run_gap_analysis(assessment)

        engine = AutoFixEngine()
        results = engine.fix_all_gaps(gap_result.gaps)

        # Some partial, some compliant
        non_compliant_or_partial = [
            g for g in gap_result.gaps
            if g.status != ComplianceStatus.COMPLIANT
        ]
        assert len(results) == len(non_compliant_or_partial)


# ── モデルのテスト ──

class TestAutoFixModels:
    """Tests for AutoFix-related Pydantic models."""

    def test_autofix_result_model(self):
        """AutoFixResult should serialize/deserialize correctly."""
        result = AutoFixResult(
            requirement_id="C01-R01",
            requirement_title="テスト要件",
            generated_documents=[
                GeneratedDocument(
                    title="テスト文書",
                    content="# テスト",
                    doc_type="policy",
                )
            ],
            checklist=[ChecklistItem(text="チェック1")],
            tasks=[
                AutoFixTask(
                    title="タスク1",
                    description="説明",
                    assignee_role="担当者",
                    deadline_days=14,
                )
            ],
            self_check_questions=[
                SelfCheckItem(question="質問1", expected_answer="yes")
            ],
        )
        # Serialize
        json_str = result.model_dump_json()
        # Deserialize
        restored = AutoFixResult.model_validate_json(json_str)
        assert restored.requirement_id == "C01-R01"
        assert len(restored.generated_documents) == 1
        assert len(restored.tasks) == 1

    def test_document_status_enum(self):
        """DocumentStatus enum values."""
        assert DocumentStatus.DRAFT == "draft"
        assert DocumentStatus.APPROVED == "approved"

    def test_generated_document_default_status(self):
        """GeneratedDocument should default to DRAFT status."""
        doc = GeneratedDocument(
            title="test",
            content="test content",
            doc_type="policy",
        )
        assert doc.status == DocumentStatus.DRAFT

    def test_checklist_item_default_unchecked(self):
        """ChecklistItem should default to unchecked."""
        item = ChecklistItem(text="test")
        assert item.checked is False

    def test_self_check_item_default_not_answered(self):
        """SelfCheckItem should default to not answered."""
        item = SelfCheckItem(question="test?", expected_answer="yes")
        assert item.answered is False
