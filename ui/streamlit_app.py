# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Streamlit UI for JPGovAI - AI Governance統合管理プラットフォーム.

スタンドアロン版: FastAPIバックエンドを使わず、app/services/のPython関数を直接呼び出す。
Streamlit Cloudで動作可能。

使い方:
    streamlit run ui/streamlit_app.py
"""

from __future__ import annotations

import asyncio
import sys
import os

# app/ パッケージをインポートできるようにパスを挿入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

st.set_page_config(
    page_title="JPGovAI - AI Governance統合管理",
    page_icon="\U0001f3db\ufe0f",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── DB初期化 ──────────────────────────────────────────────────────
from app.db.database import get_db

get_db()

# ── サービスインポート ─────────────────────────────────────────────
from app.guidelines.meti_v1_1 import ASSESSMENT_QUESTIONS, CATEGORIES, all_requirements
from app.models import AnswerItem, ComplianceStatus, EvidenceUpload
from app.services.assessment import run_assessment
from app.services.ai_advisor import ChatRequest, chat
from app.services.ai_registry import (
    AISystemCreate,
    AISystemType,
    get_registry_dashboard,
    list_ai_systems,
    register_ai_system,
)
from app.services.dashboard import build_multi_regulation_dashboard
from app.services.evidence import get_evidence_summary, list_evidence, upload_evidence
from app.services.gap_analysis import run_gap_analysis
from app.services.iso_check import run_iso_check
from app.services.report_gen import generate_report


# ── ユーティリティ ─────────────────────────────────────────────────

def _run_async(coro):
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


def _init_session_state():
    """session_stateの初期化."""
    defaults = {
        "organization_id": "org-default",
        "organization_name": "デモ組織",
        "organization_industry": "IT・通信",
        "organization_size": "medium",
        "assessment_result": None,
        "gap_result": None,
        "iso_result": None,
        "chat_session_id": "",
        "chat_messages": [],
        "assessment_answers": {},
        "assessment_step": 0,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


_init_session_state()


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
    /* テーブルスタイル */
    .stDataFrame {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ── サイドバー ────────────────────────────────────────────────────

st.sidebar.title("JPGovAI")
st.sidebar.caption("AI Governance統合管理")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "ナビゲーション",
    [
        "\U0001f4ca ダッシュボード",
        "\U0001f4cb 診断 (Self-Assessment)",
        "\U0001f50d ギャップ分析",
        "\U0001f916 AIシステム台帳",
        "\U0001f4c2 エビデンス管理",
        "\U0001f4c4 レポート",
        "\U0001f4ac AIアドバイザー",
        "\u2699\ufe0f 設定",
    ],
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
st.sidebar.caption(f"組織: {st.session_state.organization_name}")


# ══════════════════════════════════════════════════════════════════
# ページ関数
# ══════════════════════════════════════════════════════════════════


def _status_color(status: str) -> str:
    """ステータスに応じた色を返す."""
    colors = {
        "compliant": "#28a745",
        "partial": "#ffc107",
        "non_compliant": "#dc3545",
        "not_assessed": "#6c757d",
    }
    return colors.get(status, "#6c757d")


def _status_label_ja(status: str) -> str:
    """ステータスの日本語ラベル."""
    labels = {
        "compliant": "充足",
        "partial": "部分充足",
        "non_compliant": "未充足",
        "not_assessed": "未評価",
    }
    return labels.get(status, status)


def _maturity_label(level: int) -> str:
    """成熟度レベルのラベル."""
    labels = {
        1: "Lv.1 初期",
        2: "Lv.2 反復可能",
        3: "Lv.3 定義済み",
        4: "Lv.4 管理",
        5: "Lv.5 最適化",
    }
    return labels.get(level, f"Lv.{level}")


# ── 1. ダッシュボード ──────────────────────────────────────────────

def page_dashboard():
    st.header("ダッシュボード")

    assessment = st.session_state.assessment_result
    gap = st.session_state.gap_result

    if assessment is None:
        st.info("診断がまだ実行されていません。サイドバーから「診断」を実行してください。")
        # デモ用のプレースホルダ
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("成熟度スコア", "---", help="診断実行後に表示されます")
        col2.metric("全体スコア", "---")
        col3.metric("要件数", "---")
        col4.metric("充足率", "---")
        return

    # ── メインメトリクス
    col1, col2, col3, col4 = st.columns(4)

    maturity = assessment.maturity_level
    col1.metric(
        "成熟度レベル",
        _maturity_label(maturity),
        help="1(初期)〜5(最適化)の5段階",
    )
    col2.metric(
        "全体スコア",
        f"{assessment.overall_score:.2f} / 4.00",
    )

    if gap:
        total = gap.total_requirements
        compliant = gap.compliant_count
        rate = compliant / total if total > 0 else 0
        col3.metric("要件充足", f"{compliant}/{total}")
        col4.metric("充足率", f"{rate:.0%}")
    else:
        col3.metric("要件充足", "---")
        col4.metric("充足率", "---")

    st.markdown("---")

    # ── 成熟度ゲージ（プログレスバー）
    st.subheader("成熟度スコア")
    score_pct = assessment.overall_score / 4.0
    st.progress(min(score_pct, 1.0))
    st.caption(f"スコア {assessment.overall_score:.2f} / 4.00 ({_maturity_label(maturity)})")

    st.markdown("---")

    # ── 3規制準拠サマリー
    st.subheader("規制準拠状況")

    if gap:
        try:
            iso_result = st.session_state.iso_result
            if iso_result is None:
                iso_result = run_iso_check(gap)
                st.session_state.iso_result = iso_result

            dashboard = build_multi_regulation_dashboard(
                st.session_state.organization_id,
                gap,
                iso_result,
            )

            reg_cols = st.columns(3)
            regulations = [
                ("METI AI事業者ガイドライン", dashboard.meti_status),
                ("ISO 42001", dashboard.iso_status),
                ("AI推進法", dashboard.act_status),
            ]
            for col, (name, status) in zip(reg_cols, regulations):
                with col:
                    if status:
                        rate = status.compliance_rate
                        color = "#28a745" if rate >= 0.7 else "#ffc107" if rate >= 0.4 else "#dc3545"
                        st.markdown(f"**{name}**")
                        st.progress(min(rate, 1.0))
                        st.markdown(
                            f"<span style='color:{color};font-size:1.2em;font-weight:bold'>"
                            f"{rate:.0%}</span> "
                            f"({status.compliant_count}/{status.total_requirements}件 充足)",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(f"**{name}**")
                        st.caption("データなし")

        except Exception as e:
            st.warning(f"規制ダッシュボードの生成中にエラー: {e}")

    st.markdown("---")

    # ── カテゴリ別スコア
    st.subheader("カテゴリ別スコア")
    for cs in assessment.category_scores:
        col_a, col_b = st.columns([3, 1])
        col_a.markdown(f"**{cs.category_id}: {cs.category_title}**")
        col_b.markdown(f"{cs.score:.2f} / 4.00 ({_maturity_label(cs.maturity_level)})")
        st.progress(min(cs.score / 4.0, 1.0))


# ── 2. 診断 ────────────────────────────────────────────────────────

def page_assessment():
    st.header("自己診断 (Self-Assessment)")
    st.caption("25問のアンケートに回答し、AI Governance成熟度を評価します")

    questions = ASSESSMENT_QUESTIONS
    total_q = len(questions)
    step = st.session_state.assessment_step

    if step >= total_q:
        # 全問回答済み → 結果表示/診断実行
        st.success("全25問の回答が完了しました!")

        if st.button("診断を実行", type="primary"):
            answers = []
            for q in questions:
                idx = st.session_state.assessment_answers.get(q.question_id, 0)
                answers.append(AnswerItem(question_id=q.question_id, selected_index=idx))

            try:
                result = run_assessment(st.session_state.organization_id, answers)
                st.session_state.assessment_result = result

                # ギャップ分析も自動実行
                gap = _run_async(run_gap_analysis(result))
                st.session_state.gap_result = gap
                st.session_state.iso_result = None  # リセット

                st.success(f"診断完了! 成熟度: {_maturity_label(result.maturity_level)} (スコア: {result.overall_score:.2f})")
                st.balloons()
            except Exception as e:
                st.error(f"診断実行エラー: {e}")

        if st.button("回答をやり直す"):
            st.session_state.assessment_step = 0
            st.session_state.assessment_answers = {}
            st.rerun()

        # 現在の回答サマリー
        if st.session_state.assessment_result:
            result = st.session_state.assessment_result
            st.markdown("---")
            st.subheader("診断結果")
            col1, col2 = st.columns(2)
            col1.metric("成熟度レベル", _maturity_label(result.maturity_level))
            col2.metric("全体スコア", f"{result.overall_score:.2f} / 4.00")

            for cs in result.category_scores:
                st.markdown(f"**{cs.category_id}: {cs.category_title}** — {cs.score:.2f} / 4.00")
                st.progress(min(cs.score / 4.0, 1.0))
        return

    # ── ステップバイステップ質問表示
    q = questions[step]

    # プログレスバー
    st.progress(step / total_q)
    st.caption(f"質問 {step + 1} / {total_q}")

    # カテゴリ表示
    cat_title = next((c.title for c in CATEGORIES if c.category_id == q.category_id), q.category_id)
    st.markdown(f"**カテゴリ: {cat_title}**")

    st.markdown(f"### Q{step + 1}. {q.text}")

    # 回答選択
    current_answer = st.session_state.assessment_answers.get(q.question_id, 0)
    selected = st.radio(
        "回答を選択してください",
        range(len(q.options)),
        format_func=lambda i: q.options[i],
        index=current_answer,
        key=f"q_{q.question_id}",
        label_visibility="collapsed",
    )
    st.session_state.assessment_answers[q.question_id] = selected

    # ナビゲーションボタン
    col_prev, col_next = st.columns(2)
    with col_prev:
        if step > 0:
            if st.button("\u2190 前の質問"):
                st.session_state.assessment_step = step - 1
                st.rerun()
    with col_next:
        if step < total_q - 1:
            if st.button("次の質問 \u2192", type="primary"):
                st.session_state.assessment_step = step + 1
                st.rerun()
        else:
            if st.button("回答を完了する", type="primary"):
                st.session_state.assessment_step = total_q
                st.rerun()


# ── 3. ギャップ分析 ──────────────────────────────────────────────

def page_gap_analysis():
    st.header("ギャップ分析")

    gap = st.session_state.gap_result

    if gap is None:
        st.info("先に「診断」を実行してください。診断結果を元にギャップ分析を行います。")
        return

    # ── サマリー
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("充足", gap.compliant_count, help="要件を満たしている")
    col2.metric("部分充足", gap.partial_count, help="一部対応済み")
    col3.metric("未充足", gap.non_compliant_count, help="対応が必要")
    col4.metric(
        "充足率",
        f"{gap.compliant_count / gap.total_requirements:.0%}" if gap.total_requirements > 0 else "---",
    )

    st.markdown("---")

    # ── フィルタ
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        status_filter = st.selectbox(
            "ステータスで絞り込み",
            ["すべて", "未充足", "部分充足", "充足"],
        )
    with filter_col2:
        cat_options = ["すべて"] + [f"{c.category_id}: {c.title}" for c in CATEGORIES]
        cat_filter = st.selectbox("カテゴリで絞り込み", cat_options)

    # フィルタ適用
    filtered_gaps = gap.gaps
    if status_filter == "未充足":
        filtered_gaps = [g for g in filtered_gaps if g.status == ComplianceStatus.NON_COMPLIANT]
    elif status_filter == "部分充足":
        filtered_gaps = [g for g in filtered_gaps if g.status == ComplianceStatus.PARTIAL]
    elif status_filter == "充足":
        filtered_gaps = [g for g in filtered_gaps if g.status == ComplianceStatus.COMPLIANT]

    if cat_filter != "すべて":
        cat_id = cat_filter.split(":")[0].strip()
        filtered_gaps = [g for g in filtered_gaps if g.category_id == cat_id]

    # ── ギャップ一覧
    st.subheader(f"要件一覧 ({len(filtered_gaps)}件)")

    for g in filtered_gaps:
        color = _status_color(g.status.value)
        label = _status_label_ja(g.status.value)
        priority_icon = {"high": "\U0001f534", "medium": "\U0001f7e1", "low": "\U0001f7e2"}.get(g.priority, "")

        with st.expander(
            f"{priority_icon} **{g.req_id}** {g.title} — "
            f":{label}  (スコア: {g.current_score:.2f})",
            expanded=(g.status == ComplianceStatus.NON_COMPLIANT),
        ):
            st.markdown(
                f"<span style='background-color:{color};color:white;padding:2px 8px;"
                f"border-radius:4px;font-size:0.85em'>{label}</span>"
                f" 優先度: **{g.priority}** | スコア: **{g.current_score:.2f}** / 4.00",
                unsafe_allow_html=True,
            )
            if g.gap_description:
                st.markdown(f"> {g.gap_description}")
            if g.improvement_actions:
                st.markdown("**改善アクション:**")
                for action in g.improvement_actions:
                    st.markdown(f"- {action}")

    # ── AI改善提案
    if gap.ai_recommendations:
        st.markdown("---")
        st.subheader("AI改善提案")
        st.markdown(gap.ai_recommendations)


# ── 4. AIシステム台帳 ──────────────────────────────────────────────

def page_ai_registry():
    st.header("AIシステム台帳")

    org_id = st.session_state.organization_id

    # ── 新規登録フォーム
    with st.expander("新規AIシステム登録", expanded=False):
        with st.form("register_ai_system"):
            name = st.text_input("システム名*", placeholder="例: 社内チャットボット")
            description = st.text_area("説明", placeholder="システムの概要を記載")
            col1, col2 = st.columns(2)
            with col1:
                ai_type = st.selectbox(
                    "種別",
                    [t.value for t in AISystemType],
                    format_func=lambda v: {
                        "generative": "生成AI",
                        "predictive": "予測",
                        "classification": "分類",
                        "recommendation": "推薦",
                        "other": "その他",
                    }.get(v, v),
                )
                department = st.text_input("所管部門", placeholder="例: 情報システム部")
                vendor = st.text_input("ベンダー", placeholder="例: OpenAI")
            with col2:
                owner = st.text_input("責任者", placeholder="例: 田中太郎")
                purpose = st.text_input("利用目的", placeholder="例: 社内問い合わせ対応")
                data_types = st.multiselect(
                    "取扱データ",
                    ["personal", "confidential", "public"],
                    format_func=lambda v: {"personal": "個人データ", "confidential": "機密", "public": "公開"}.get(v, v),
                )

            submitted = st.form_submit_button("登録", type="primary")
            if submitted and name:
                try:
                    system = register_ai_system(AISystemCreate(
                        organization_id=org_id,
                        name=name,
                        description=description,
                        ai_type=AISystemType(ai_type),
                        department=department,
                        vendor=vendor,
                        owner=owner,
                        purpose=purpose,
                        data_types=data_types,
                    ))
                    st.success(f"登録完了: {system.name} (リスクレベル: {system.risk_level.value})")
                except Exception as e:
                    st.error(f"登録エラー: {e}")

    st.markdown("---")

    # ── システム一覧
    systems = list_ai_systems(org_id)

    if not systems:
        st.info("登録されたAIシステムはありません。上のフォームから登録してください。")
        return

    # ダッシュボード
    dash = get_registry_dashboard(org_id)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("登録システム数", dash.total_systems)
    col2.metric("高リスク", dash.by_risk_level.get("high", 0))
    col3.metric("Shadow AI", dash.shadow_ai_count)
    col4.metric("平均ガバナンススコア", f"{dash.avg_governance_score:.0%}")

    st.markdown("---")

    # リスク分布
    if dash.by_risk_level:
        st.subheader("リスク分布")
        risk_data = {
            "リスクレベル": list(dash.by_risk_level.keys()),
            "件数": list(dash.by_risk_level.values()),
        }
        st.bar_chart(risk_data, x="リスクレベル", y="件数")

    # システムテーブル
    st.subheader("システム一覧")
    table_data = []
    for s in systems:
        table_data.append({
            "名前": s.name,
            "種別": s.ai_type.value,
            "リスク": s.risk_level.value,
            "部門": s.department,
            "責任者": s.owner,
            "ステータス": s.status.value,
            "ガバナンス": f"{s.governance_score:.0%}",
        })
    st.dataframe(table_data, use_container_width=True)


# ── 5. エビデンス管理 ──────────────────────────────────────────────

def page_evidence():
    st.header("エビデンス管理")

    org_id = st.session_state.organization_id

    # カバレッジサマリー
    try:
        summary = get_evidence_summary(org_id)
        col1, col2, col3 = st.columns(3)
        col1.metric("カバレッジ率", f"{summary.coverage_rate:.0%}")
        col2.metric("エビデンス有り", f"{summary.requirements_with_evidence}件")
        col3.metric("全要件数", f"{summary.total_requirements}件")

        st.progress(min(summary.coverage_rate, 1.0))

        # カテゴリ別カバレッジ
        if summary.by_category:
            st.subheader("カテゴリ別カバレッジ")
            for cat_id, info in summary.by_category.items():
                title = info.get("title", cat_id)
                covered = info.get("covered", 0)
                total = info.get("total", 0)
                rate = info.get("rate", 0)
                color = "#28a745" if rate >= 0.7 else "#ffc107" if rate >= 0.3 else "#dc3545"
                st.markdown(
                    f"**{cat_id}: {title}** — "
                    f"<span style='color:{color}'>{covered}/{total} ({rate:.0%})</span>",
                    unsafe_allow_html=True,
                )
                st.progress(min(rate, 1.0))
    except Exception as e:
        st.warning(f"サマリー取得エラー: {e}")

    st.markdown("---")

    # エビデンスアップロード
    st.subheader("エビデンス登録")
    reqs = all_requirements()
    req_options = {f"{r.req_id}: {r.title}": r.req_id for r in reqs}

    with st.form("upload_evidence"):
        selected_req = st.selectbox("対象要件", list(req_options.keys()))
        filename = st.text_input("ファイル名", placeholder="例: ai_policy_v1.pdf")
        description = st.text_area("説明", placeholder="エビデンスの説明")
        file_type = st.selectbox("種別", ["policy", "test_result", "audit_log", "training_record", "other"],
            format_func=lambda v: {
                "policy": "ポリシー文書",
                "test_result": "テスト結果",
                "audit_log": "監査ログ",
                "training_record": "研修記録",
                "other": "その他",
            }.get(v, v),
        )

        submitted = st.form_submit_button("登録", type="primary")
        if submitted and filename and selected_req:
            try:
                req_id = req_options[selected_req]
                record = upload_evidence(
                    EvidenceUpload(
                        organization_id=org_id,
                        requirement_id=req_id,
                        filename=filename,
                        description=description,
                        file_type=file_type,
                    )
                )
                st.success(f"登録完了: {record.filename}")
            except Exception as e:
                st.error(f"登録エラー: {e}")

    # 登録済みエビデンス一覧
    st.markdown("---")
    st.subheader("登録済みエビデンス")
    try:
        evidences = list_evidence(org_id)
        if evidences:
            table = []
            for ev in evidences:
                table.append({
                    "要件ID": ev.requirement_id,
                    "ファイル名": ev.filename,
                    "種別": ev.file_type,
                    "説明": ev.description,
                    "登録日": ev.uploaded_at[:10] if ev.uploaded_at else "",
                })
            st.dataframe(table, use_container_width=True)
        else:
            st.info("登録されたエビデンスはありません。")
    except Exception as e:
        st.warning(f"一覧取得エラー: {e}")


# ── 6. レポート ──────────────────────────────────────────────────

def page_reports():
    st.header("レポート")

    assessment = st.session_state.assessment_result
    gap = st.session_state.gap_result

    if assessment is None or gap is None:
        st.info("レポートを生成するには、先に「診断」を実行してください。")
        return

    st.subheader("レポート生成")
    st.markdown("診断結果とギャップ分析を元にPDFレポートを生成します。")

    org_name = st.text_input("組織名（レポート表示用）", value=st.session_state.organization_name)

    if st.button("PDFレポートを生成", type="primary"):
        with st.spinner("レポート生成中..."):
            try:
                evidence_summary = None
                try:
                    evidence_summary = get_evidence_summary(st.session_state.organization_id)
                except Exception:
                    pass

                report = _run_async(generate_report(
                    assessment,
                    gap,
                    evidence_summary=evidence_summary,
                    organization_name=org_name,
                ))
                st.success(f"レポート生成完了: {report.filename}")

                # PDFダウンロード
                report_path = os.path.join("reports", report.filename)
                if os.path.exists(report_path):
                    with open(report_path, "rb") as f:
                        st.download_button(
                            label="PDFをダウンロード",
                            data=f.read(),
                            file_name=report.filename,
                            mime="application/pdf",
                        )
            except Exception as e:
                st.error(f"レポート生成エラー: {e}")

    # 現在の結果サマリー
    st.markdown("---")
    st.subheader("現在の評価サマリー")
    col1, col2, col3 = st.columns(3)
    col1.metric("成熟度", _maturity_label(assessment.maturity_level))
    col2.metric("スコア", f"{assessment.overall_score:.2f}/4.00")
    col3.metric(
        "充足率",
        f"{gap.compliant_count / gap.total_requirements:.0%}" if gap.total_requirements > 0 else "---",
    )


# ── 7. AIアドバイザー ──────────────────────────────────────────────

def page_advisor():
    st.header("AIアドバイザー")
    st.caption("AIガバナンスに関する質問にお答えします（Anthropic APIキーがない場合はFAQフォールバック）")

    # チャット履歴表示
    for msg in st.session_state.chat_messages:
        role = msg["role"]
        with st.chat_message(role):
            st.markdown(msg["content"])

    # ユーザー入力
    if prompt := st.chat_input("質問を入力してください..."):
        # ユーザーメッセージ追加
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI応答
        with st.chat_message("assistant"):
            with st.spinner("回答を生成中..."):
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
                    st.session_state.chat_messages.append({"role": "assistant", "content": answer})

                    if response.sources:
                        st.caption(f"参照: {', '.join(response.sources)}")
                except Exception as e:
                    error_msg = f"回答の生成中にエラーが発生しました: {e}"
                    st.error(error_msg)
                    st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})

    # クリアボタン
    if st.session_state.chat_messages:
        if st.button("会話をクリア"):
            st.session_state.chat_messages = []
            st.session_state.chat_session_id = ""
            st.rerun()


# ── 8. 設定 ────────────────────────────────────────────────────────

def page_settings():
    st.header("設定")

    st.subheader("組織情報")

    with st.form("org_settings"):
        name = st.text_input("組織名", value=st.session_state.organization_name)
        industry = st.selectbox(
            "業界",
            ["IT・通信", "金融・保険", "製造", "医療・ヘルスケア", "小売・EC", "公共・行政", "教育", "その他"],
            index=["IT・通信", "金融・保険", "製造", "医療・ヘルスケア", "小売・EC", "公共・行政", "教育", "その他"].index(
                st.session_state.organization_industry
            ) if st.session_state.organization_industry in ["IT・通信", "金融・保険", "製造", "医療・ヘルスケア", "小売・EC", "公共・行政", "教育", "その他"] else 0,
        )
        size = st.selectbox(
            "組織規模",
            ["small", "medium", "large", "enterprise"],
            format_func=lambda v: {
                "small": "小規模 (〜50名)",
                "medium": "中規模 (50〜300名)",
                "large": "大規模 (300〜1000名)",
                "enterprise": "エンタープライズ (1000名〜)",
            }.get(v, v),
            index=["small", "medium", "large", "enterprise"].index(st.session_state.organization_size)
            if st.session_state.organization_size in ["small", "medium", "large", "enterprise"] else 1,
        )

        submitted = st.form_submit_button("保存", type="primary")
        if submitted:
            st.session_state.organization_name = name
            st.session_state.organization_industry = industry
            st.session_state.organization_size = size
            st.success("組織情報を保存しました。")

    st.markdown("---")
    st.subheader("データ管理")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("診断データをリセット"):
            st.session_state.assessment_result = None
            st.session_state.gap_result = None
            st.session_state.iso_result = None
            st.session_state.assessment_answers = {}
            st.session_state.assessment_step = 0
            st.success("診断データをリセットしました。")
    with col2:
        if st.button("チャット履歴をリセット"):
            st.session_state.chat_messages = []
            st.session_state.chat_session_id = ""
            st.success("チャット履歴をリセットしました。")


# ══════════════════════════════════════════════════════════════════
# ルーティング
# ══════════════════════════════════════════════════════════════════

PAGE_MAP = {
    "\U0001f4ca ダッシュボード": page_dashboard,
    "\U0001f4cb 診断 (Self-Assessment)": page_assessment,
    "\U0001f50d ギャップ分析": page_gap_analysis,
    "\U0001f916 AIシステム台帳": page_ai_registry,
    "\U0001f4c2 エビデンス管理": page_evidence,
    "\U0001f4c4 レポート": page_reports,
    "\U0001f4ac AIアドバイザー": page_advisor,
    "\u2699\ufe0f 設定": page_settings,
}

page_fn = PAGE_MAP.get(page, page_dashboard)
page_fn()
