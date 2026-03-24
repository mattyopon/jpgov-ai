# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for ISO 42001 detailed requirements, controls, and implementation guidance."""

from __future__ import annotations

from app.guidelines.iso42001_detailed import (
    all_controls,
    all_detailed_requirements,
    get_check_questions_by_clause,
    get_common_gaps_all,
    get_control,
    get_detailed_requirement,
)


class TestISO42001Detailed:
    """ISO 42001 detailed knowledge base tests."""

    def test_detailed_requirements_exist(self):
        reqs = all_detailed_requirements()
        assert len(reqs) >= 20  # All ISO requirements should be detailed

    def test_controls_exist(self):
        controls = all_controls()
        assert len(controls) >= 10

    def test_get_detailed_requirement(self):
        req = get_detailed_requirement("ISO-4.1")
        assert req is not None
        assert req.title == "組織とその状況の理解"
        assert len(req.implementation_guidance) > 0
        assert len(req.evidence_examples) > 0
        assert len(req.common_gaps) > 0
        assert len(req.check_questions) > 0

    def test_get_control(self):
        ctrl = get_control("A.2.2")
        assert ctrl is not None
        assert ctrl.title == "AI方針"
        assert len(ctrl.implementation_guidance) > 0

    def test_get_nonexistent_requirement(self):
        assert get_detailed_requirement("ISO-99.99") is None

    def test_get_nonexistent_control(self):
        assert get_control("A.99.99") is None

    def test_all_requirements_have_guidance(self):
        for req in all_detailed_requirements():
            assert len(req.implementation_guidance) > 0, f"{req.req_id} missing guidance"
            assert len(req.evidence_examples) > 0, f"{req.req_id} missing evidence"
            assert len(req.common_gaps) > 0, f"{req.req_id} missing common gaps"
            assert len(req.check_questions) > 0, f"{req.req_id} missing check questions"

    def test_all_requirements_have_meti_mapping(self):
        for req in all_detailed_requirements():
            assert isinstance(req.meti_mapping, list)
            assert len(req.meti_mapping) > 0, f"{req.req_id} missing METI mapping"

    def test_unique_req_ids(self):
        reqs = all_detailed_requirements()
        ids = [r.req_id for r in reqs]
        assert len(ids) == len(set(ids))

    def test_unique_control_ids(self):
        controls = all_controls()
        ids = [c.control_id for c in controls]
        assert len(ids) == len(set(ids))

    def test_check_questions_by_clause(self):
        questions = get_check_questions_by_clause("4")
        assert len(questions) > 0

    def test_check_questions_empty_clause(self):
        questions = get_check_questions_by_clause("99")
        assert questions == []

    def test_common_gaps_all(self):
        gaps = get_common_gaps_all()
        assert len(gaps) > 0
        assert all("req_id" in g for g in gaps)
        assert all("gap" in g for g in gaps)

    def test_nist_mapping_present(self):
        """At least some requirements should have NIST mapping."""
        reqs = all_detailed_requirements()
        with_nist = [r for r in reqs if r.nist_mapping]
        assert len(with_nist) > 5

    def test_eu_mapping_present(self):
        """At least some requirements should have EU AI Act mapping."""
        reqs = all_detailed_requirements()
        with_eu = [r for r in reqs if r.eu_ai_act_mapping]
        assert len(with_eu) > 3

    def test_controls_referenced_in_requirements(self):
        """Controls referenced in requirements should exist."""
        for req in all_detailed_requirements():
            for ctrl in req.controls:
                assert get_control(ctrl.control_id) is not None
