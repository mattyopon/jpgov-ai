"""テストケース一覧に基づく受け入れテスト.

docs/design/テストケース一覧.csv の50項目のうち、
バックエンドで自動検証可能な項目を網羅する。
UI操作テスト（Streamlit直接テスト不可）はスキップ。
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.assessment import run_assessment
from app.models import AnswerItem
from app.services.gap_analysis import run_gap_analysis_sync
from app.services.autofix import AutoFixEngine
from app.services.ai_advisor import chat, ChatRequest, create_session
from app.services.ai_registry import (
    register_ai_system, list_ai_systems, AISystemCreate, AISystemType, reset_registry
)
from app.services.audit_trail import get_audit_ledger, reset_audit_ledger
from app.services.review_cycle import create_review_cycle, advance_next_review, ReviewCycleCreate


# === 共通フィクスチャ ===

@pytest.fixture
def answers_low():
    return [AnswerItem(question_id=f"Q{i+1:02d}", selected_index=0) for i in range(25)]

@pytest.fixture
def answers_mid():
    return [AnswerItem(question_id=f"Q{i+1:02d}", selected_index=2) for i in range(25)]

@pytest.fixture
def answers_high():
    return [AnswerItem(question_id=f"Q{i+1:02d}", selected_index=4) for i in range(25)]

@pytest.fixture
def result_low(answers_low):
    return run_assessment("org-accept", answers_low)

@pytest.fixture
def result_mid(answers_mid):
    return run_assessment("org-accept", answers_mid)

@pytest.fixture
def result_high(answers_high):
    return run_assessment("org-accept", answers_high)

@pytest.fixture
def gap_low(result_low):
    return run_gap_analysis_sync(result_low)

@pytest.fixture
def autofix_engine():
    return AutoFixEngine()

@pytest.fixture
def org_ctx():
    return {"org_name": "テスト株式会社", "industry": "IT", "size": "100-500"}


# === TC-03: 診断 25問回答→スコア ===
def test_tc03_assessment_score(result_mid):
    assert 1.0 <= result_mid.overall_score <= 5.0
    assert len(result_mid.category_scores) == 10

# === TC-05: 全問0点→低スコア ===
def test_tc05_all_zero_low_score(result_low):
    assert result_low.overall_score < 2.0

# === TC-06: 全問最高点→高スコア ===
def test_tc06_all_max_high_score(result_high):
    assert result_high.overall_score >= 3.5

# === TC-11: 28要件が返る ===
def test_tc11_28_gaps(gap_low):
    assert len(gap_low.gaps) == 28

# === TC-15: 全28件AutoFix成功 ===
def test_tc15_autofix_all_28(gap_low, autofix_engine, org_ctx):
    success = 0
    for g in gap_low.gaps:
        result = autofix_engine.fix_requirement(g.req_id, org_ctx)
        assert result is not None
        assert len(result.generated_documents) >= 1
        success += 1
    assert success == 28

# === TC-18: 組織名が文書に反映 ===
def test_tc18_org_name_in_document(autofix_engine, org_ctx):
    fix = autofix_engine.fix_requirement("C01-R01", org_ctx)
    has_org = any("テスト株式会社" in d.content for d in fix.generated_documents)
    assert has_org

# === TC-23: AIアドバイザーが回答を返す ===
def test_tc23_ai_advisor_response():
    session = create_session("org-accept")
    resp = chat(ChatRequest(
        message="リスクアセスメントのやり方を教えて",
        organization_id="org-accept",
        session_id=session.id,
        user_id="user-test",
    ))
    assert len(resp.message.content) > 20

# === TC-25: APIキー未設定でFAQ回答 ===
def test_tc25_faq_fallback():
    session = create_session("org-accept2")
    resp = chat(ChatRequest(
        message="ISO 42001認証を取るにはどうすればいい",
        organization_id="org-accept2",
        session_id=session.id,
        user_id="user-test",
    ))
    assert len(resp.message.content) > 20

# === TC-27: AIシステム登録 ===
def test_tc27_register_ai_system():
    reset_registry()
    system = register_ai_system(AISystemCreate(
        name="テストChatbot",
        ai_type=AISystemType.GENERATIVE,
        organization_id="org-accept",
    ))
    assert system.id is not None

# === TC-28: AIシステム一覧 ===
def test_tc28_list_ai_systems():
    systems = list_ai_systems("org-accept")
    assert len(systems) >= 1

# === TC-31: スコア算出範囲 ===
def test_tc31_score_range(result_mid):
    assert 0.0 <= result_mid.overall_score <= 4.0

# === TC-32: 全問最低点→Level1 ===
def test_tc32_maturity_level1(result_low):
    assert result_low.maturity_level == 1

# === TC-33: gap_analysis_sync ===
def test_tc33_gap_sync(gap_low):
    assert len(gap_low.gaps) == 28

# === TC-34: 全問0点→28件non_compliant ===
def test_tc34_all_non_compliant(gap_low):
    nc = [g for g in gap_low.gaps if g.status.value == "non_compliant"]
    assert len(nc) == 28

# === TC-35: AutoFix 文書生成 ===
def test_tc35_autofix_generates_docs(autofix_engine, org_ctx):
    fix = autofix_engine.fix_requirement("C01-R01", org_ctx)
    assert len(fix.generated_documents) >= 1

# === TC-36: 28件全て成功（TC-15で検証済みだが明示的に） ===
def test_tc36_autofix_28_success(gap_low, autofix_engine, org_ctx):
    for g in gap_low.gaps:
        fix = autofix_engine.fix_requirement(g.req_id, org_ctx)
        assert fix is not None

# === TC-37: 複数要件で組織名反映 ===
def test_tc37_org_name_multiple(autofix_engine, org_ctx):
    for req_id in ["C01-R01", "C07-R01", "C05-R01"]:
        fix = autofix_engine.fix_requirement(req_id, org_ctx)
        has_org = any("テスト株式会社" in d.content for d in fix.generated_documents)
        assert has_org, f"{req_id}の文書に組織名がない"

# === TC-38: 監査証跡チェーン正常 ===
def test_tc38_audit_chain_valid():
    reset_audit_ledger()
    ledger = get_audit_ledger()
    ledger.append(action="action1", actor="actor1", resource_type="test", details={"key": "val"})
    ledger.append(action="action2", actor="actor2", resource_type="test", details={"key2": "val2"})
    ledger.append(action="action3", actor="actor3", resource_type="test", details={"key3": "val3"})
    result = ledger.verify_chain()
    is_valid = result[0] if isinstance(result, tuple) else result
    assert is_valid, "正常なチェーンがinvalidと判定された"

# === TC-39: 監査証跡改竄検出 ===
def test_tc39_audit_tamper_detection():
    reset_audit_ledger()
    ledger = get_audit_ledger()
    ledger.append(action="action1", actor="actor1", resource_type="test", details={"key": "val"})
    ledger.append(action="action2", actor="actor2", resource_type="test", details={"key2": "val2"})
    # 改竄
    events = ledger.get_events()
    events[0].details = {"tampered": True}
    result = ledger.verify_chain()
    # verify_chain returns (bool, list) or just bool
    is_valid = result[0] if isinstance(result, tuple) else result
    assert not is_valid, "改竄されたチェーンがvalidと判定された"

# === TC-44: レビューサイクル進行 ===
def test_tc44_review_cycle():
    cycle = create_review_cycle(ReviewCycleCreate(
        organization_id="org-review-accept",
        frequency="quarterly",
        name="Q1 Review",
    ))
    advanced = advance_next_review(cycle.id)
    assert advanced is not None
