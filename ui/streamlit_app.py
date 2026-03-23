"""Streamlit UI for JPGovAI - AI Governance Mark取得支援.

使い方:
    streamlit run ui/streamlit_app.py
"""

from __future__ import annotations


import requests
import streamlit as st

# APIベースURL
API_BASE = "http://localhost:8000/api"

st.set_page_config(
    page_title="JPGovAI - AI Governance Mark取得支援",
    page_icon="🏛️",
    layout="wide",
)


def api_get(path: str, params: dict | None = None) -> dict | list | None:
    """API GETリクエスト."""
    try:
        resp = requests.get(f"{API_BASE}{path}", params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"API通信エラー: {e}")
        return None


def api_post(path: str, data: dict) -> dict | None:
    """API POSTリクエスト."""
    try:
        resp = requests.post(f"{API_BASE}{path}", json=data, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"API通信エラー: {e}")
        return None


# ── Sidebar ───────────────────────────────────────────────────────

st.sidebar.title("JPGovAI")
st.sidebar.markdown("**AI Governance Mark取得支援**")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "メニュー",
    [
        "ホーム",
        "組織登録",
        "自己診断",
        "ギャップ分析",
        "エビデンス管理",
        "レポート生成",
        "監査証跡",
        "ガイドライン参照",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown("METI AI事業者ガイドライン v1.0 準拠")
st.sidebar.markdown("Prototype Version 0.1.0")

# ── Session State ─────────────────────────────────────────────────

if "org_id" not in st.session_state:
    st.session_state.org_id = ""
if "assessment_id" not in st.session_state:
    st.session_state.assessment_id = ""
if "gap_id" not in st.session_state:
    st.session_state.gap_id = ""


# ── Pages ─────────────────────────────────────────────────────────

if page == "ホーム":
    st.title("JPGovAI - AI Governance Mark取得支援")
    st.markdown(
        """
        ### AI Governance Markとは
        経済産業省・総務省の「AI事業者ガイドライン」に準拠したAIガバナンス体制を
        構築・証明するための認証制度です。

        ### JPGovAIでできること
        1. **自己診断**: 25問の質問票でAIガバナンス成熟度を診断
        2. **ギャップ分析**: ガイドラインの各要件に対する充足状況を可視化
        3. **エビデンス管理**: 各要件に対するエビデンスを一元管理
        4. **レポート生成**: 申請用の自己評価レポートをAIが自動生成
        5. **監査証跡**: 全操作の改竄防止ログを自動記録

        ### 使い方
        1. まず「組織登録」で組織情報を登録
        2. 「自己診断」で質問票に回答
        3. 「ギャップ分析」で改善点を確認
        4. 「エビデンス管理」でエビデンスを登録
        5. 「レポート生成」で申請用レポートを出力
        """
    )

    # Health check
    health = api_get("/health")
    if health:
        st.success(f"APIサーバー接続OK (version: {health.get('version', '?')})")
    else:
        st.warning("APIサーバーに接続できません。`uvicorn app.main:app --reload` で起動してください。")

elif page == "組織登録":
    st.title("組織登録")
    st.markdown("AIガバナンス診断を行う組織の情報を登録します。")

    with st.form("org_form"):
        name = st.text_input("組織名", placeholder="株式会社サンプル")
        industry = st.selectbox(
            "業種",
            ["IT・通信", "金融・保険", "医療・ヘルスケア", "製造", "小売・EC", "公共・行政", "教育", "その他"],
        )
        size = st.selectbox(
            "企業規模",
            ["small (50人未満)", "medium (50-300人)", "large (300-1000人)", "enterprise (1000人以上)"],
        )
        ai_role = st.selectbox(
            "AI事業者としての立場",
            ["developer (AI開発者)", "provider (AI提供者)", "user (AI利用者)"],
        )
        submitted = st.form_submit_button("登録")

    if submitted and name:
        result = api_post(
            "/organizations",
            {
                "name": name,
                "industry": industry,
                "size": size.split(" ")[0],
                "ai_role": ai_role.split(" ")[0],
            },
        )
        if result:
            st.session_state.org_id = result["id"]
            st.success(f"組織を登録しました。ID: {result['id']}")

    if st.session_state.org_id:
        st.info(f"現在の組織ID: {st.session_state.org_id}")

elif page == "自己診断":
    st.title("AI利用状況の自己診断")
    st.markdown("質問票に回答して、AIガバナンス成熟度を診断します。")

    if not st.session_state.org_id:
        st.warning("先に「組織登録」を行ってください。")
    else:
        questions = api_get("/guidelines/questions")
        if questions:
            answers = []
            with st.form("assessment_form"):
                for i, q in enumerate(questions):
                    st.markdown(f"**Q{i+1}. {q['text']}**")
                    selected = st.radio(
                        f"選択 (Q{i+1})",
                        options=range(len(q["options"])),
                        format_func=lambda x, opts=q["options"]: opts[x],
                        key=f"q_{q['question_id']}",
                        horizontal=True,
                    )
                    answers.append(
                        {"question_id": q["question_id"], "selected_index": selected}
                    )
                    st.markdown("---")

                submitted = st.form_submit_button("診断を実行", type="primary")

            if submitted:
                result = api_post(
                    "/assessment",
                    {
                        "organization_id": st.session_state.org_id,
                        "answers": answers,
                    },
                )
                if result:
                    st.session_state.assessment_id = result["id"]
                    st.success("診断が完了しました！")

                    # 結果表示
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("総合スコア", f"{result['overall_score']:.2f} / 4.00")
                    with col2:
                        st.metric("成熟度レベル", f"Level {result['maturity_level']}")

                    st.subheader("カテゴリ別スコア")
                    for cs in result.get("category_scores", []):
                        progress = cs["score"] / cs["max_score"]
                        st.markdown(f"**{cs['category_title']}**")
                        st.progress(progress, text=f"{cs['score']:.2f} / {cs['max_score']:.2f} (Level {cs['maturity_level']})")

elif page == "ギャップ分析":
    st.title("ギャップ分析")
    st.markdown("ガイドラインの各要件に対する充足状況を分析します。")

    if not st.session_state.assessment_id:
        st.warning("先に「自己診断」を実行してください。")
    else:
        if st.button("ギャップ分析を実行", type="primary"):
            with st.spinner("分析中...（AI改善提案を生成しています）"):
                result = api_post(
                    f"/gap-analysis?assessment_id={st.session_state.assessment_id}",
                    {},
                )
            if result:
                st.session_state.gap_id = result["id"]
                st.success("分析が完了しました！")

                # サマリー
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("充足", result["compliant_count"], delta_color="normal")
                with col2:
                    st.metric("部分充足", result["partial_count"], delta_color="off")
                with col3:
                    st.metric("未充足", result["non_compliant_count"], delta_color="inverse")

                # 要件別ステータス
                st.subheader("要件別ステータス")
                for gap in result.get("gaps", []):
                    status = gap["status"]
                    if status == "compliant":
                        color = "🟢"
                    elif status == "partial":
                        color = "🟡"
                    else:
                        color = "🔴"

                    with st.expander(f"{color} {gap['req_id']}: {gap['title']} ({status})"):
                        st.markdown(f"**スコア**: {gap['current_score']:.2f}")
                        st.markdown(f"**優先度**: {gap['priority']}")
                        if gap.get("gap_description"):
                            st.markdown(f"**ギャップ**: {gap['gap_description']}")
                        if gap.get("improvement_actions"):
                            st.markdown("**改善アクション**:")
                            for action in gap["improvement_actions"]:
                                st.markdown(f"  - {action}")

                # AI改善提案
                if result.get("ai_recommendations"):
                    st.subheader("AI改善提案")
                    st.markdown(result["ai_recommendations"])

elif page == "エビデンス管理":
    st.title("エビデンス管理")
    st.markdown("各要件に対するエビデンスをアップロード・管理します。")

    if not st.session_state.org_id:
        st.warning("先に「組織登録」を行ってください。")
    else:
        tab1, tab2 = st.tabs(["アップロード", "充足率ダッシュボード"])

        with tab1:
            st.subheader("エビデンスのアップロード")
            requirements = api_get("/guidelines/requirements")
            if requirements:
                with st.form("evidence_form"):
                    req_options = {
                        f"{r['req_id']}: {r['title']}": r["req_id"]
                        for r in requirements
                    }
                    selected_req = st.selectbox("対象要件", list(req_options.keys()))
                    filename = st.text_input("ファイル名", placeholder="governance_policy_v1.pdf")
                    description = st.text_area("説明", placeholder="AIガバナンス基本方針文書（2024年版）")
                    file_type = st.selectbox(
                        "文書種別",
                        ["policy (方針文書)", "test_result (テスト結果)", "audit_log (監査ログ)",
                         "training_record (研修記録)", "other (その他)"],
                    )
                    submitted = st.form_submit_button("登録")

                if submitted and filename:
                    result = api_post(
                        "/evidence",
                        {
                            "organization_id": st.session_state.org_id,
                            "requirement_id": req_options[selected_req],
                            "filename": filename,
                            "description": description,
                            "file_type": file_type.split(" ")[0],
                        },
                    )
                    if result:
                        st.success(f"エビデンスを登録しました。ID: {result['id']}")

        with tab2:
            st.subheader("エビデンス充足率")
            summary = api_get(f"/evidence-summary/{st.session_state.org_id}")
            if summary:
                st.metric(
                    "全体充足率",
                    f"{summary['coverage_rate']:.0%}",
                )
                st.progress(summary["coverage_rate"])

                st.markdown("### カテゴリ別充足率")
                for cat_id, info in summary.get("by_category", {}).items():
                    rate = info.get("rate", 0)
                    st.markdown(f"**{info.get('title', cat_id)}**")
                    st.progress(
                        rate,
                        text=f"{info.get('covered', 0)}/{info.get('total', 0)} ({rate:.0%})",
                    )

elif page == "レポート生成":
    st.title("レポート生成")
    st.markdown("AI Governance Mark申請用の自己評価レポートを自動生成します。")

    if not st.session_state.assessment_id or not st.session_state.gap_id:
        st.warning("先に「自己診断」と「ギャップ分析」を実行してください。")
    else:
        if st.button("レポートを生成", type="primary"):
            with st.spinner("レポート生成中..."):
                result = api_post(
                    "/report",
                    {
                        "organization_id": st.session_state.org_id,
                        "assessment_id": st.session_state.assessment_id,
                        "gap_analysis_id": st.session_state.gap_id,
                        "include_evidence": True,
                    },
                )
            if result:
                st.success(f"レポートを生成しました: {result['filename']}")
                st.info(f"プレビュー: {result.get('content_preview', '')}")
                st.markdown(f"📄 レポートファイル: `reports/{result['filename']}`")

elif page == "監査証跡":
    st.title("監査証跡")
    st.markdown("全操作の改竄防止ログを確認します。")

    # チェーン検証
    col1, col2 = st.columns(2)
    with col1:
        if st.button("チェーン整合性を検証"):
            status = api_get("/audit/verify")
            if status:
                if status["chain_valid"]:
                    st.success(f"チェーン整合性: 有効 (イベント数: {status['total_events']})")
                else:
                    st.error("チェーン整合性: 改竄検出！")
                    for err in status.get("errors", []):
                        st.error(err)
                st.code(f"Merkle Root: {status['merkle_root']}", language="text")

    with col2:
        st.metric("", "SHA-256 ハッシュチェーン")
        st.caption("全イベントが暗号学的ハッシュで連鎖されています")

    # イベント一覧
    st.subheader("イベント一覧")
    events = api_get("/audit/events", params={"limit": 50})
    if events:
        for ev in reversed(events):
            with st.expander(
                f"#{ev['sequence']} | {ev['action']} | {ev['timestamp'][:19]}"
            ):
                st.json(ev)
    else:
        st.info("まだ監査イベントがありません。")

elif page == "ガイドライン参照":
    st.title("METI AI事業者ガイドライン 要件一覧")
    st.markdown(
        "経済産業省・総務省「AI事業者ガイドライン（第1.0版）」の要件定義です。"
    )

    categories = api_get("/guidelines/categories")
    if categories:
        for cat in categories:
            with st.expander(
                f"{cat['category_id']}: {cat['title']} ({cat['requirement_count']}要件)"
            ):
                st.markdown(cat["description"])
                # 個別要件
                requirements = api_get("/guidelines/requirements")
                if requirements:
                    cat_reqs = [r for r in requirements if r["category_id"] == cat["category_id"]]
                    for r in cat_reqs:
                        st.markdown(f"**{r['req_id']}: {r['title']}**")
                        st.markdown(f"  {r['description']}")
                        st.caption(f"対象: {', '.join(r['target_roles'])}")
                        st.markdown("---")
