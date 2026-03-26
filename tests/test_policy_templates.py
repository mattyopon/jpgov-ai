# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for policy_templates.py — 28要件の実用的雛形文書."""

from __future__ import annotations

from app.guidelines.meti_v1_1 import all_requirements
from app.knowledge.policy_templates import (
    POLICY_TEMPLATES,
    all_template_requirement_ids,
    get_policy_template,
)


class TestPolicyTemplatesCoverage:
    """全28要件に雛形文書が存在することを検証."""

    def test_all_28_requirements_have_templates(self):
        """All 28 requirements should have a policy template."""
        all_reqs = all_requirements()
        assert len(all_reqs) == 28
        for req in all_reqs:
            template = get_policy_template(req.req_id)
            assert template is not None, f"Missing policy template for {req.req_id}"

    def test_template_count_matches_requirements(self):
        """Template count should be exactly 28."""
        assert len(POLICY_TEMPLATES) == 28

    def test_all_template_requirement_ids_sorted(self):
        """all_template_requirement_ids should return sorted list."""
        ids = all_template_requirement_ids()
        assert len(ids) == 28
        assert ids == sorted(ids)


class TestPolicyTemplatesPlaceholders:
    """雛形文書に必須プレースホルダが含まれていることを検証."""

    def test_all_templates_have_org_name_placeholder(self):
        """All templates should contain {org_name} placeholder."""
        for req_id, template in POLICY_TEMPLATES.items():
            assert "{org_name}" in template, (
                f"{req_id} template is missing {{org_name}} placeholder"
            )

    def test_all_templates_have_date_placeholder(self):
        """All templates should contain {date} placeholder."""
        for req_id, template in POLICY_TEMPLATES.items():
            assert "{date}" in template, (
                f"{req_id} template is missing {{date}} placeholder"
            )

    def test_all_templates_renderable_with_all_placeholders(self):
        """All templates should be renderable with standard placeholders."""
        context = {
            "org_name": "テスト株式会社",
            "date": "2026年01月01日",
            "industry": "IT・通信",
            "ai_usage": "production",
        }
        for req_id, template in POLICY_TEMPLATES.items():
            try:
                rendered = template.format(**context)
                assert len(rendered) > 0, f"{req_id} rendered to empty string"
            except KeyError as e:
                raise AssertionError(
                    f"{req_id} template has unknown placeholder: {e}"
                ) from e


class TestPolicyTemplatesContent:
    """雛形文書の内容品質を検証."""

    def test_all_templates_are_markdown(self):
        """All templates should start with a Markdown heading."""
        for req_id, template in POLICY_TEMPLATES.items():
            assert template.strip().startswith("#"), (
                f"{req_id} template does not start with a Markdown heading"
            )

    def test_all_templates_have_minimum_length(self):
        """All templates should be at least 500 characters (A4 half page)."""
        for req_id, template in POLICY_TEMPLATES.items():
            assert len(template) >= 500, (
                f"{req_id} template is too short ({len(template)} chars). "
                "Expected at least 500 characters for a practical document."
            )

    def test_all_templates_have_draft_notice(self):
        """All templates should contain a draft notice."""
        for req_id, template in POLICY_TEMPLATES.items():
            assert "JPGovAI" in template or "ドラフト" in template, (
                f"{req_id} template is missing draft notice"
            )

    def test_get_policy_template_returns_none_for_unknown(self):
        """get_policy_template should return None for unknown requirement ID."""
        result = get_policy_template("UNKNOWN-999")
        assert result is None

    def test_templates_have_section_structure(self):
        """All templates should have at least 2 section headings (##)."""
        for req_id, template in POLICY_TEMPLATES.items():
            section_count = template.count("\n## ")
            assert section_count >= 2, (
                f"{req_id} template has only {section_count} sections. "
                "Expected at least 2 for a practical document."
            )
