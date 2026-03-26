# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Streamlit UI for JPGovAI - AIガバナンス診断ツール.

一般ユーザー向けに設計されたUI。初回はオンボーディングフローを表示し、
診断完了後はダッシュボードを表示する。
「ポチポチするだけで規制遵守が完了する」体験に最適化。

使い方:
    streamlit run ui/streamlit_app.py
"""

from __future__ import annotations

import asyncio
import html as _html
import sys
import os

# app/ パッケージをインポートできるようにパスを挿入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

st.set_page_config(
    page_title="AIガバナンス診断 - JPGovAI",
    page_icon="\U0001f3db\ufe0f",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── プロフェッショナルCSS ─────────────────────────────────────────
st.markdown("""
<style>
/* Vanta/Drata風のクリーンSaaSデザイン */

/* フォント */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="st-"] { font-family: 'Inter', sans-serif !important; }

/* サイドバー */
section[data-testid="stSidebar"] {
    background-color: #0f172a !important;
    border-right: 1px solid #1e293b;
}
section[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    background-color: #1e293b !important;
    border-radius: 8px;
}

/* メインコンテンツ */
.main .block-container {
    padding: 2rem 3rem !important;
    max-width: 1200px !important;
}

/* ボタン */
.stButton > button[kind="primary"] {
    background-color: #2563eb !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.5rem !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: #1d4ed8 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
}
.stButton > button[kind="secondary"], .stButton > button:not([kind]) {
    border-radius: 8px !important;
    border: 1px solid #e2e8f0 !important;
    font-weight: 500 !important;
}

