# Copyright (c) 2026 Yutaro Maeda
# Licensed under the MIT License. See LICENSE file for details.

"""Tests for the AI Promotion Act guidelines."""

from __future__ import annotations

from app.guidelines.ai_promotion_act import (
    ACT_CHAPTERS,
    all_act_requirements,
    get_act_requirement,
    get_act_to_iso_mapping,
    get_meti_to_act_mapping,
)


class TestAIPromotionAct:
    """AI Promotion Act guideline data tests."""

    def test_chapters_exist(self):
        assert len(ACT_CHAPTERS) >= 6

    def test_all_requirements_not_empty(self):
        reqs = all_act_requirements()
        assert len(reqs) > 0

    def test_get_requirement(self):
        req = get_act_requirement("APA-01")
        assert req is not None
        assert req.title == "基本理念の遵守"

    def test_all_have_meti_mapping(self):
        for req in all_act_requirements():
            assert isinstance(req.meti_mapping, list)
            assert len(req.meti_mapping) > 0

    def test_obligation_types(self):
        reqs = all_act_requirements()
        mandatory = [r for r in reqs if r.obligation_type == "mandatory"]
        effort = [r for r in reqs if r.obligation_type == "effort"]
        assert len(mandatory) > 0
        assert len(effort) > 0

    def test_meti_to_act_mapping(self):
        mapping = get_meti_to_act_mapping()
        assert isinstance(mapping, dict)
        assert len(mapping) > 0

    def test_act_to_iso_mapping(self):
        mapping = get_act_to_iso_mapping()
        assert isinstance(mapping, dict)
        assert len(mapping) > 0

    def test_unique_req_ids(self):
        reqs = all_act_requirements()
        ids = [r.req_id for r in reqs]
        assert len(ids) == len(set(ids))
