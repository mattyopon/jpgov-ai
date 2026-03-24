# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for NIST AI RMF 1.0 guidelines."""

from __future__ import annotations

from app.guidelines.nist_ai_rmf import (
    NIST_FUNCTIONS,
    all_nist_subcategories,
    all_nist_subcategory_ids,
    get_meti_to_nist_mapping,
    get_nist_function,
    get_nist_subcategory,
    get_nist_to_iso_mapping,
    get_nist_to_meti_mapping,
)


class TestNISTAIRMF:
    """NIST AI RMF guideline data tests."""

    def test_four_core_functions(self):
        assert len(NIST_FUNCTIONS) == 4
        ids = {f.function_id for f in NIST_FUNCTIONS}
        assert ids == {"GOVERN", "MAP", "MEASURE", "MANAGE"}

    def test_get_function(self):
        gov = get_nist_function("GOVERN")
        assert gov is not None
        assert gov.title.startswith("GOVERN")
        assert len(gov.categories) > 0

    def test_get_nonexistent_function(self):
        assert get_nist_function("NONEXIST") is None

    def test_subcategories_exist(self):
        subs = all_nist_subcategories()
        assert len(subs) >= 15

    def test_subcategory_ids_unique(self):
        ids = all_nist_subcategory_ids()
        assert len(ids) == len(set(ids))

    def test_get_subcategory(self):
        sub = get_nist_subcategory("GOVERN-1.1")
        assert sub is not None
        assert len(sub.suggested_actions) > 0
        assert len(sub.meti_mapping) > 0

    def test_get_nonexistent_subcategory(self):
        assert get_nist_subcategory("GOVERN-99.99") is None

    def test_all_subcategories_have_meti_mapping(self):
        for sub in all_nist_subcategories():
            assert isinstance(sub.meti_mapping, list)
            assert len(sub.meti_mapping) > 0, f"{sub.subcategory_id} missing METI mapping"

    def test_all_subcategories_have_actions(self):
        for sub in all_nist_subcategories():
            assert len(sub.suggested_actions) > 0, f"{sub.subcategory_id} missing actions"

    def test_nist_to_meti_mapping(self):
        mapping = get_nist_to_meti_mapping()
        assert isinstance(mapping, dict)
        assert len(mapping) > 0

    def test_meti_to_nist_mapping(self):
        mapping = get_meti_to_nist_mapping()
        assert isinstance(mapping, dict)
        assert len(mapping) > 0

    def test_nist_to_iso_mapping(self):
        mapping = get_nist_to_iso_mapping()
        assert isinstance(mapping, dict)
        assert len(mapping) > 0

    def test_govern_has_multiple_categories(self):
        gov = get_nist_function("GOVERN")
        assert gov is not None
        assert len(gov.categories) >= 3

    def test_each_function_has_categories(self):
        for func in NIST_FUNCTIONS:
            assert len(func.categories) > 0, f"{func.function_id} has no categories"

    def test_each_category_has_subcategories(self):
        for func in NIST_FUNCTIONS:
            for cat in func.categories:
                assert len(cat.subcategories) > 0, f"{cat.category_id} has no subcategories"