/* メトリクスカード */
[data-testid="stMetric"] {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1rem;
}
[data-testid="stMetricLabel"] { font-weight: 600 !important; color: #64748b !important; }
[data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 700 !important; }

/* Expander */
.streamlit-expanderHeader {
    border-radius: 8px !important;
    font-weight: 600 !important;
}

/* プログレスバー */
.stProgress > div > div {
    background-color: #2563eb !important;
    border-radius: 999px !important;
}

/* ヘッダー */
h1 { font-weight: 800 !important; letter-spacing: -0.02em !important; }
h2 { font-weight: 700 !important; color: #0f172a !important; }
h3 { font-weight: 600 !important; }

/* タブ */
.stTabs [data-baseweb="tab-list"] { gap: 0 !important; }
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0 !important;
    font-weight: 500 !important;
}

/* ダウンロードボタン */
.stDownloadButton > button {
    border-radius: 8px !important;
    border: 1px solid #2563eb !important;
    color: #2563eb !important;
    font-weight: 600 !important;
}

/* ラジオボタン */
.stRadio > div { gap: 0.25rem !important; }

/* 成功/警告/エラーメッセージ */
.stAlert { border-radius: 8px !important; }

/* フッター非表示 */
footer { display: none !important; }
#MainMenu { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── DB初期化 ──────────────────────────────────────────────────────
from app.db.database import get_db

get_db()

# ── サービスインポート ─────────────────────────────────────────────
from app.guidelines.meti_v1_1 import ASSESSMENT_QUESTIONS, CATEGORIES, all_requirements
from app.models import AnswerItem, ComplianceStatus
from app.services.assessment import run_assessment
from app.services.ai_advisor import ChatRequest, chat
from app.services.ai_registry import (  # noqa: E402
    AISystemCreate,
    list_ai_systems,
    register_ai_system,
)
from app.services.gap_analysis import run_gap_analysis_sync  # noqa: E402, F401


# ── ユーティリティ ─────────────────────────────────────────────────

def _run_async(coro):  # noqa: ANN001, ANN202
    """asyncio コルーチンを同期的に実行するヘルパー."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ── session_state 初期化 ──────────────────────────────────────────

defaults = {
    "onboarded": False,
    "org_name": "",
    "org_industry": "",
    "org_size": "",
    "org_ai_usage": "",
    "organization_id": "org-default",
    "assessment_answers": {},
    "assessment_step": 0,
    "assessment_done": False,
    "assessment_result": None,
    "gap_result": None,
    "chat_history": [],
    "chat_session_id": "",
    "current_page": None,
    # AutoFix状態
    "autofix_results": {},
    "autofix_running": False,
    "autofix_progress": 0,
    "autofix_total": 0,
    "autofix_done": False,
    "autofix_errors": [],
    # 対応完了マーク
    "marked_complete": {},
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── カスタムCSS ──────────────────────────────────────────────────

st.markdown("""
<style>
    /* メトリクスカード */
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 12px 16px;
    }
    /* サイドバー */
    section[data-testid="stSidebar"] > div {
        padding-top: 1rem;
    }
    /* ウェルカムカード */
    .welcome-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 40px;
        color: white;
        text-align: center;
        margin-bottom: 24px;
    }
    .welcome-card h1 {
        color: white;
        font-size: 2em;
        margin-bottom: 8px;
    }
    .welcome-card p {
        color: rgba(255,255,255,0.9);
        font-size: 1.1em;
    }
    /* ステップカード */
    .step-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        height: 100%;
    }
    .step-card h3 {
        margin-top: 8px;
    }
    /* スコアゲージ */
    .score-gauge {
        text-align: center;
        padding: 20px;
    }
    .score-gauge .score-number {
        font-size: 3em;
        font-weight: bold;
        line-height: 1;
    }
    .score-gauge .score-label {
        font-size: 1.1em;
        color: #6c757d;
        margin-top: 4px;
    }
    /* ギャップカード */
    .gap-card {
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 8px;
        border-left: 4px solid;
    }
    .gap-card-red { border-left-color: #dc3545; background: #fff5f5; }
    .gap-card-yellow { border-left-color: #ffc107; background: #fffdf0; }
    .gap-card-green { border-left-color: #28a745; background: #f0fff4; }
    /* 質問ヘルプテキスト */
    .question-help {
        background: #e8f4fd;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 16px;
        font-size: 0.9em;
        color: #0c5460;
    }
    /* アクションカード */
    .action-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 12px;
    }
    /* 空状態 */
    .empty-state {
        text-align: center;
        padding: 60px 20px;
        color: #6c757d;
    }
    .empty-state h3 {
        color: #495057;
    }
    /* スコア凡例 */
    .score-legend {
        display: flex;
        justify-content: center;
        gap: 16px;
        margin-top: 8px;
        font-size: 0.85em;
        flex-wrap: wrap;
    }
    .score-legend-item {
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .score-legend-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
    }
    /* チャットウェルカム */
    .chat-welcome {
        text-align: center;
        padding: 32px 20px;
        color: #6c757d;
        border: 1px dashed #dee2e6;
        border-radius: 12px;
        margin-bottom: 16px;
    }
    /* CTA大ボタン */
    .cta-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 32px;
        text-align: center;
        margin: 24px 0;
    }
    .cta-box h2 {
        color: white;
        margin-bottom: 8px;
    }
    .cta-box p {
        color: rgba(255,255,255,0.9);
        font-size: 1.1em;
        margin-bottom: 16px;
    }
    /* 修復進捗アイテム */
    .fix-item {
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .fix-item-done {
        background: #f0fff4;
        border-left: 3px solid #28a745;
    }
    .fix-item-pending {
        background: #f8f9fa;
        border-left: 3px solid #dee2e6;
    }
    .fix-item-active {
        background: #e8f4fd;
        border-left: 3px solid #667eea;
    }
    /* 完了バナー */
    .completion-banner {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        border-radius: 16px;
        padding: 40px;
        text-align: center;
        color: white;
        margin: 24px 0;
    }
    .completion-banner h2 {
        color: white;
        font-size: 2em;
    }
    .completion-banner p {
        color: rgba(255,255,255,0.9);
        font-size: 1.1em;
    }
    /* フローステッパー */
    .flow-stepper {
        display: flex;
        justify-content: center;
        gap: 0;
        margin: 24px 0;
        flex-wrap: wrap;
    }
    .flow-step {
        padding: 8px 20px;
        font-size: 0.9em;
        border: 1px solid #e9ecef;
        background: #f8f9fa;
        color: #6c757d;
    }
    .flow-step:first-child { border-radius: 8px 0 0 8px; }
    .flow-step:last-child { border-radius: 0 8px 8px 0; }
    .flow-step-active {
        background: #667eea;
        color: white;
        border-color: #667eea;
        font-weight: bold;
    }
    .flow-step-done {
        background: #28a745;
        color: white;
        border-color: #28a745;
    }
</style>
""", unsafe_allow_html=True)


# ── ヘルパー関数 ─────────────────────────────────────────────────

def _score_color(score: float, max_score: float = 4.0) -> str:
    """スコアに応じた色を返す."""
    ratio = score / max_score if max_score > 0 else 0
    if ratio >= 0.75:
        return "#28a745"
    if ratio >= 0.5:
        return "#ffc107"
    return "#dc3545"


def _status_label(status: str) -> str:
    """ステータスの日本語ラベル."""
    labels = {
        "compliant": "OK",
        "partial": "注意",
        "non_compliant": "要対応",
        "not_assessed": "未評価",
    }
    return labels.get(status, status)


def _status_color(status: str) -> str:
    """ステータスに応じた色を返す."""
    colors = {
        "compliant": "#28a745",
        "partial": "#ffc107",
        "non_compliant": "#dc3545",
        "not_assessed": "#6c757d",
    }
    return colors.get(status, "#6c757d")


def _maturity_label(level: int) -> str:
    """成熟度レベルの分かりやすいラベル."""
    labels = {
        1: "始めたばかり",
        2: "基本ができている",
        3: "体制が整っている",
        4: "しっかり管理できている",
        5: "継続的に改善している",
    }
    return labels.get(level, f"レベル{level}")


def _score_legend_html() -> str:
    """スコアの色分けの凡例HTMLを返す."""
    return (
        '<div class="score-legend">'
        '<div class="score-legend-item"><span class="score-legend-dot" style="background:#dc3545"></span> 0〜2.0 要改善</div>'
        '<div class="score-legend-item"><span class="score-legend-dot" style="background:#ffc107"></span> 2.0〜3.0 おおむね対応</div>'
        '<div class="score-legend-item"><span class="score-legend-dot" style="background:#28a745"></span> 3.0〜4.0 十分に対応</div>'
        '</div>'
    )


def _count_action_needed(gap) -> int:  # noqa: ANN001
    """要対応+注意の件数を返す."""
    if gap is None:
        return 0
    return gap.non_compliant_count + gap.partial_count


def _count_fixed() -> int:
    """AutoFix済みの件数を返す."""
    return len(st.session_state.autofix_results)


def _count_marked_complete() -> int:
    """対応完了マーク済みの件数を返す."""
    return sum(1 for v in st.session_state.marked_complete.values() if v)


def _get_flow_stage() -> str:
    """現在のフロー段階を返す."""
    if not st.session_state.assessment_done:
        return "diagnose"
    gap = st.session_state.gap_result
    action_needed = _count_action_needed(gap)
    if action_needed == 0:
        return "complete"
    fixed = _count_fixed()
    marked = _count_marked_complete()
    if fixed + marked < action_needed:
        return "fix"
    if marked < action_needed:
        return "review"
    return "complete"


def _render_flow_stepper(active: str) -> None:
    """フローステッパーを表示."""
    steps = [
        ("diagnose", "診断"),
        ("fix", "修復"),
        ("review", "確認"),
        ("complete", "完了"),
    ]
    stage_order = [s[0] for s in steps]
    active_idx = stage_order.index(active) if active in stage_order else 0

    html_parts = []
    for i, (key, label) in enumerate(steps):
        if i < active_idx:
            cls = "flow-step flow-step-done"
            prefix = "&#10003; "
        elif i == active_idx:
            cls = "flow-step flow-step-active"
            prefix = ""
        else:
            cls = "flow-step"
            prefix = ""
        html_parts.append(f'<div class="{cls}">{prefix}{label}</div>')

    st.markdown(
        '<div class="flow-stepper">' + "".join(html_parts) + '</div>',
        unsafe_allow_html=True,
    )


# 質問のヘルプテキスト（何を聞いているかの簡単な説明）
QUESTION_HELP: dict[str, str] = {
    "Q01": "AIが出した判断を、人間がチェックする仕組みがあるかを確認します。",
    "Q02": "AIが作る文章やデータが正しいか確認する方法があるかを聞いています。",
    "Q03": "AIのリスク（危険性）をどの程度把握しているかを確認します。",
    "Q04": "AIの学習に使うデータの品質を管理しているかを聞いています。",
    "Q05": "AIに問題が起きたとき、安全に止める手順があるかを確認します。",
    "Q06": "AIが特定の人を不当に差別していないかチェックしているかを聞いています。",
    "Q07": "差別的な結果が見つかったとき、直す手順があるかを確認します。",
    "Q08": "AIで個人情報をどう扱うかのルールを決めているかを聞いています。",
    "Q09": "AIを導入する前に、プライバシーへの影響を調べているかを確認します。",
    "Q10": "AIへのサイバー攻撃に対する防御策があるかを聞いています。",
    "Q11": "セキュリティ問題が起きたときの対応体制を確認します。",
    "Q12": "AIを使っていることを関係者にきちんと伝えているかを聞いています。",
    "Q13": "AIがなぜその判断をしたか説明できるかを確認します。",
    "Q14": "AIガバナンスの責任者がいるかを聞いています。",
    "Q15": "AIを適切に管理するための方針や体制があるかを確認します。",
    "Q16": "従業員にAIに関する教育を行っているかを聞いています。",
    "Q17": "AIを使う人に、正しい使い方を伝えているかを確認します。",
    "Q18": "AIの利用が公正な競争を妨げていないかを聞いています。",
    "Q19": "AIを使って新しい価値を生み出す取り組みがあるかを確認します。",
    "Q20": "AIに関する決定や実施の記録を残しているかを聞いています。",
    "Q21": "AIをどのような用途で使っているかを確認します。リスクの高さに関わります。",
    "Q22": "AIが扱うデータの種類を確認します。個人情報を含むかが重要です。",
    "Q23": "外部のAIサービスを使うときのセキュリティ管理について聞いています。",
    "Q24": "AIシステムの仕様や性能をきちんと文書にしているかを確認します。",
    "Q25": "AIに関する契約やサービス品質の取り決めがあるかを聞いています。",
}


# ══════════════════════════════════════════════════════════════════
# オンボーディングフロー
# ══════════════════════════════════════════════════════════════════

def show_welcome() -> None:
    """ウェルカム画面を表示."""
    st.markdown("""
    <div class="welcome-card">
        <h1>AIガバナンス診断へようこそ</h1>
        <p>3ステップで、あなたの組織のAI管理状況を診断します</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="step-card">
            <div style="font-size:2em">1</div>
            <h3>組織情報を入力</h3>
            <p>業種・規模・AI利用状況を教えてください</p>
            <p style="color:#6c757d;font-size:0.9em">約30秒</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="step-card">
            <div style="font-size:2em">2</div>
            <h3>25問の診断に回答</h3>
            <p>現在のAI管理状況について答えてください</p>
            <p style="color:#6c757d;font-size:0.9em">約10分</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="step-card">
            <div style="font-size:2em">3</div>
            <h3>結果を確認</h3>
            <p>スコアと改善ポイントがすぐ分かります</p>
            <p style="color:#6c757d;font-size:0.9em">すぐ表示</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("")

    _col_l, col_center, _col_r = st.columns([1, 2, 1])
    with col_center:
        if st.button("無料で診断を始める", type="primary", use_container_width=True):
            st.session_state.current_page = "onboarding_org"
            st.rerun()


def show_onboarding_org() -> None:
    """Step 1: 組織情報入力."""
    st.markdown("### Step 1 / 3: 組織情報を入力")
    st.caption("あなたの組織について教えてください。診断結果の精度が上がります。")

    st.markdown("")

    org_name = st.text_input(
        "組織名",
        value=st.session_state.org_name,
        placeholder="例: 株式会社サンプル",
    )

    org_industry = st.selectbox(
        "業種",
        ["", "IT・通信", "金融・保険", "製造", "医療・ヘルスケア", "小売・EC", "公共・行政", "教育", "その他"],
        index=["", "IT・通信", "金融・保険", "製造", "医療・ヘルスケア", "小売・EC", "公共・行政", "教育", "その他"].index(
            st.session_state.org_industry
        ) if st.session_state.org_industry in ["", "IT・通信", "金融・保険", "製造", "医療・ヘルスケア", "小売・EC", "公共・行政", "教育", "その他"] else 0,
        help="業種によって重要な対応項目が変わります",
    )

    org_size = st.selectbox(
        "従業員数",
        ["", "small", "medium", "large", "enterprise"],
        format_func=lambda v: {
            "": "選択してください",
            "small": "50名以下",
            "medium": "50〜300名",
            "large": "300〜1,000名",
            "enterprise": "1,000名以上",
        }.get(v, v),
        index=["", "small", "medium", "large", "enterprise"].index(
            st.session_state.org_size
        ) if st.session_state.org_size in ["", "small", "medium", "large", "enterprise"] else 0,
    )

    org_ai_usage = st.selectbox(
        "AIの利用状況",
        ["", "exploring", "piloting", "production", "scaling"],
        format_func=lambda v: {
            "": "選択してください",
            "exploring": "検討・情報収集中",
            "piloting": "一部で試験的に利用中",
            "production": "本番運用している",
            "scaling": "複数部門で本格運用している",
        }.get(v, v),
        help="現在のAI活用のステージを選んでください",
    )

    st.markdown("")

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("戻る"):
            st.session_state.current_page = None
            st.rerun()
    with col_next:
        if st.button("次へ: 診断を始める", type="primary"):
            if not org_industry or not org_size:
                st.warning("業種と従業員数を選択してください。")
            else:
                st.session_state.org_name = org_name if org_name else "未設定"
                st.session_state.org_industry = org_industry
                st.session_state.org_size = org_size
                st.session_state.org_ai_usage = org_ai_usage if org_ai_usage else "exploring"
                st.session_state.current_page = "onboarding_assessment"
                st.session_state.assessment_step = 0
                st.rerun()


def show_onboarding_assessment() -> None:
    """Step 2: 25問の診断."""
    questions = ASSESSMENT_QUESTIONS
    total_q = len(questions)
    step = st.session_state.assessment_step

    st.markdown("### Step 2 / 3: 診断")

    # プログレスバー
    progress_ratio = step / total_q
    st.progress(progress_ratio)
    st.caption(f"{step} / {total_q} 問回答済み")

    if step >= total_q:
        # 全問回答済み → 結果算出
        _run_assessment_and_show_result()
        return

    q = questions[step]

    # カテゴリ表示
    cat_title = next((c.title for c in CATEGORIES if c.category_id == q.category_id), q.category_id)
    st.markdown(f"**{cat_title}**")

    # 質問テキスト
    st.markdown(f"#### Q{step + 1}. {q.text}")

    # ヘルプテキスト
    help_text = QUESTION_HELP.get(q.question_id, "")
    if help_text:
        st.markdown(f'<div class="question-help">{help_text}</div>', unsafe_allow_html=True)

    current_answer = st.session_state.assessment_answers.get(q.question_id, 0)
    selected = st.radio(
        "回答を選んでください",
        range(len(q.options)),
        format_func=lambda i, opts=q.options: opts[i],
        index=current_answer,
        key=f"q_{q.question_id}",
        label_visibility="collapsed",
    )
    st.session_state.assessment_answers[q.question_id] = selected

    # ナビゲーション
    st.markdown("")
    col_prev, col_save, col_next = st.columns([1, 1, 1])

    with col_prev:
        if step > 0:
            if st.button("前の質問へ"):
                st.session_state.assessment_step = step - 1
                st.rerun()
        else:
            if st.button("組織情報に戻る"):
                st.session_state.current_page = "onboarding_org"
                st.rerun()

    with col_save:
        st.caption("回答は自動保存されます")

    with col_next:
        if step < total_q - 1:
            if st.button("次の質問へ", type="primary"):
                st.session_state.assessment_step = step + 1
                st.rerun()
        else:
            if st.button("回答を完了する", type="primary"):
                st.session_state.assessment_step = total_q
                st.rerun()


def _run_assessment_and_show_result() -> None:
    """診断を実行して結果を表示. 完了後に自動修復への導線を表示."""
    st.markdown("### Step 3 / 3: 診断結果")

    # まだ結果がない場合は診断実行
    if st.session_state.assessment_result is None:
        with st.spinner("診断しています..."):
            try:
                questions = ASSESSMENT_QUESTIONS
                answers = []
                for q in questions:
                    idx = st.session_state.assessment_answers.get(q.question_id, 0)
                    answers.append(AnswerItem(question_id=q.question_id, selected_index=idx))

                result = run_assessment(st.session_state.organization_id, answers)
                st.session_state.assessment_result = result

                gap = run_gap_analysis_sync(result)
                st.session_state.gap_result = gap
                st.session_state.assessment_done = True
            except Exception as e:
                st.error(f"診断中にエラーが発生しました。もう一度お試しください。\n詳細: {e}")
                if st.button("やり直す"):
                    st.session_state.assessment_step = 0
                    st.session_state.assessment_result = None
                    st.rerun()
                return

    result = st.session_state.assessment_result
    gap = st.session_state.gap_result

    # スコア表示
    score = result.overall_score
    color = _score_color(score)

    st.markdown(
        f'<div class="score-gauge">'
        f'<div class="score-number" style="color:{color}">{score:.1f}</div>'
        f'<div class="score-label">/ 4.0 ({_maturity_label(result.maturity_level)})</div>'
        f'</div>'
        f'{_score_legend_html()}',
        unsafe_allow_html=True,
    )

    # 対応状況のサマリー
    if gap:
        col1, col2, col3 = st.columns(3)
        col1.metric("OK", f"{gap.compliant_count}件", help="十分に対応できている項目")
        col2.metric("注意", f"{gap.partial_count}件", help="一部対応できているが改善の余地がある項目")
        col3.metric("要対応", f"{gap.non_compliant_count}件", help="対応が必要な項目")

        # 要対応がある場合は大きな修復ボタンを表示
        action_needed = _count_action_needed(gap)
        if action_needed > 0:
            st.markdown("")
            st.markdown(
                f'<div class="cta-box">'
                f'<h2>{action_needed}項目が要対応です</h2>'
                f'<p>ワンクリックで必要な文書・チェックリスト・タスクを自動生成します</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

            _col_l, col_center, _col_r = st.columns([1, 2, 1])
            with col_center:
                if st.button(
                    "ワンクリックで全て修復する",
                    type="primary",
                    use_container_width=True,
                    key="onboarding_fix_all",
                ):
                    st.session_state.onboarded = True
                    st.session_state.current_page = "page_autofix"
                    st.rerun()

            st.markdown("")
            _col_l2, col_center2, _col_r2 = st.columns([1, 2, 1])
            with col_center2:
                if st.button("まずはダッシュボードを見る", use_container_width=True):
                    st.session_state.onboarded = True
                    st.session_state.current_page = None
                    st.rerun()
        else:
            st.markdown("")
            _col_l, col_center, _col_r = st.columns([1, 2, 1])
            with col_center:
                st.success("全ての項目に対応済みです。")
                if st.button("ダッシュボードへ", type="primary", use_container_width=True):
                    st.session_state.onboarded = True
                    st.session_state.current_page = None
                    st.rerun()
    else:
        st.markdown("")
        _col_l, col_center, _col_r = st.columns([1, 2, 1])
        with col_center:
            if st.button("ダッシュボードへ", type="primary", use_container_width=True):
                st.session_state.onboarded = True
                st.session_state.current_page = None
                st.rerun()

    # カテゴリ別スコア
    st.markdown("---")
    st.markdown("#### カテゴリ別の状況")

    for cs in result.category_scores:
        col_a, col_b = st.columns([3, 1])
        cs_color = _score_color(cs.score)
        col_a.markdown(f"**{cs.category_title}**")
        col_b.markdown(
            f"<span style='color:{cs_color};font-weight:bold'>{cs.score:.1f}</span> / 4.0",
            unsafe_allow_html=True,
        )
        st.progress(min(cs.score / 4.0, 1.0))


# ══════════════════════════════════════════════════════════════════
# メインページ（オンボーディング完了後）
# ══════════════════════════════════════════════════════════════════

def page_dashboard() -> None:
    """ダッシュボード: フロー段階に応じたCTAを表示."""
    st.header("ダッシュボード")

    assessment = st.session_state.assessment_result
    gap = st.session_state.gap_result

    if assessment is None:
        # ── 診断前
        _render_flow_stepper("diagnose")
        st.markdown("""
        <div class="empty-state">
            <h3>まだ診断していません</h3>
            <p>25問の診断に回答すると、ここにスコアと改善ポイントが表示されます。</p>
        </div>
        """, unsafe_allow_html=True)
        _col_l, col_center, _col_r = st.columns([1, 2, 1])
        with col_center:
            if st.button("診断を始める", type="primary", use_container_width=True):
                st.session_state.current_page = "page_assessment"
                st.rerun()
        return

    # ── メインスコア
    score = assessment.overall_score
    color = _score_color(score)

    st.markdown(
        f'<div class="score-gauge">'
        f'<div class="score-number" style="color:{color}">{score:.1f}</div>'
        f'<div class="score-label">/ 4.0 ({_maturity_label(assessment.maturity_level)})</div>'
        f'</div>'
        f'{_score_legend_html()}',
        unsafe_allow_html=True,
    )

    # ── 対応状況サマリー
    if gap:
        action_needed = _count_action_needed(gap)
        fixed = _count_fixed()
        marked = _count_marked_complete()

        # フロー段階を判定して表示
        stage = _get_flow_stage()
        _render_flow_stepper(stage)

        st.markdown("#### あなたの対応状況")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(
            "OK",
            f"{gap.compliant_count}件",
            help="十分に対応できている項目の数",
        )
        col2.metric(
            "注意",
            f"{gap.partial_count}件",
            help="一部対応できているが改善の余地がある項目の数",
        )
        col3.metric(
            "要対応",
            f"{gap.non_compliant_count}件",
            help="対応が必要な項目の数",
        )
        total = gap.total_requirements
        rate = (gap.compliant_count + marked) / total if total > 0 else 0
        col4.metric(
            "対応率",
            f"{min(rate, 1.0):.0%}",
            help="全項目のうち対応できている割合",
        )

        st.markdown("---")

        # ── フロー段階に応じたCTA
        if stage == "complete":
            # 全完了
            st.markdown(
                '<div class="completion-banner">'
                '<h2>おめでとうございます！</h2>'
                '<p>全要件を充足しました。定期的に再診断して状態を維持しましょう。</p>'
                '</div>',
                unsafe_allow_html=True,
            )
        elif stage == "fix" and action_needed > 0:
            # 診断後・修復前
            st.markdown(
                f'<div class="cta-box">'
                f'<h2>{action_needed}項目が要対応です</h2>'
                f'<p>ワンクリックで必要な文書・チェックリスト・タスクを自動生成します</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
            _col_l, col_center, _col_r = st.columns([1, 2, 1])
            with col_center:
                if st.button(
                    "ワンクリックで全て修復する",
                    type="primary",
                    use_container_width=True,
                    key="dashboard_fix_all",
                ):
                    st.session_state.current_page = "page_autofix"
                    st.rerun()
        elif stage == "review":
            # 修復後・確認前
            st.markdown(
                f'<div class="cta-box">'
                f'<h2>文書が生成されました</h2>'
                f'<p>{fixed}件の修復文書を確認して承認してください（{marked}/{action_needed}件承認済み）</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
            _col_l, col_center, _col_r = st.columns([1, 2, 1])
            with col_center:
                if st.button(
                    "生成された文書を確認する",
                    type="primary",
                    use_container_width=True,
                    key="dashboard_review",
                ):
                    st.session_state.current_page = "page_gaps"
                    st.rerun()

        # ── 次にやるべきこと トップ3
        if stage not in ("complete",):
            st.markdown("#### 次にやるべきこと")

            high_priority_gaps = [
                g for g in gap.gaps
                if g.status == ComplianceStatus.NON_COMPLIANT and g.priority == "high"
            ]
            if not high_priority_gaps:
                high_priority_gaps = [
                    g for g in gap.gaps
                    if g.status == ComplianceStatus.NON_COMPLIANT
                ]
            if not high_priority_gaps:
                high_priority_gaps = [
                    g for g in gap.gaps
                    if g.status == ComplianceStatus.PARTIAL
                ]

            top_actions = high_priority_gaps[:3]

            if top_actions:
                for i, g in enumerate(top_actions, 1):
                    actions_text = ""
                    if g.improvement_actions:
                        actions_text = g.improvement_actions[0]
                    st.markdown(
                        f'<div class="action-card">'
                        f'<strong>{i}. {_html.escape(g.title)}</strong><br>'
                        f'<span style="color:#6c757d">{_html.escape(actions_text)}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.success("すべての項目に対応済みです。")

            st.markdown("")
            if st.button("すべての改善項目を見る"):
                st.session_state.current_page = "page_gaps"
                st.rerun()

    # ── カテゴリ別スコア
    st.markdown("---")
    st.markdown("#### カテゴリ別の状況")

    for cs in assessment.category_scores:
        col_a, col_b = st.columns([3, 1])
        cs_color = _score_color(cs.score)
        col_a.markdown(f"**{cs.category_title}**")
        col_b.markdown(
            f"<span style='color:{cs_color};font-weight:bold'>{cs.score:.1f}</span> / 4.0",
            unsafe_allow_html=True,
        )
        st.progress(min(cs.score / 4.0, 1.0))


def page_assessment() -> None:
    """診断する: 25問の質問に回答."""
    st.header("診断する")
    st.caption("このページでは、25問の質問に回答してAIガバナンスの成熟度を診断します。")

    questions = ASSESSMENT_QUESTIONS
    total_q = len(questions)
    step = st.session_state.assessment_step

    # 既に診断済みの場合
    if st.session_state.assessment_done and st.session_state.assessment_result is not None:
        result = st.session_state.assessment_result

        st.success(
            f"診断済みです（スコア: {result.overall_score:.1f} / 4.0, "
            f"{_maturity_label(result.maturity_level)}）"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("もう一度診断する"):
                st.session_state.assessment_step = 0
                st.session_state.assessment_answers = {}
                st.session_state.assessment_done = False
                st.session_state.assessment_result = None
                st.session_state.gap_result = None
                st.session_state.autofix_results = {}
                st.session_state.autofix_done = False
                st.session_state.marked_complete = {}
                st.rerun()
        with col2:
            if st.button("結果を見る", type="primary"):
                st.session_state.current_page = "page_dashboard"
                st.rerun()

        # 前回の結果を表示
        st.markdown("---")
        st.markdown("#### 前回の診断結果")

        score = result.overall_score
        color = _score_color(score)
        st.markdown(
            f'<div class="score-gauge">'
            f'<div class="score-number" style="color:{color}">{score:.1f}</div>'
            f'<div class="score-label">/ 4.0 ({_maturity_label(result.maturity_level)})</div>'
            f'</div>'
            f'{_score_legend_html()}',
            unsafe_allow_html=True,
        )

        for cs in result.category_scores:
            col_a, col_b = st.columns([3, 1])
            cs_color = _score_color(cs.score)
            col_a.markdown(f"**{cs.category_title}**")
            col_b.markdown(
                f"<span style='color:{cs_color};font-weight:bold'>{cs.score:.1f}</span> / 4.0",
                unsafe_allow_html=True,
            )
            st.progress(min(cs.score / 4.0, 1.0))
        return

    # ── ステップバイステップ質問表示
    if step >= total_q:
        # 全問回答済み → 診断実行
        st.success("全25問の回答が完了しました。")

        if st.button("診断結果を見る", type="primary"):
            with st.spinner("診断しています..."):
                try:
                    answers = []
                    for q in questions:
                        idx = st.session_state.assessment_answers.get(q.question_id, 0)
                        answers.append(AnswerItem(question_id=q.question_id, selected_index=idx))

                    result = run_assessment(st.session_state.organization_id, answers)
                    st.session_state.assessment_result = result

                    gap = run_gap_analysis_sync(result)
                    st.session_state.gap_result = gap
                    st.session_state.assessment_done = True
                    st.rerun()
                except Exception as e:
                    st.error(
                        "診断中にエラーが発生しました。しばらく待ってからもう一度お試しください。"
                        f"\n\n技術的な詳細: {e}"
                    )

        if st.button("回答をやり直す"):
            st.session_state.assessment_step = 0
            st.session_state.assessment_answers = {}
            st.rerun()
        return

    q = questions[step]

    # プログレスバー
    st.progress(step / total_q)
    st.caption(f"{step} / {total_q} 問回答済み")

    # カテゴリ表示
    cat_title = next((c.title for c in CATEGORIES if c.category_id == q.category_id), q.category_id)
    st.markdown(f"**{cat_title}**")

    # 質問テキスト
    st.markdown(f"#### Q{step + 1}. {q.text}")

    # ヘルプテキスト
    help_text = QUESTION_HELP.get(q.question_id, "")
    if help_text:
        st.markdown(f'<div class="question-help">{help_text}</div>', unsafe_allow_html=True)

    # 回答選択
    current_answer = st.session_state.assessment_answers.get(q.question_id, 0)
    selected = st.radio(
        "回答を選んでください",
        range(len(q.options)),
        format_func=lambda i, opts=q.options: opts[i],
        index=current_answer,
        key=f"q_{q.question_id}",
        label_visibility="collapsed",
    )
    st.session_state.assessment_answers[q.question_id] = selected

    # ナビゲーション
    st.markdown("")
    col_prev, col_save, col_next = st.columns([1, 1, 1])

    with col_prev:
        if step > 0:
            if st.button("前の質問へ"):
                st.session_state.assessment_step = step - 1
                st.rerun()
        else:
            if st.button("ダッシュボードに戻る"):
                st.session_state.current_page = "page_dashboard"
                st.rerun()

    with col_save:
        st.caption("回答は自動保存されます")

    with col_next:
        if step < total_q - 1:
            if st.button("次の質問へ", type="primary"):
                st.session_state.assessment_step = step + 1
                st.rerun()
        else:
            if st.button("回答を完了する", type="primary"):
                st.session_state.assessment_step = total_q
                st.rerun()


def _get_autofix_engine():
    """AutoFixEngineのシングルトンを取得."""
    from app.services.autofix import AutoFixEngine as _Engine
    return _Engine()


def _get_org_context() -> dict[str, str]:
    """session_stateから組織コンテキストを取得."""
    return {
        "org_name": st.session_state.org_name or "貴社",
        "industry": st.session_state.org_industry or "",
        "size": st.session_state.org_size or "",
    }


def _show_autofix_result(fix_result) -> None:  # noqa: ANN001
    """AutoFix結果を表示（プレビュー・編集・承認UI付き）."""
    from app.models import DocumentStatus as _DS

    # 生成された文書
    if fix_result.generated_documents:
        st.markdown("---")
        st.markdown("**生成された文書:**")
        for doc_idx, doc in enumerate(fix_result.generated_documents):
            doc_type_label = {
                "policy": "方針書",
                "checklist": "チェックリスト",
                "template": "テンプレート",
                "procedure": "手順書",
            }.get(doc.doc_type, doc.doc_type)

            status_badge = ""
            if doc.status == _DS.APPROVED:
                status_badge = " [承認済み]"
            else:
                status_badge = " [ドラフト]"

            with st.expander(
                f"{doc_type_label}: {doc.title}{status_badge}",
                expanded=False,
            ):
                # 編集モードのキー
                edit_key = f"edit_mode_{fix_result.requirement_id}_{doc_idx}"
                text_key = f"edit_text_{fix_result.requirement_id}_{doc_idx}"

                if st.session_state.get(edit_key, False):
                    # 編集モード
                    edited = st.text_area(
                        "文書を編集",
                        value=doc.content,
                        height=400,
                        key=text_key,
                    )
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button(
                            "保存",
                            key=f"save_{fix_result.requirement_id}_{doc_idx}",
                            type="primary",
                        ):
                            doc.content = edited
                            st.session_state[edit_key] = False
                            st.rerun()
                    with col_cancel:
                        if st.button(
                            "キャンセル",
                            key=f"cancel_{fix_result.requirement_id}_{doc_idx}",
                        ):
                            st.session_state[edit_key] = False
                            st.rerun()
                else:
                    # プレビューモード
                    st.markdown(doc.content)

                    col_edit, col_approve, col_dl = st.columns(3)
                    with col_edit:
                        if doc.status != _DS.APPROVED:
                            if st.button(
                                "編集する",
                                key=f"btn_edit_{fix_result.requirement_id}_{doc_idx}",
                            ):
                                st.session_state[edit_key] = True
                                st.rerun()
                    with col_approve:
                        if doc.status != _DS.APPROVED:
                            if st.button(
                                "承認する",
                                key=f"btn_approve_{fix_result.requirement_id}_{doc_idx}",
                                type="primary",
                            ):
                                doc.status = _DS.APPROVED
                                # 全文書承認済みならresultも完了に
                                all_approved = all(
                                    d.status == _DS.APPROVED
                                    for d in fix_result.generated_documents
                                )
                                if all_approved:
                                    fix_result.status = "completed"
                                st.rerun()
                        else:
                            st.success("承認済み")
                    with col_dl:
                        st.download_button(
                            label="ダウンロード",
                            data=doc.content,
                            file_name=f"{doc.title}.md",
                            mime="text/markdown",
                            key=f"dl_{fix_result.requirement_id}_{doc.id}",
                        )

    # タスクリスト
    if fix_result.tasks:
        st.markdown("")
        st.markdown("**タスクリスト:**")
        for i, task in enumerate(fix_result.tasks, 1):
            deps = ""
            if task.depends_on:
                dep_names = [fix_result.tasks[d].title for d in task.depends_on if isinstance(d, int) and 0 <= d < len(fix_result.tasks)]
                deps = f" (前提: {', '.join(dep_names)})" if dep_names else ""
            st.markdown(
                f"{i}. **{task.title}**{deps}\n"
                f"   - 担当: {task.assignee_role} / 期限: {task.deadline_days}日以内"
            )

    # セルフチェック
    if fix_result.self_check_questions:
        st.markdown("")
        st.markdown("**対応完了のセルフチェック:**")
        for i, sc in enumerate(fix_result.self_check_questions):
            st.checkbox(
                sc.question,
                key=f"sc_{fix_result.requirement_id}_{i}",
            )


def page_autofix() -> None:
    """自動修復: 全項目をその場で一括修復."""
    st.header("自動修復")

    gap = st.session_state.gap_result
    if gap is None:
        st.warning("先に診断を完了してください。")
        if st.button("診断を始める", type="primary"):
            st.session_state.current_page = "page_assessment"
            st.rerun()
        return

    non_compliant_gaps = [
        g for g in gap.gaps if g.status != ComplianceStatus.COMPLIANT
    ]
    total_to_fix = len(non_compliant_gaps)

    if total_to_fix == 0:
        st.success("全ての項目に対応済みです。修復の必要はありません。")
        if st.button("ダッシュボードに戻る", type="primary"):
            st.session_state.current_page = "page_dashboard"
            st.rerun()
        return

    # 既に全件修復済みかチェック
    all_fixed = all(
        g.req_id in st.session_state.autofix_results
        for g in non_compliant_gaps
    )

    if all_fixed:
        # ── 修復完了表示
        st.markdown(
            f'<div class="completion-banner">'
            f'<h2>{total_to_fix}/{total_to_fix} 修復完了！</h2>'
            f'<p>全ての要対応項目に対する文書・チェックリスト・タスクを生成しました</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # 修復済みアイテムのリスト
        for g in non_compliant_gaps:
            fix_result = st.session_state.autofix_results.get(g.req_id)
            doc_count = len(fix_result.generated_documents) if fix_result else 0
            task_count = len(fix_result.tasks) if fix_result else 0
            st.markdown(
                f'<div class="fix-item fix-item-done">'
                f'&#10003; <strong>{_html.escape(g.title)}</strong>'
                f' &mdash; {doc_count}文書, {task_count}タスク生成済み'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("")

        # 一括ダウンロード
        _col_l, col_center, _col_r = st.columns([1, 2, 1])
        with col_center:
            all_docs_md = _build_all_documents_markdown()
            st.download_button(
                label="全文書をダウンロード",
                data=all_docs_md,
                file_name="governance_documents.md",
                mime="text/markdown",
                use_container_width=True,
                key="download_all_docs_autofix",
            )

        st.markdown("")
        _col_l2, col_center2, _col_r2 = st.columns([1, 2, 1])
        with col_center2:
            if st.button(
                "生成された文書を確認する",
                type="primary",
                use_container_width=True,
                key="go_to_review",
            ):
                st.session_state.current_page = "page_gaps"
                st.rerun()

        return

    # ── まだ修復していない: 修復実行
    st.markdown(f"**{total_to_fix}件**の項目を自動修復します。")
    st.caption("必要な方針書・チェックリスト・タスクリストを自動生成します。")

    # 修復対象一覧
    for g in non_compliant_gaps:
        is_done = g.req_id in st.session_state.autofix_results
        cls = "fix-item-done" if is_done else "fix-item-pending"
        prefix = "&#10003;" if is_done else "&#9744;"
        st.markdown(
            f'<div class="fix-item {cls}">'
            f'{prefix} {g.title}'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("")
    _col_l, col_center, _col_r = st.columns([1, 2, 1])
    with col_center:
        if st.button(
            "全て修復を開始する",
            type="primary",
            use_container_width=True,
            key="start_autofix",
        ):
            _execute_autofix_all(non_compliant_gaps)
            st.rerun()


def _execute_autofix_all(gaps_to_fix: list) -> None:
    """全ギャップに対してAutoFixを実行. プログレス表示付き."""
    total = len(gaps_to_fix)
    progress_bar = st.progress(0.0)
    status_text = st.empty()
    error_items: list[str] = []

    engine = _get_autofix_engine()
    org_ctx = _get_org_context()

    for i, g in enumerate(gaps_to_fix):
        if g.req_id in st.session_state.autofix_results:
            # 既に修復済み
            progress_bar.progress((i + 1) / total)
            continue

        status_text.markdown(f"**{i + 1}/{total}** 修復中: {g.title}")
        try:
            fix_result = engine.fix_requirement(g.req_id, org_ctx)
            st.session_state.autofix_results[g.req_id] = fix_result
        except Exception as e:
            error_items.append(f"{g.title}: {e}")

        progress_bar.progress((i + 1) / total)

    st.session_state.autofix_done = True
    st.session_state.autofix_errors = error_items
    progress_bar.progress(1.0)

    if error_items:
        status_text.warning(
            f"{total - len(error_items)}/{total}件の修復が完了しました。"
            f"\n{len(error_items)}件は手動対応が必要です:\n"
            + "\n".join(f"- {item}" for item in error_items)
        )
    else:
        status_text.success(f"{total}/{total} 修復完了！")


def _build_all_documents_markdown() -> str:
    """全AutoFix結果の文書をまとめたMarkdownを生成."""
    parts: list[str] = []
    parts.append("# AIガバナンス対応文書\n")
    parts.append(f"組織名: {st.session_state.org_name or '未設定'}\n")
    parts.append("---\n")

    for req_id, fix_result in st.session_state.autofix_results.items():
        parts.append(f"\n## {fix_result.requirement_title or req_id}\n")

        # 文書
        for doc in fix_result.generated_documents:
            doc_type_label = {
                "policy": "方針書",
                "checklist": "チェックリスト",
                "template": "テンプレート",
                "procedure": "手順書",
            }.get(doc.doc_type, doc.doc_type)
            parts.append(f"\n### {doc_type_label}: {doc.title}\n")
            parts.append(doc.content)
            parts.append("\n")

        # タスク
        if fix_result.tasks:
            parts.append("\n### タスクリスト\n")
            for i, task in enumerate(fix_result.tasks, 1):
                parts.append(
                    f"{i}. **{task.title}** - 担当: {task.assignee_role} / 期限: {task.deadline_days}日以内\n"
                )

        # チェックリスト
        if fix_result.checklist:
            parts.append("\n### チェックリスト\n")
            for item in fix_result.checklist:
                parts.append(f"- [ ] {item.text}\n")

        parts.append("\n---\n")

    return "\n".join(parts)


def page_gaps() -> None:
    """改善が必要な項目: ギャップ一覧と改善アクション."""
    st.header("改善が必要な項目")
    st.caption("このページでは、対応が必要な項目と具体的な改善方法を確認できます。")

    gap = st.session_state.gap_result

    if gap is None:
        st.markdown("""
        <div class="empty-state">
            <h3>まだ診断していません</h3>
            <p>診断を完了すると、改善が必要な項目がここに表示されます。</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("診断を始める", type="primary"):
            st.session_state.current_page = "page_assessment"
            st.rerun()
        return

    # サマリー
    marked = _count_marked_complete()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("OK", f"{gap.compliant_count}件", help="十分に対応できている項目")
    col2.metric("注意", f"{gap.partial_count}件", help="一部対応できているが改善の余地がある項目")
    col3.metric("要対応", f"{gap.non_compliant_count}件", help="対応が必要な項目")
    total = gap.total_requirements
    rate = (gap.compliant_count + marked) / total if total > 0 else 0
    col4.metric("対応率", f"{min(rate, 1.0):.0%}")

    st.markdown("---")

    # 全件一括AutoFixボタン + 一括ダウンロード
    non_compliant_gaps = [
        g for g in gap.gaps if g.status != ComplianceStatus.COMPLIANT
    ]

    col_fix, col_dl = st.columns(2)
    with col_fix:
        if non_compliant_gaps:
            not_yet_fixed = [g for g in non_compliant_gaps if g.req_id not in st.session_state.autofix_results]
            if not_yet_fixed:
                if st.button(
                    "全て自動修復",
                    type="primary",
                    help="要対応・注意の全項目に対して自動修復を実行します",
                    use_container_width=True,
                ):
                    st.session_state.current_page = "page_autofix"
                    st.rerun()
            else:
                st.success(f"全{len(non_compliant_gaps)}件の修復済み")

    with col_dl:
        if st.session_state.autofix_results:
            all_docs_md = _build_all_documents_markdown()
            st.download_button(
                label="全文書をダウンロード",
                data=all_docs_md,
                file_name="governance_documents.md",
                mime="text/markdown",
                use_container_width=True,
                key="download_all_docs_gaps",
            )

    st.markdown("")

    # フィルタ（デフォルトは「要対応」を最初に見せる）
    status_filter = st.selectbox(
        "表示する項目を絞り込む",
        ["要対応のみ", "注意のみ", "OKのみ", "すべて表示"],
        index=0,
        help="ステータスで項目を絞り込めます。まずは「要対応」から確認するのがおすすめです。",
    )

    # フィルタ適用
    filtered_gaps = gap.gaps
    if status_filter == "要対応のみ":
        filtered_gaps = [g for g in filtered_gaps if g.status == ComplianceStatus.NON_COMPLIANT]
    elif status_filter == "注意のみ":
        filtered_gaps = [g for g in filtered_gaps if g.status == ComplianceStatus.PARTIAL]
    elif status_filter == "OKのみ":
        filtered_gaps = [g for g in filtered_gaps if g.status == ComplianceStatus.COMPLIANT]

    if not filtered_gaps:
        st.info("この条件に該当する項目はありません。フィルターを変更してください。")
    else:
        st.caption(f"{len(filtered_gaps)}件の項目")

    # ギャップ一覧
    for g in filtered_gaps:
        status_val = g.status.value
        label = _status_label(status_val)
        color = _status_color(status_val)
        is_marked = st.session_state.marked_complete.get(g.req_id, False)

        # タイトルに対応完了マーク
        title_suffix = " [対応完了]" if is_marked else ""

        with st.expander(
            f"{'!' if status_val == 'non_compliant' else ''} "
            f"**{g.title}** [{label}]{title_suffix}",
            expanded=(g.status == ComplianceStatus.NON_COMPLIANT and not is_marked),
        ):
            # ステータスバッジ
            st.markdown(
                f"<span style='background-color:{color};color:white;padding:2px 8px;"
                f"border-radius:4px;font-size:0.85em'>{_html.escape(label)}</span>"
                f" スコア: **{g.current_score:.1f}** / 4.0",
                unsafe_allow_html=True,
            )

            # 問題の説明
            if g.gap_description:
                st.markdown("")
                st.markdown("**何が問題か:**")
                st.markdown(f"> {g.gap_description}")

            # 改善アクション
            if g.improvement_actions:
                st.markdown("")
                st.markdown("**どうすれば改善できるか:**")
                for i, action in enumerate(g.improvement_actions, 1):
                    st.markdown(f"{i}. {action}")

            # 関連する証拠書類
            req = next((r for r in all_requirements() if r.req_id == g.req_id), None)
            if req:
                st.markdown("")
                st.markdown("**必要な証拠書類の例:**")
                st.caption("ポリシー文書、テスト結果、監査ログ、研修記録など")

            # AutoFixボタンと結果表示
            if g.status != ComplianceStatus.COMPLIANT:
                st.markdown("")
                fix_key = g.req_id

                if fix_key in st.session_state.autofix_results:
                    # 既にAutoFix実行済み
                    st.success("自動修復済み")
                    _show_autofix_result(st.session_state.autofix_results[fix_key])
                else:
                    # AutoFixボタン
                    if st.button(
                        "自動修復",
                        key=f"autofix_{g.req_id}",
                        help="この項目に必要な文書・チェックリスト・タスクを自動生成します",
                    ):
                        with st.spinner("自動修復を実行中..."):
                            engine = _get_autofix_engine()
                            org_ctx = _get_org_context()
                            fix_result = engine.fix_requirement(g.req_id, org_ctx)
                            st.session_state.autofix_results[fix_key] = fix_result
                            st.rerun()

                # 「対応完了にする」ボタン
                st.markdown("---")
                if is_marked:
                    st.markdown("**&#10003; 対応完了としてマーク済み**")
                    if st.button("対応完了を取り消す", key=f"unmark_{g.req_id}"):
                        st.session_state.marked_complete[g.req_id] = False
                        st.rerun()
                else:
                    if st.button(
                        "対応完了にする",
                        key=f"mark_{g.req_id}",
                        type="primary",
                        help="この項目の対応が完了したらクリックしてください。ダッシュボードのスコアに反映されます。",
                    ):
                        st.session_state.marked_complete[g.req_id] = True
                        st.rerun()

    # AI改善提案
    if gap.ai_recommendations:
        st.markdown("---")
        st.markdown("#### AIからの改善提案")
        st.markdown(gap.ai_recommendations)


def page_chat() -> None:
    """AIに質問する: チャットUI."""
    st.header("AIに質問する")
    st.caption("このページでは、AIガバナンスに関する質問にAIが回答します。")

    # API キーの確認
    has_api_key = bool(os.environ.get("ANTHROPIC_API_KEY"))

    if not has_api_key:
        st.info(
            "AI による詳しい回答を有効にするには、管理者が ANTHROPIC_API_KEY を設定する必要があります。\n\n"
            "現在は、あらかじめ用意された回答をもとにお答えします。"
        )

    # チャット履歴が空のときはウェルカムメッセージ
    if not st.session_state.chat_history:
        st.markdown(
            '<div class="chat-welcome">'
            '<h3>AIガバナンスについて何でもお聞きください</h3>'
            '<p>診断結果の読み方、改善の進め方、法規制の概要など、<br>AIガバナンスに関する疑問にお答えします。</p>'
            '</div>',
            unsafe_allow_html=True,
        )

    # サジェストボタン
    st.markdown("**よくある質問:**")
    suggest_col1, suggest_col2, suggest_col3 = st.columns(3)

    suggested_question = None
    with suggest_col1:
        if st.button("リスク評価のやり方は？", use_container_width=True):
            suggested_question = "リスクアセスメントのやり方を教えてください"
    with suggest_col2:
        if st.button("ISO 42001認証を取るには？", use_container_width=True):
            suggested_question = "ISO 42001認証を取得するにはどうすればよいですか？"
    with suggest_col3:
        if st.button("最初に何をすべき？", use_container_width=True):
            suggested_question = "AIガバナンスに取り組む際、最初に何をすべきですか？"

    st.markdown("---")

    # チャット履歴表示
    for msg in st.session_state.chat_history:
        role = msg["role"]
        with st.chat_message(role):
            st.markdown(msg["content"])

    # サジェストからの質問またはユーザー入力
    prompt = suggested_question
    if prompt is None:
        prompt = st.chat_input("質問を入力してください...")

    if prompt:
        # ユーザーメッセージ追加
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI応答
        with st.chat_message("assistant"):
            with st.spinner("回答を作成中..."):
                try:
                    request = ChatRequest(
                        session_id=st.session_state.chat_session_id,
                        organization_id=st.session_state.organization_id,
                        message=prompt,
                    )
                    response = chat(request)
                    st.session_state.chat_session_id = response.session_id
                    answer = response.message.content
                    st.markdown(answer)
                    st.session_state.chat_history.append({"role": "assistant", "content": answer})

                    if response.sources:
                        st.caption(f"参照: {', '.join(response.sources)}")
                except Exception:
                    error_msg = "回答の生成中にエラーが発生しました。もう一度お試しください。"
                    st.error(error_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

        # チャット履歴の上限チェック（メモリリーク防止）
        if len(st.session_state.chat_history) > 100:
            st.session_state.chat_history = st.session_state.chat_history[-100:]

    # クリアボタン（サイドバーに配置して誤操作を防止）
    if st.session_state.chat_history:
        st.markdown("")
        _clr_l, _clr_m, clr_r = st.columns([2, 2, 1])
        with clr_r:
            if st.button("会話をクリア", help="これまでの会話をすべて削除します"):
                st.session_state.chat_history = []
                st.session_state.chat_session_id = ""
                st.rerun()


def page_settings() -> None:
    """設定: 組織情報変更とAIシステム台帳."""
    st.header("設定")
    st.caption("このページでは、組織情報の変更やAIシステムの管理ができます。")

    # ── 組織情報
    st.subheader("組織情報")

    with st.form("org_settings"):
        name = st.text_input("組織名", value=st.session_state.org_name)
        industry = st.selectbox(
            "業種",
            ["IT・通信", "金融・保険", "製造", "医療・ヘルスケア", "小売・EC", "公共・行政", "教育", "その他"],
            index=["IT・通信", "金融・保険", "製造", "医療・ヘルスケア", "小売・EC", "公共・行政", "教育", "その他"].index(
                st.session_state.org_industry
            ) if st.session_state.org_industry in ["IT・通信", "金融・保険", "製造", "医療・ヘルスケア", "小売・EC", "公共・行政", "教育", "その他"] else 0,
        )
        size = st.selectbox(
            "従業員数",
            ["small", "medium", "large", "enterprise"],
            format_func=lambda v: {
                "small": "50名以下",
                "medium": "50〜300名",
                "large": "300〜1,000名",
                "enterprise": "1,000名以上",
            }.get(v, v),
            index=["small", "medium", "large", "enterprise"].index(st.session_state.org_size)
            if st.session_state.org_size in ["small", "medium", "large", "enterprise"] else 1,
        )

        ai_usage_options = ["exploring", "piloting", "production", "scaling"]
        ai_usage = st.selectbox(
            "AIの利用状況",
            ai_usage_options,
            format_func=lambda v: {
                "exploring": "検討・情報収集中",
                "piloting": "一部で試験的に利用中",
                "production": "本番運用している",
                "scaling": "複数部門で本格運用している",
            }.get(v, v),
            index=ai_usage_options.index(st.session_state.org_ai_usage)
            if st.session_state.org_ai_usage in ai_usage_options else 0,
        )

        submitted = st.form_submit_button("保存", type="primary")
        if submitted:
            st.session_state.org_name = name
            st.session_state.org_industry = industry
            st.session_state.org_size = size
            st.session_state.org_ai_usage = ai_usage
            st.success("組織情報を保存しました。")

    st.markdown("---")

    # ── AIシステム台帳（簡易版）
    st.subheader("AIシステム台帳")
    st.caption("組織で利用しているAIシステムを登録・管理できます。")

    org_id = st.session_state.organization_id

    # 新規登録
    with st.expander("AIシステムを追加", expanded=False):
        with st.form("register_ai_system"):
            sys_name = st.text_input("システム名", placeholder="例: 社内チャットボット")

            risk_display = st.selectbox(
                "リスクの高さ",
                ["minimal", "limited", "high"],
                format_func=lambda v: {
                    "minimal": "低い（社内利用のみ等）",
                    "limited": "中程度（顧客対応等）",
                    "high": "高い（自動判定・個人情報処理等）",
                }.get(v, v),
                help="AIシステムが扱うデータや判断の重要度で選んでください",
            )

            sys_submitted = st.form_submit_button("登録", type="primary")
            if sys_submitted and not sys_name:
                st.warning("システム名を入力してください。")
            if sys_submitted and sys_name:
                try:
                    from app.services.ai_registry import AISystemRiskLevel
                    system = register_ai_system(AISystemCreate(
                        organization_id=org_id,
                        name=sys_name,
                        risk_level=AISystemRiskLevel(risk_display),
                    ))
                    st.success(f"「{system.name}」を登録しました。")
                except Exception as e:
                    st.error(f"登録中にエラーが発生しました: {e}")

    # システム一覧
    try:
        systems = list_ai_systems(org_id)
        if systems:
            st.markdown("")
            for s in systems:
                risk_label = {
                    "high": "高リスク",
                    "limited": "中リスク",
                    "minimal": "低リスク",
                }.get(s.risk_level.value, s.risk_level.value)

                risk_color = {
                    "high": "#dc3545",
                    "limited": "#ffc107",
                    "minimal": "#28a745",
                }.get(s.risk_level.value, "#6c757d")

                st.markdown(
                    f"**{_html.escape(s.name)}** "
                    f"<span style='background-color:{risk_color};color:white;padding:2px 8px;"
                    f"border-radius:4px;font-size:0.8em'>{_html.escape(risk_label)}</span>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("登録されたAIシステムはありません。")
    except Exception as e:
        st.warning(f"一覧の取得中にエラーが発生しました: {e}")

    st.markdown("---")

    # ── データ管理
    st.subheader("データ管理")
    st.caption("リセットすると、該当データが完全に削除されます。この操作は取り消せません。")

    col1, col2 = st.columns(2)
    with col1:
        # 初期化: 確認状態
        if "confirm_reset_assessment" not in st.session_state:
            st.session_state.confirm_reset_assessment = False
        if "confirm_reset_chat" not in st.session_state:
            st.session_state.confirm_reset_chat = False

        if not st.session_state.confirm_reset_assessment:
            if st.button("診断データをリセット"):
                st.session_state.confirm_reset_assessment = True
                st.rerun()
        else:
            st.warning("診断データを本当にリセットしますか？回答内容と診断結果がすべて削除されます。")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("リセットする", type="primary", key="confirm_reset_assess_yes"):
                    st.session_state.assessment_result = None
                    st.session_state.gap_result = None
                    st.session_state.assessment_answers = {}
                    st.session_state.assessment_step = 0
                    st.session_state.assessment_done = False
                    st.session_state.autofix_results = {}
                    st.session_state.autofix_done = False
                    st.session_state.marked_complete = {}
                    st.session_state.confirm_reset_assessment = False
                    st.success("診断データをリセットしました。")
            with c2:
                if st.button("キャンセル", key="confirm_reset_assess_no"):
                    st.session_state.confirm_reset_assessment = False
                    st.rerun()

    with col2:
        if not st.session_state.get("confirm_reset_chat", False):
            if st.button("会話履歴をリセット"):
                st.session_state.confirm_reset_chat = True
                st.rerun()
        else:
            st.warning("会話履歴を本当にリセットしますか？")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("リセットする", type="primary", key="confirm_reset_chat_yes"):
                    st.session_state.chat_history = []
                    st.session_state.chat_session_id = ""
                    st.session_state.confirm_reset_chat = False
                    st.success("会話履歴をリセットしました。")
            with c2:
                if st.button("キャンセル", key="confirm_reset_chat_no"):
                    st.session_state.confirm_reset_chat = False
                    st.rerun()


# ══════════════════════════════════════════════════════════════════
# ルーティング
# ══════════════════════════════════════════════════════════════════

# オンボーディング未完了 → オンボーディングフローを表示
if not st.session_state.onboarded and not st.session_state.assessment_done:
    current = st.session_state.current_page

    if current == "onboarding_org":
        show_onboarding_org()
    elif current == "onboarding_assessment":
        show_onboarding_assessment()
    else:
        show_welcome()
else:
    # オンボーディング完了後のメイン画面
    st.session_state.onboarded = True

    # サイドバー
    st.sidebar.title("AIガバナンス診断")
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "メニュー",
        [
            "ダッシュボード",
            "診断する",
            "自動修復",
            "改善が必要な項目",
            "AIに質問する",
            "設定",
        ],
        label_visibility="collapsed",
    )

    st.sidebar.markdown("---")
    org_display = st.session_state.org_name if st.session_state.org_name else "未設定"
    st.sidebar.caption(f"組織: {org_display}")

    # ページ遷移（ボタンからの直接遷移をサポート）
    override_page = st.session_state.current_page
    if override_page in ("page_dashboard", "page_assessment", "page_gaps", "page_chat", "page_settings", "page_autofix"):
        page_map = {
            "page_dashboard": "ダッシュボード",
            "page_assessment": "診断する",
            "page_autofix": "自動修復",
            "page_gaps": "改善が必要な項目",
            "page_chat": "AIに質問する",
            "page_settings": "設定",
        }
        page = page_map.get(override_page, page)
        st.session_state.current_page = None

    PAGE_MAP = {
        "ダッシュボード": page_dashboard,
        "診断する": page_assessment,
        "自動修復": page_autofix,
        "改善が必要な項目": page_gaps,
        "AIに質問する": page_chat,
        "設定": page_settings,
    }

    page_fn = PAGE_MAP.get(page, page_dashboard)
    page_fn()
