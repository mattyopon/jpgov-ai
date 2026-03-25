# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""AI Chatbot（対話型アドバイザー）.

「この要件はうちの場合どう対応すればいい？」に即答するAIアドバイザー:
- Anthropic API（Claude）を使った対話型インターフェース
- コンテキスト: 組織プロファイル、ガバナンススコア、Gap、各種ガイド知識
- 会話履歴の保存
- AI fallback: APIキーがない場合はFAQベース
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


# ── Models ───────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    """チャットメッセージ."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    role: str = "user"  # user / assistant / system
    content: str = ""
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatSession(BaseModel):
    """チャットセッション."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    user_id: str = ""
    title: str = ""
    messages: list[ChatMessage] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ChatRequest(BaseModel):
    """チャットリクエスト."""

    session_id: str = ""  # 空=新規セッション
    organization_id: str
    user_id: str = ""
    message: str


class ChatResponse(BaseModel):
    """チャットレスポンス."""

    session_id: str
    message: ChatMessage
    sources: list[str] = Field(default_factory=list)


# ── FAQ (静的回答フォールバック) ──────────────────────────────────

FAQ_DATABASE: dict[str, dict[str, str]] = {
    "リスクアセスメント": {
        "answer": (
            "リスクアセスメントの実施手順:\n\n"
            "1. **対象AIシステムの特定**: 組織内で使用している全AIシステムを洗い出します\n"
            "2. **リスク分類**: EU AI Act準拠のリスクレベル（高/限定的/最小）に分類します\n"
            "3. **影響評価**: 各システムが個人・社会・組織に与える影響を評価します\n"
            "4. **対策策定**: リスクレベルに応じた管理策を策定します\n"
            "5. **文書化**: 評価結果と対策を文書化し、エビデンスとして保管します\n\n"
            "JPGovAIの「リスクアセスメント」機能で自動分類が可能です。"
        ),
        "sources": ["METI AI事業者ガイドライン v1.1", "EU AI Act Article 9"],
    },
    "ISO 42001": {
        "answer": (
            "ISO 42001認証取得のステップ:\n\n"
            "1. **Gap分析**: 現状とISO 42001要求事項のギャップを把握（JPGovAIで自動分析）\n"
            "2. **AIMS構築**: AI管理システム（AIMS）のポリシー・プロセスを整備\n"
            "3. **文書化**: 必要文書の作成（方針書、リスクアセスメント記録等）\n"
            "4. **内部監査**: 内部監査チェックリストに基づく自己監査\n"
            "5. **マネジメントレビュー**: 経営層によるレビュー実施\n"
            "6. **認証審査**: 認証機関によるStage 1（文書審査）→ Stage 2（実地審査）\n\n"
            "JPGovAIの「認証ガイド」と「監査パッケージ」機能をご活用ください。"
        ),
        "sources": ["ISO 42001:2023", "JPGovAI認証ガイド"],
    },
    "インシデント": {
        "answer": (
            "AIインシデントの報告義務:\n\n"
            "AI推進法では以下の場合に報告が必要です:\n"
            "- 高リスクAIシステムにおける重大な障害\n"
            "- 個人の権利に重大な影響を与えるバイアス・差別の発覚\n"
            "- 安全性に関わる重大な不具合\n\n"
            "報告先: 所管官庁（AI推進法に基づく）\n"
            "報告期限: 重大インシデントは72時間以内\n\n"
            "JPGovAIの「インシデント管理」機能で報告テンプレートを生成できます。"
        ),
        "sources": ["AI推進法（想定）", "EU AI Act Article 62"],
    },
    "ベンチマーク": {
        "answer": (
            "業界ベンチマークの活用方法:\n\n"
            "JPGovAIでは匿名化された業界データを集約し、以下を提供します:\n"
            "- 業界平均スコアとの比較\n"
            "- 業界上位/下位の傾向分析\n"
            "- よくあるGapパターンと解決事例\n\n"
            "「業界ベンチマーク」ページでベンチマークデータを登録・参照できます。"
        ),
        "sources": ["JPGovAI ベンチマーク機能"],
    },
    "ポリシー": {
        "answer": (
            "AI利用ポリシーの作成ガイド:\n\n"
            "1. **AI利用方針**: 組織としてのAI活用の基本姿勢を定めます\n"
            "2. **リスク管理方針**: AIリスクの特定・評価・軽減のプロセスを規定\n"
            "3. **倫理方針**: 公平性・透明性・説明責任の原則を定義\n"
            "4. **データ管理方針**: AI学習データ・推論データの取扱いルール\n\n"
            "JPGovAIの「ポリシー生成」機能で組織に合わせたテンプレートを自動生成できます。"
        ),
        "sources": ["METI AI事業者ガイドライン v1.1", "ISO 42001 Annex B"],
    },
}


# ── システムプロンプト構築 ───────────────────────────────────────

def _build_system_prompt(context: dict[str, Any]) -> str:
    """組織コンテキストを含むシステムプロンプトを構築.

    Args:
        context: 組織情報・スコア・Gap等のコンテキスト

    Returns:
        str: システムプロンプト
    """
    org_name = context.get("organization_name", "")
    industry = context.get("industry", "")
    size = context.get("size", "")
    score = context.get("governance_score", "N/A")
    gaps = context.get("gap_summary", "")
    ai_systems_count = context.get("ai_systems_count", 0)

    return f"""あなたはJPGovAI AIアドバイザーです。日本企業のAIガバナンスを支援する専門家として回答してください。

