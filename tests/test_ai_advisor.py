# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for the AI Advisor (Chatbot) service."""

from __future__ import annotations

import pytest

from app.services.ai_advisor import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatSession,
    chat,
    create_session,
    delete_session,
    get_session,
    list_sessions,
    reset_advisor,
)


@pytest.fixture(autouse=True)
def _reset():
    reset_advisor()
    yield
    reset_advisor()


ORG_ID = "org-test-001"
USER_ID = "user-001"


# ── Session Tests ───────────────────────────────────────────────

class TestSessions:
    def test_create_session(self):
        session = create_session(ORG_ID, USER_ID)
        assert session.id
        assert session.organization_id == ORG_ID
        assert session.user_id == USER_ID
        assert session.messages == []

    def test_create_session_with_context(self):
        ctx = {"organization_name": "テスト株式会社", "industry": "IT"}
        session = create_session(ORG_ID, USER_ID, context=ctx)
        assert session.context["organization_name"] == "テスト株式会社"

    def test_get_session(self):
        session = create_session(ORG_ID, USER_ID)
        fetched = get_session(session.id)
        assert fetched is not None
        assert fetched.id == session.id

    def test_get_nonexistent(self):
        assert get_session("nonexistent") is None

    def test_list_sessions(self):
        create_session(ORG_ID, USER_ID)
        create_session(ORG_ID, USER_ID)
        create_session(ORG_ID, "other-user")

        all_sessions = list_sessions(ORG_ID)
        assert len(all_sessions) == 3

        user_sessions = list_sessions(ORG_ID, USER_ID)
        assert len(user_sessions) == 2

    def test_list_sessions_other_org(self):
        create_session(ORG_ID, USER_ID)
        assert list_sessions("other-org") == []

    def test_delete_session(self):
        session = create_session(ORG_ID, USER_ID)
        assert delete_session(session.id) is True
        assert get_session(session.id) is None

    def test_delete_nonexistent(self):
        assert delete_session("nonexistent") is False


# ── Chat Tests (FAQ Fallback) ───────────────────────────────────

class TestChatFAQ:
    def test_chat_risk_assessment(self):
        """リスクアセスメントに関する質問にFAQで回答."""
        response = chat(ChatRequest(
            organization_id=ORG_ID,
            user_id=USER_ID,
            message="リスクアセスメントのやり方を教えて",
        ))
        assert response.session_id
        assert response.message.role == "assistant"
        assert "リスクアセスメント" in response.message.content
        assert len(response.sources) > 0

    def test_chat_iso42001(self):
        """ISO 42001に関する質問にFAQで回答."""
        response = chat(ChatRequest(
            organization_id=ORG_ID,
            user_id=USER_ID,
            message="ISO 42001認証を取るには何から始めるべき？",
        ))
        assert "ISO 42001" in response.message.content or "認証" in response.message.content

    def test_chat_incident(self):
        """インシデントに関する質問にFAQで回答."""
        response = chat(ChatRequest(
            organization_id=ORG_ID,
            user_id=USER_ID,
            message="このインシデントは報告対象？",
        ))
        assert "インシデント" in response.message.content or "報告" in response.message.content

    def test_chat_benchmark(self):
        """ベンチマークに関する質問にFAQで回答."""
        response = chat(ChatRequest(
            organization_id=ORG_ID,
            user_id=USER_ID,
            message="うちの業界のベンチマークはどうなっている？",
        ))
        assert "ベンチマーク" in response.message.content

    def test_chat_policy(self):
        """ポリシーに関する質問にFAQで回答."""
        response = chat(ChatRequest(
            organization_id=ORG_ID,
            user_id=USER_ID,
            message="ポリシーの作り方を教えて",
        ))
        assert "ポリシー" in response.message.content

    def test_chat_unknown_question(self):
        """不明な質問にはデフォルト回答."""
        response = chat(ChatRequest(
            organization_id=ORG_ID,
            user_id=USER_ID,
            message="量子コンピュータについて教えて",
        ))
        assert response.message.content
        assert response.message.role == "assistant"


# ── Session Continuity Tests ────────────────────────────────────

class TestSessionContinuity:
    def test_new_session_created(self):
        """session_idなしで新規セッションが作成される."""
        response = chat(ChatRequest(
            organization_id=ORG_ID,
            user_id=USER_ID,
            message="テスト",
        ))
        assert response.session_id

        session = get_session(response.session_id)
        assert session is not None
        assert len(session.messages) == 2  # user + assistant

    def test_continue_session(self):
        """既存セッションに追加できる."""
        r1 = chat(ChatRequest(
            organization_id=ORG_ID,
            user_id=USER_ID,
            message="リスクアセスメントについて",
        ))
        r2 = chat(ChatRequest(
            session_id=r1.session_id,
            organization_id=ORG_ID,
            user_id=USER_ID,
            message="もう少し詳しく教えて",
        ))
        assert r2.session_id == r1.session_id

        session = get_session(r1.session_id)
        assert session is not None
        assert len(session.messages) == 4  # 2 user + 2 assistant

    def test_session_title_set_from_first_message(self):
        """セッションタイトルが最初のメッセージから設定される."""
        response = chat(ChatRequest(
            organization_id=ORG_ID,
            user_id=USER_ID,
            message="リスクアセスメントのやり方",
        ))
        session = get_session(response.session_id)
        assert session is not None
        assert session.title

    def test_message_roles(self):
        """メッセージのロールが正しい."""
        response = chat(ChatRequest(
            organization_id=ORG_ID,
            message="テスト質問",
        ))
        session = get_session(response.session_id)
        assert session is not None
        assert session.messages[0].role == "user"
        assert session.messages[1].role == "assistant"

    def test_invalid_session_creates_new(self):
        """存在しないsession_idの場合、新規セッションが作成される."""
        response = chat(ChatRequest(
            session_id="invalid-session-id",
            organization_id=ORG_ID,
            message="テスト",
        ))
        assert response.session_id != "invalid-session-id"


# ── Model Tests ─────────────────────────────────────────────────

class TestModels:
    def test_chat_message_defaults(self):
        msg = ChatMessage(content="Hello")
        assert msg.id
        assert msg.role == "user"
        assert msg.timestamp

    def test_chat_session_defaults(self):
        session = ChatSession(organization_id=ORG_ID)
        assert session.id
        assert session.messages == []
        assert session.created_at

    def test_chat_response(self):
        msg = ChatMessage(role="assistant", content="Reply")
        resp = ChatResponse(session_id="s1", message=msg, sources=["src1"])
        assert resp.session_id == "s1"
        assert resp.sources == ["src1"]
