from __future__ import annotations

import json

import pandas as pd
import plotly.express as px
import streamlit as st

from src.config import (
    ASEAN_COUNTRIES,
    CLEAN_PATH,
    CLUSTER_EVAL_PATH,
    CLUSTER_PATH,
    COVERAGE_PATH,
    FEATURE_PATH,
    METADATA_PATH,
    OUTLIER_PATH,
    RANKING_PATH,
    STORY_PATH,
)


st.set_page_config(
    page_title="ASEAN Recovery Observatory",
    page_icon="🌏",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1500px;}
    .hero {
        padding: 1.6rem 1.8rem; border-radius: 18px;
        background: linear-gradient(120deg, #082f49 0%, #0f766e 65%, #14b8a6 100%);
        color: white; margin-bottom: 1rem;
    }
    .hero h1 {font-size: 2.1rem; margin: 0 0 .4rem 0; color: white;}
    .hero p {font-size: 1rem; margin: 0; opacity: .9;}
    .story-card {
        border: 1px solid #dbeafe; border-left: 5px solid #0f766e;
        border-radius: 12px; padding: 1rem; min-height: 190px; background: #f8fafc;
    }
    .story-card h4 {margin: 0 0 .55rem 0; color: #0f172a;}
    .story-card p {font-size: .92rem; color: #334155;}
    .step {
        border-radius: 12px; padding: .75rem .85rem; text-align: center;
        background: #ecfeff; border: 1px solid #a5f3fc; min-height: 92px;
    }
    .step strong {color: #155e75;}
    div[data-testid="stMetric"] {
        border: 1px solid #e2e8f0; border-radius: 12px; padding: .8rem 1rem;
        background: white;
    }
    div[data-testid="stMetricValue"] {color: #0f766e;}
    .small-note {color: #64748b; font-size: .88rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


INDICATOR_LABELS = {
    "NGDP_RPCH": "Real GDP growth · annual % change",
    "PCPIPCH": "Inflation · annual % change",
    "GGXWDG_NGDP": "Government gross debt · % GDP",
    "LUR": "Unemployment rate · %",
    "BCA_NGDPD": "Current account balance · % GDP",
}

COUNTRY_COLORS = {
    country: color
    for country, color in zip(
        ASEAN_COUNTRIES.values(),
        px.colors.qualitative.Safe + px.colors.qualitative.Set2,
    )
}


@st.cache_data
def load_outputs() -> dict:
    required = [
        CLEAN_PATH,
        FEATURE_PATH,
        COVERAGE_PATH,
        RANKING_PATH,
        OUTLIER_PATH,
        CLUSTER_PATH,
        STORY_PATH,
        METADATA_PATH,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Run `python run_pipeline.py` first. Missing: " + ", ".join(missing))
    return {
        "clean": pd.read_csv(CLEAN_PATH),
        "features": pd.read_csv(FEATURE_PATH),
        "coverage": pd.read_csv(COVERAGE_PATH),
        "ranking": pd.read_csv(RANKING_PATH),
        "outliers": pd.read_csv(OUTLIER_PATH),
        "clusters": pd.read_csv(CLUSTER_PATH),
        "cluster_eval": pd.read_csv(CLUSTER_EVAL_PATH) if CLUSTER_EVAL_PATH.exists() else pd.DataFrame(),
        "stories": pd.read_csv(STORY_PATH),
        "metadata": json.loads(METADATA_PATH.read_text(encoding="utf-8")),
    }


def format_number(value: float, suffix: str = "") -> str:
    return "—" if pd.isna(value) else f"{value:+.2f}{suffix}"


def story_card(row: pd.Series) -> str:
    return (
        '<div class="story-card">'
        f"<h4>{row['title']}</h4>"
        f"<p><strong>{row['countries_involved']}</strong></p>"
        f"<p>{row['evidence']}</p>"
        "</div>"
    )


try:
    data = load_outputs()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.code("python run_pipeline.py --force-download")
    st.stop()

clean = data["clean"]
features = data["features"]
ranking = data["ranking"]
clusters = data["clusters"]
metadata = data["metadata"]

st.markdown(
    """
    <div class="hero">
      <h1>ASEAN-10 Recovery Observatory</h1>
      <p>COVID shock → recovery → economic costs | IMF WEO April 2026 | 2015–2024</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Khám phá dữ liệu")
    selected = st.multiselect(
        "Quốc gia hiển thị",
        list(ASEAN_COUNTRIES.values()),
        default=list(ASEAN_COUNTRIES.values()),
    )
    st.divider()
    st.markdown("**Câu hỏi nghiên cứu**")
    st.write(
        "Nền kinh tế nào phục hồi mạnh hơn sau COVID-19, và kết quả đó đi cùng thay đổi nào về "
        "lạm phát, nợ công, thất nghiệp và cán cân vãng lai?"
    )
    st.info("Các chiều được báo cáo riêng. Không dùng composite score và không suy diễn nhân quả.")
    with st.expander("Cách đọc dashboard"):
        st.write(
            "1. Đọc ba phát hiện chính ở Tổng quan.\n\n"
            "2. So sánh chuỗi thời gian trong Country lens.\n\n"
            "3. Kiểm tra trade-off và nhóm phục hồi.\n\n"
            "4. Xem missing data và phương pháp ở Method & QA."
        )
    st.download_button(
        "Tải dữ liệu sạch",
        CLEAN_PATH.read_bytes(),
        file_name="clean_imf_weo.csv",
        mime="text/csv",
        width="stretch",
    )
    st.download_button(
        "Tải candidate stories",
        STORY_PATH.read_bytes(),
        file_name="candidate_stories.csv",
        mime="text/csv",
        width="stretch",
    )

if not selected:
    st.warning("Hãy chọn ít nhất một quốc gia.")
    st.stop()

view = clean[clean["country"].isin(selected)].copy()
feature_view = features[features["country"].isin(selected)].copy()

tab_overview, tab_country, tab_tradeoff, tab_patterns, tab_method = st.tabs(
    ["Executive overview", "Country lens", "Trade-offs", "Patterns & stories", "Method & QA"]
)

with tab_overview:
    available = int(view["value"].notna().sum())
    expected = len(view)
    overall_coverage = available / expected if expected else 0
    best = feature_view.dropna(subset=["recovery_gap"]).sort_values("recovery_gap", ascending=False).iloc[0]
    worst = feature_view.dropna(subset=["recovery_gap"]).sort_values("recovery_gap").iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Phạm vi", f"{feature_view['country'].nunique()} nền kinh tế")
    c2.metric("Data coverage", f"{overall_coverage:.0%}", f"{available}/{expected} observations")
    c3.metric("Recovery gap cao nhất", format_number(best["recovery_gap"], " pp"), best["country"])
    c4.metric("Recovery gap thấp nhất", format_number(worst["recovery_gap"], " pp"), worst["country"], delta_color="inverse")

    st.subheader("Ba phát hiện đáng kể nhất")
    story_columns = st.columns(3)
    for column, (_, row) in zip(story_columns, data["stories"].head(3).iterrows()):
        column.markdown(story_card(row), unsafe_allow_html=True)

    st.subheader("Từ baseline đến phục hồi")
    comparison = feature_view[
        ["country", "pre_growth", "covid_growth", "recovery_growth", "recovery_gap"]
    ].melt(id_vars=["country", "recovery_gap"], var_name="period", value_name="growth")
    comparison["period"] = comparison["period"].map(
        {
            "pre_growth": "Baseline · 2015–2019",
            "covid_growth": "Shock · 2020",
            "recovery_growth": "Recovery · 2021–2024",
        }
    )
    fig = px.bar(
        comparison,
        x="country",
        y="growth",
        color="period",
        barmode="group",
        color_discrete_map={
            "Baseline · 2015–2019": "#2563eb",
            "Shock · 2020": "#ef4444",
            "Recovery · 2021–2024": "#0f766e",
        },
        labels={"country": "", "growth": "Real GDP growth (%)", "period": ""},
    )
    fig.update_layout(legend_orientation="h", legend_y=1.12, margin=dict(t=55, b=20))
    st.plotly_chart(fig, width="stretch")

    table = ranking[ranking["country"].isin(selected)][
        ["country", "covid_shock", "recovery_gap", "inflation_cost", "debt_cost", "tradeoff_profile"]
    ].rename(
        columns={
            "country": "Country",
            "covid_shock": "COVID shock",
            "recovery_gap": "Recovery gap",
            "inflation_cost": "Inflation cost",
            "debt_cost": "Debt cost",
            "tradeoff_profile": "Profile",
        }
    )
    st.dataframe(
        table.round(2),
        hide_index=True,
        width="stretch",
        column_config={
            "COVID shock": st.column_config.NumberColumn(format="%.2f"),
            "Recovery gap": st.column_config.NumberColumn(format="%.2f"),
            "Inflation cost": st.column_config.NumberColumn(format="%.2f"),
            "Debt cost": st.column_config.NumberColumn(format="%.2f"),
        },
    )

with tab_country:
    st.subheader("So sánh từng nền kinh tế theo thời gian")
    left, right = st.columns([1, 2])
    with left:
        indicator = st.selectbox("Chỉ tiêu", list(INDICATOR_LABELS), format_func=INDICATOR_LABELS.get)
        focus = st.multiselect(
            "Quốc gia so sánh",
            selected,
            default=selected[: min(4, len(selected))],
            key="country_lens_selection",
        )
        st.markdown(
            "<p class='small-note'>Vùng xanh: baseline 2015–2019 · đường đỏ: COVID 2020 · vùng lục: recovery 2021–2024.</p>",
            unsafe_allow_html=True,
        )
    with right:
        period = view[(view["indicator_code"] == indicator) & view["country"].isin(focus)]
        fig = px.line(
            period,
            x="year",
            y="value",
            color="country",
            markers=True,
            color_discrete_map=COUNTRY_COLORS,
            labels={"year": "Year", "value": INDICATOR_LABELS[indicator], "country": ""},
        )
        fig.add_vrect(x0=2015, x1=2019, fillcolor="#3b82f6", opacity=0.05, line_width=0)
        fig.add_vline(x=2020, line_dash="dash", line_color="#dc2626")
        fig.add_vrect(x0=2021, x1=2024, fillcolor="#10b981", opacity=0.06, line_width=0)
        fig.update_layout(legend_orientation="h", legend_y=1.14, margin=dict(t=50, b=20))
        st.plotly_chart(fig, width="stretch")

    if focus:
        detail = feature_view[feature_view["country"].isin(focus)].set_index("country")
        st.subheader("Recovery profile")
        st.dataframe(
            detail[
                ["covid_shock", "recovery_gap", "inflation_cost", "debt_cost", "unemployment_change", "current_account_change"]
            ].round(2),
            width="stretch",
        )

with tab_tradeoff:
    st.subheader("Phục hồi đi cùng chi phí nào?")
    left, right = st.columns(2)
    trade = feature_view.dropna(subset=["recovery_gap"])
    with left:
        fig = px.scatter(
            trade.dropna(subset=["inflation_cost"]),
            x="inflation_cost",
            y="recovery_gap",
            color="country",
            text="country",
            color_discrete_map=COUNTRY_COLORS,
            hover_data=["covid_shock", "debt_cost"],
            labels={"inflation_cost": "Inflation cost (pp)", "recovery_gap": "Recovery gap (pp)", "country": ""},
            title="Recovery vs inflation cost",
        )
        fig.update_traces(textposition="top center", marker_size=12)
        fig.add_hline(y=0, line_color="#94a3b8")
        fig.add_vline(x=0, line_color="#94a3b8")
        st.plotly_chart(fig, width="stretch")
    with right:
        fig = px.scatter(
            trade.dropna(subset=["debt_cost"]),
            x="debt_cost",
            y="recovery_gap",
            color="country",
            text="country",
            color_discrete_map=COUNTRY_COLORS,
            hover_data=["inflation_cost", "current_account_change"],
            labels={"debt_cost": "Debt cost (pp GDP)", "recovery_gap": "Recovery gap (pp)", "country": ""},
            title="Recovery vs government gross debt",
        )
        fig.update_traces(textposition="top center", marker_size=12)
        fig.add_hline(y=0, line_color="#94a3b8")
        fig.add_vline(x=0, line_color="#94a3b8")
        st.plotly_chart(fig, width="stretch")
    st.warning(
        "Các biểu đồ thể hiện đồng biến hoặc nghịch biến mô tả, không chứng minh nhân quả. Gross debt không phải net debt; "
        "Singapore cần được đọc cùng bối cảnh tài sản của chính phủ."
    )

with tab_patterns:
    cluster_column, story_column = st.columns([1.1, 1])
    with cluster_column:
        st.subheader("Nhóm phục hồi")
        cluster_view = clusters[clusters["country"].isin(selected)].dropna(subset=["pca_1", "pca_2"])
        if cluster_view.empty:
            st.warning("Không đủ dữ liệu cho clustering.")
        else:
            fig = px.scatter(
                cluster_view,
                x="pca_1",
                y="pca_2",
                color="cluster_label",
                text="country",
                hover_data=["cluster"],
                labels={"pca_1": "PCA dimension 1", "pca_2": "PCA dimension 2", "cluster_label": ""},
            )
            fig.update_traces(textposition="top center", marker_size=14)
            fig.update_layout(legend_orientation="h", legend_y=1.16, margin=dict(t=65, b=20))
            st.plotly_chart(fig, width="stretch")
        with st.expander("Model selection: KMeans và Hierarchical, k=2…5"):
            st.dataframe(data["cluster_eval"], hide_index=True, width="stretch")
    with story_column:
        st.subheader("Evidence cards")
        for index, row in data["stories"].iterrows():
            with st.expander(f"{index + 1}. {row['title']}", expanded=index < 2):
                st.markdown(f"**Countries:** {row['countries_involved']}")
                st.markdown(f"**Evidence:** {row['evidence']}")
                st.markdown(f"**Interpretation:** {row['interpretation']}")
                st.markdown(f"**Alternative explanation:** {row['alternative_explanation']}")
                st.markdown(f"**Limitation:** {row['limitation']}")

with tab_method:
    st.subheader("Pipeline có thể kiểm tra và tái lập")
    steps = [
        ("1 · Retrieve", "IMF SDMX 2.1", "Raw XML retained"),
        ("2 · Parse", "Series + Obs", "Full 500-row grid"),
        ("3 · Validate", "Duplicates + NA", "Country × indicator coverage"),
        ("4 · Derive", "Shock + recovery", "Transparent formulas"),
        ("5 · Explore", "Outliers + clusters", "Candidate stories"),
    ]
    for column, (number, title, detail) in zip(st.columns(5), steps):
        column.markdown(
            f'<div class="step"><strong>{number}</strong><br>{title}<br><span class="small-note">{detail}</span></div>',
            unsafe_allow_html=True,
        )

    st.subheader("Coverage theo country × indicator")
    coverage = data["coverage"].copy()
    unavailable_lur = coverage[
        (coverage["indicator_code"] == "LUR")
        & (coverage["available_2015_2024"] == 0)
    ]["country"].tolist()
    if unavailable_lur:
        st.info(
            "Đây không phải lỗi lấy dữ liệu: IMF WEO April 2026 không trả về chuỗi LUR "
            f"giai đoạn 2015–2024 cho {', '.join(unavailable_lur)}. "
            "Pipeline giữ nguyên NA theo yêu cầu, không nội suy và không dùng nguồn khác để lấp dữ liệu. "
            "Các phân tích liên quan đến thất nghiệp tự động chỉ dùng những quốc gia có quan sát hợp lệ."
        )
    coverage_matrix = coverage.pivot(index="country", columns="indicator_code", values="coverage_2015_2024")
    coverage_matrix = coverage_matrix.reindex(columns=list(INDICATOR_LABELS))
    fig = px.imshow(
        coverage_matrix,
        zmin=0,
        zmax=1,
        color_continuous_scale=[(0, "#fecaca"), (0.7, "#fef3c7"), (1, "#99f6e4")],
        text_auto=".0%",
        aspect="auto",
        labels={"x": "Indicator", "y": "", "color": "Coverage"},
    )
    st.plotly_chart(fig, width="stretch")

    left, right = st.columns(2)
    with left:
        st.markdown("**Coverage details**")
        st.dataframe(coverage, hide_index=True, width="stretch")
    with right:
        st.markdown("**Outliers |z| ≥ 2**")
        st.dataframe(data["outliers"], hide_index=True, width="stretch")

    with st.expander("Data provenance và metadata"):
        st.json(metadata)
        st.code(
            "https://api.imf.org/external/sdmx/2.1/data/IMF.RES,WEO,+/"
            "BRN+KHM+IDN+LAO+MYS+MMR+PHL+SGP+THA+VNM."
            "NGDP_RPCH+PCPIPCH+GGXWDG_NGDP+LUR+BCA_NGDPD.A"
            "?startPeriod=2015&endPeriod=2024"
        )
