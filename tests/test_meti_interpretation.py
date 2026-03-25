# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for METI interpretation guide."""

from __future__ import annotations

from app.guidelines.meti_interpretation import (
    METI_INTERPRETATIONS,
    all_interpretations,
    get_interpretation,
    get_interpreted_requirement_ids,
)


class TestMETIInterpretation:
    """METI解釈ガイドのテスト."""

    def test_interpretations_exist(self):
        """解釈データが存在すること."""
        assert len(METI_INTERPRETATIONS) >= 10

    def test_get_interpretation_found(self):
        """存在する要件IDで解釈を取得できること."""
        interp = get_interpretation("C01-R02")
        assert interp is not None
        assert interp.req_id == "C01-R02"

    def test_get_interpretation_not_found(self):
        """存在しない要件IDでNoneが返ること."""
        assert get_interpretation("NONEXISTENT") is None

    def test_all_interpretations_returns_list(self):
        """全解釈がリストで返ること."""
        result = all_interpretations()
        assert isinstance(result, list)
        assert len(result) == len(METI_INTERPRETATIONS)

    def test_get_interpreted_requirement_ids(self):
        """解釈済み要件IDが取得できること."""
        ids = get_interpreted_requirement_ids()
        assert "C01-R02" in ids
        assert "C02-R01" in ids

    def test_interpretation_has_required_fields(self):
        """各解釈が必須フィールドを持つこと."""
        for interp in METI_INTERPRETATIONS:
            assert interp.req_id, f"req_id is empty for {interp}"
            assert interp.official_text, f"official_text is empty for {interp.req_id}"
            assert interp.interpretation, f"interpretation is empty for {interp.req_id}"
            assert interp.common_misunderstanding, f"common_misunderstanding is empty for {interp.req_id}"
            assert interp.auditor_focus, f"auditor_focus is empty for {interp.req_id}"
            assert interp.best_practice, f"best_practice is empty for {interp.req_id}"
            assert interp.pitfall, f"pitfall is empty for {interp.req_id}"

    def test_unique_req_ids(self):
        """要件IDが一意であること."""
        ids = [i.req_id for i in METI_INTERPRETATIONS]
        assert len(ids) == len(set(ids))

    def test_iso42001_cross_ref(self):
        """ISO 42001のクロスリファレンスが含まれること."""
        interp = get_interpretation("C02-R01")
        assert interp is not None
        assert interp.iso42001_cross_ref != ""

    def test_interpretation_content_length(self):
        """解釈が十分な長さを持つこと（最低50文字）."""
        for interp in METI_INTERPRETATIONS:
            assert len(interp.interpretation) >= 50, (
                f"{interp.req_id} interpretation too short"
            )