## あなたの知識ベース
- METI AI事業者ガイドライン v1.1（経済産業省）
- ISO 42001:2023（AI管理システム国際規格）
- EU AI Act（欧州AI規制法）
- AI推進法（日本のAI推進基本法）
- 金融業向けAIガバナンスディープガイド
- ISO 42001認証取得実務ガイド

## 相談者の組織情報
- 組織名: {org_name or '未設定'}
- 業界: {industry or '未設定'}
- 規模: {size or '未設定'}
- 現在のガバナンススコア: {score}
- 管理AIシステム数: {ai_systems_count}
{f'- 主なGap: {gaps}' if gaps else ''}

## 回答方針
1. 具体的かつ実践的な回答を心がける
2. 関連する規制・ガイドラインの条項を引用する
3. JPGovAIの該当機能がある場合は案内する
4. 不確実な情報は明示する
5. 日本語で回答する（技術用語は英語可）
6. 必要に応じて具体的なテンプレートや手順を提供する
"""


# ── In-memory storage ────────────────────────────────────────────

_sessions: dict[str, ChatSession] = {}


# ── FAQ matching ─────────────────────────────────────────────────

def _find_faq_match(question: str) -> dict[str, str] | None:
    """FAQ から最も適切な回答を検索.

    Args:
        question: ユーザーの質問

    Returns:
        dict | None: マッチしたFAQエントリ or None
    """
    question_lower = question.lower()
    best_match = None
    best_score = 0

    for keyword, entry in FAQ_DATABASE.items():
        keyword_lower = keyword.lower()
        if keyword_lower in question_lower:
            score = len(keyword)
            if score > best_score:
                best_score = score
                best_match = entry

    return best_match


# ── Chat functions ───────────────────────────────────────────────

def create_session(
    organization_id: str,
    user_id: str = "",
    context: dict[str, Any] | None = None,
) -> ChatSession:
    """新規チャットセッションを作成.

    Args:
        organization_id: 組織ID
        user_id: ユーザーID
        context: 組織コンテキスト

    Returns:
        ChatSession: 作成されたセッション
    """
    session = ChatSession(
        organization_id=organization_id,
        user_id=user_id,
        title="AIアドバイザー相談",
        context=context or {},
    )
    _sessions[session.id] = session
    return session


def get_session(session_id: str) -> ChatSession | None:
    """チャットセッションを取得."""
    return _sessions.get(session_id)


def list_sessions(
    organization_id: str,
    user_id: str = "",
) -> list[ChatSession]:
    """チャットセッション一覧を取得."""
    result = [
        s for s in _sessions.values()
        if s.organization_id == organization_id
    ]
    if user_id:
        result = [s for s in result if s.user_id == user_id]
    return sorted(result, key=lambda s: s.updated_at, reverse=True)


def _call_anthropic_api(
    system_prompt: str,
    messages: list[dict[str, str]],
) -> str | None:
    """Anthropic APIを呼び出す.

    Args:
        system_prompt: システムプロンプト
        messages: 会話履歴

    Returns:
        str | None: AI応答テキスト or None (APIキーなし)
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text  # type: ignore[union-attr]
    except Exception:
        return None


def chat(request: ChatRequest) -> ChatResponse:
    """チャットメッセージを送信して応答を取得.

    Args:
        request: チャットリクエスト

    Returns:
        ChatResponse: チャットレスポンス
    """
    # セッション取得 or 新規作成
    session = None
    if request.session_id:
        session = _sessions.get(request.session_id)

    if session is None:
        session = create_session(
            organization_id=request.organization_id,
            user_id=request.user_id,
        )

    # ユーザーメッセージを追加
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=request.message,
    )
    session.messages.append(user_msg)

    # セッション初回はタイトルを設定
    if len(session.messages) == 1:
        session.title = request.message[:50]

    # AI応答を生成
    system_prompt = _build_system_prompt(session.context)
    api_messages = [
        {"role": m.role, "content": m.content}
        for m in session.messages
        if m.role in ("user", "assistant")
    ]

    response_text = _call_anthropic_api(system_prompt, api_messages)
    sources: list[str] = []

    if response_text is None:
        # Fallback: FAQベース応答
        faq = _find_faq_match(request.message)
        if faq:
            response_text = faq["answer"]
            sources = faq.get("sources", [])
        else:
            response_text = (
                "ご質問ありがとうございます。\n\n"
                "現在AIアドバイザーはオフラインモードで動作しています。"
                "以下のJPGovAI機能をご利用ください:\n\n"
                "- **自己診断**: 現在のガバナンス成熟度を評価\n"
                "- **ギャップ分析**: 改善が必要な領域を特定\n"
                "- **ポリシー生成**: 組織に合わせたポリシーテンプレートを生成\n"
                "- **ISO 42001認証ガイド**: 認証取得のステップを確認\n"
                "- **METI解釈ガイド**: 各要件の詳細な解説を参照\n\n"
                "より具体的な質問（「リスクアセスメント」「ISO 42001」"
                "「インシデント報告」等）をいただければ、"
                "関連情報をお伝えします。"
            )
            sources = ["JPGovAI FAQ"]

    # アシスタントメッセージを追加
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=response_text,
        metadata={"sources": sources},
    )
    session.messages.append(assistant_msg)
    session.updated_at = datetime.now(timezone.utc).isoformat()

    return ChatResponse(
        session_id=session.id,
        message=assistant_msg,
        sources=sources,
    )


def delete_session(session_id: str) -> bool:
    """チャットセッションを削除."""
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False


# ── テスト用リセット ────────────────────────────────────────────

def reset_advisor() -> None:
    """テスト用: ストレージをリセット."""
    _sessions.clear()
