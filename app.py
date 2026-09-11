from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src import config as project_config
from src.clustering import run_clustering
from src.config import (
    ASEAN_COUNTRIES,
    CLEAN_PATH,
    COVERAGE_PATH,
    FEATURE_PATH,
    METADATA_PATH,
    OUTLIER_PATH,
    STORY_PATH,
)
from src.features import build_transparent_ranking


_PROJECT_ROOT = Path(__file__).resolve().parent
_CROSSCHECK_DIR = _PROJECT_ROOT / "data" / "crosscheck"
WB_COMPARISON_PATH = getattr(
    project_config,
    "WB_COMPARISON_PATH",
    _CROSSCHECK_DIR / "imf_worldbank_gdp_growth_comparison.csv",
)
WB_SUMMARY_PATH = getattr(
    project_config,
    "WB_SUMMARY_PATH",
    _CROSSCHECK_DIR / "imf_worldbank_gdp_growth_summary.csv",
)


st.set_page_config(
    page_title="Bức tranh phục hồi kinh tế ASEAN-10",
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
    .hero p {font-size: 1rem; margin: 0; opacity: .92;}
    .story-card {
        border: 1px solid #dbeafe; border-left: 5px solid #0f766e;
        border-radius: 12px; padding: 1rem; min-height: 205px; background: #f8fafc;
    }
    .story-card h4 {margin: 0 0 .55rem 0; color: #0f172a;}
    .story-card p {font-size: .92rem; color: #334155;}
    .step {
        border-radius: 12px; padding: .8rem .85rem; text-align: center;
        background: #ecfeff; border: 1px solid #a5f3fc; min-height: 105px;
    }
    .step strong {color: #155e75;}
    .guide {
        border-radius: 14px; padding: 1rem 1.2rem; margin: .3rem 0 1rem 0;
        background: #f0fdfa; border: 1px solid #99f6e4; color: #134e4a;
    }
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


COUNTRY_VI = {
    "Brunei Darussalam": "Brunei",
    "Cambodia": "Campuchia",
    "Indonesia": "Indonesia",
    "Lao P.D.R.": "Lào",
    "Malaysia": "Malaysia",
    "Myanmar": "Myanmar",
    "Philippines": "Philippines",
    "Singapore": "Singapore",
    "Thailand": "Thái Lan",
    "Vietnam": "Việt Nam",
}

INDICATOR_LABELS = {
    "NGDP_RPCH": "Tăng trưởng GDP thực · % thay đổi hằng năm",
    "PCPIPCH": "Lạm phát bình quân · % thay đổi hằng năm",
    "GGXWDG_NGDP": "Nợ công gộp · % GDP",
    "LUR": "Tỷ lệ thất nghiệp · %",
    "BCA_NGDPD": "Cán cân vãng lai · % GDP",
}

FEATURE_LABELS = {
    "covid_shock": "Cú sốc tăng trưởng năm 2020",
    "recovery_gap": "Khoảng cách phục hồi",
    "inflation_cost": "Mức tăng áp lực lạm phát",
    "debt_cost": "Mức thay đổi nợ công",
    "unemployment_change": "Mức thay đổi thất nghiệp",
    "current_account_change": "Mức thay đổi cán cân vãng lai",
    "growth_volatility_post": "Biến động tăng trưởng sau dịch",
}

PROFILE_VI = {
    "Above-median recovery + lower inflation/debt cost": "Phục hồi trên trung vị, chi phí lạm phát và nợ thấp hơn",
    "Above-median recovery + higher cost": "Phục hồi trên trung vị nhưng chi phí vĩ mô cao hơn",
    "Below-median recovery + higher cost": "Phục hồi dưới trung vị và chi phí vĩ mô cao hơn",
    "Below-median recovery + lower cost": "Phục hồi dưới trung vị nhưng chi phí vĩ mô thấp hơn",
}

CLUSTER_VI = {
    "Singleton pattern (interpret cautiously)": "Mẫu hình đơn lẻ (cần diễn giải thận trọng)",
    "Other ASEAN economies (heterogeneous)": "Các nền kinh tế ASEAN còn lại (không đồng nhất)",
    "Above-median recovery, lower costs": "Phục hồi trên trung vị, chi phí thấp hơn",
    "Above-median recovery, higher costs": "Phục hồi trên trung vị, chi phí cao hơn",
    "Below-median recovery, higher costs": "Phục hồi dưới trung vị, chi phí cao hơn",
    "Below-median recovery, lower or mixed costs": "Phục hồi dưới trung vị, chi phí thấp hoặc đan xen",
    "Insufficient data": "Không đủ dữ liệu",
}

STORY_VI = {
    "Similar COVID shock, different recovery": {
        "title": "Cùng chịu cú sốc lớn, nhưng phục hồi theo hai hướng trái ngược",
        "evidence": "Lào và Singapore mất lần lượt 6,85 và 6,72 điểm phần trăm tăng trưởng trong năm 2020. Đến giai đoạn 2021–2024, khoảng cách phục hồi của Lào là -3,35 điểm, còn Singapore đạt +2,12 điểm.",
        "interpretation": "Mức độ thiệt hại ban đầu khá giống nhau không dẫn đến cùng một quỹ đạo phục hồi.",
        "alternative": "Khác biệt có thể liên quan đến cơ cấu ngành, thời điểm mở cửa, hiệu ứng nền và chính sách hỗ trợ.",
        "limitation": "So sánh mô tả này không xác định yếu tố nào là nguyên nhân trực tiếp.",
    },
    "Strong recovery with a high inflation bill": {
        "title": "Phục hồi mạnh đi cùng áp lực lạm phát cao hơn",
        "evidence": "Singapore có khoảng cách phục hồi +2,12 điểm phần trăm, đồng thời lạm phát bình quân sau dịch cao hơn mức nền khoảng 3,81 điểm.",
        "interpretation": "Tăng trưởng phục hồi và lạm phát cao hơn xuất hiện đồng thời trong giai đoạn quan sát.",
        "alternative": "Giá thực phẩm, năng lượng và các cú sốc toàn cầu có thể tác động đến lạm phát độc lập với phục hồi trong nước.",
        "limitation": "Sự đồng biến không chứng minh phục hồi kinh tế gây ra lạm phát.",
    },
    "Debt rose while recovery stayed weak": {
        "title": "Nợ tăng trong khi đà phục hồi vẫn yếu",
        "evidence": "Myanmar có tỷ lệ nợ công năm 2024 cao hơn năm 2019 khoảng 13,02 điểm phần trăm GDP, trong khi khoảng cách phục hồi là -8,31 điểm.",
        "interpretation": "Nợ công cao hơn và tăng trưởng yếu hơn cùng xuất hiện trong một giai đoạn nhiều biến động.",
        "alternative": "Tỷ giá, cách ghi nhận nợ, hiệu ứng mẫu số và các biến cố riêng của quốc gia đều có thể ảnh hưởng kết quả.",
        "limitation": "Nợ gộp không phải nợ ròng và không phản ánh đầy đủ vị thế tài sản của chính phủ.",
    },
    "Recovery with contained inflation and debt costs": {
        "title": "Phục hồi tương đối tốt với áp lực lạm phát và nợ được kiềm chế",
        "evidence": "Brunei có khoảng cách phục hồi gần 0; áp lực lạm phát tăng 1,62 điểm, còn tỷ lệ nợ công giảm nhẹ 0,25 điểm phần trăm GDP.",
        "interpretation": "Trong phạm vi các chỉ tiêu được quan sát, Brunei có tổ hợp kết quả tương đối thuận lợi so với nhiều nước cùng khu vực.",
        "alternative": "Kết quả có thể chịu ảnh hưởng của giá hàng hóa, tăng trưởng mẫu số hoặc dư địa tài khóa sẵn có.",
        "limitation": "Đây là so sánh tương đối trong ASEAN-10, không phải xếp hạng sức chống chịu tuyệt đối.",
    },
    "ASEAN's clearest statistical outlier": {
        "title": "Trường hợp khác biệt rõ nhất về mặt thống kê",
        "evidence": "Myanmar có độ biến động tăng trưởng sau dịch là 6,98 và điểm chuẩn hóa z bằng 2,54.",
        "interpretation": "Quỹ đạo tăng trưởng của Myanmar khác biệt đáng kể so với phần còn lại của mẫu ASEAN-10.",
        "alternative": "Đặc điểm cơ cấu, biến cố trong nước hoặc quy ước đo lường có thể giải thích một phần khác biệt.",
        "limitation": "Với mẫu chỉ gồm 10 quốc gia, điểm z khá nhạy với từng quan sát riêng lẻ.",
    },
    "Positive growth, but still below the old baseline": {
        "title": "Đã tăng trưởng trở lại nhưng chưa bắt kịp nhịp độ cũ",
        "evidence": "Lào tăng trưởng bình quân 3,07% trong giai đoạn 2021–2024, nhưng vẫn thấp hơn mức nền trước dịch 3,35 điểm phần trăm.",
        "interpretation": "Tăng trưởng dương không đồng nghĩa nền kinh tế đã lấy lại tốc độ trước COVID-19.",
        "alternative": "Mức tăng trưởng trước dịch có thể từng cao bất thường hoặc khó duy trì lâu dài.",
        "limitation": "Số bình quân theo giai đoạn có thể che khuất các bước ngoặt từng năm.",
    },
    "Growth recovery without equal labor-market improvement": {
        "title": "Sản lượng phục hồi không đồng nghĩa thị trường lao động cải thiện tương ứng",
        "evidence": "Singapore có khoảng cách phục hồi +2,12 điểm, nhưng tỷ lệ thất nghiệp bình quân sau dịch vẫn cao hơn mức nền khoảng 0,06 điểm phần trăm.",
        "interpretation": "Tăng trưởng GDP và thị trường lao động có thể điều chỉnh với tốc độ khác nhau.",
        "alternative": "Tỷ lệ tham gia lực lượng lao động và cơ cấu việc làm có thể ảnh hưởng chỉ tiêu thất nghiệp.",
        "limitation": "WEO không có dữ liệu thất nghiệp cho đầy đủ cả 10 quốc gia ASEAN.",
    },
}

COUNTRY_COLORS = {
    country: color
    for country, color in zip(COUNTRY_VI.values(), px.colors.qualitative.Safe + px.colors.qualitative.Set2)
}


@st.cache_data
def load_outputs() -> dict:
    required = [CLEAN_PATH, FEATURE_PATH, COVERAGE_PATH, OUTLIER_PATH, STORY_PATH, METADATA_PATH, WB_COMPARISON_PATH, WB_SUMMARY_PATH]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Chưa có đủ tệp dữ liệu. Hãy chạy `python run_pipeline.py` và `python run_crosscheck.py`. Tệp còn thiếu: "
            + ", ".join(missing)
        )
    features = pd.read_csv(FEATURE_PATH)
    ranking = build_transparent_ranking(features)
    clusters, cluster_eval, cluster_meta = run_clustering(features)
    return {
        "clean": pd.read_csv(CLEAN_PATH),
        "features": features,
        "coverage": pd.read_csv(COVERAGE_PATH),
        "ranking": ranking,
        "outliers": pd.read_csv(OUTLIER_PATH),
        "clusters": clusters,
        "cluster_eval": cluster_eval,
        "cluster_meta": cluster_meta,
        "stories": pd.read_csv(STORY_PATH),
        "metadata": json.loads(METADATA_PATH.read_text(encoding="utf-8")),
        "wb_comparison": pd.read_csv(WB_COMPARISON_PATH),
        "wb_summary": pd.read_csv(WB_SUMMARY_PATH),
    }


def format_number(value: float, suffix: str = "") -> str:
    return "—" if pd.isna(value) else f"{value:+.2f}{suffix}"


def country_vi(value: str) -> str:
    return COUNTRY_VI.get(value, value)


def add_country_vi(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["Quốc gia"] = result["country"].map(country_vi)
    return result


def cluster_label_vi(label: str) -> str:
    if pd.isna(label):
        return label
    result = str(label).replace("Cluster", "Nhóm")
    for english, vietnamese in CLUSTER_VI.items():
        result = result.replace(english, vietnamese)
    return result


def story_content(row: pd.Series) -> dict[str, str]:
    return STORY_VI.get(
        row["title"],
        {
            "title": row["title"],
            "evidence": row["evidence"],
            "interpretation": row["interpretation"],
            "alternative": row["alternative_explanation"],
            "limitation": row["limitation"],
        },
    )


def story_card(row: pd.Series) -> str:
    story = story_content(row)
    countries = ", ".join(country_vi(name.strip()) for name in str(row["countries_involved"]).split(";"))
    return (
        '<div class="story-card">'
        f"<h4>{story['title']}</h4>"
        f"<p><strong>{countries}</strong></p>"
        f"<p>{story['evidence']}</p>"
        "</div>"
    )


try:
    data = load_outputs()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.code("python run_pipeline.py --force-download\npython run_crosscheck.py --force-download")
    st.stop()

clean = data["clean"]
features = data["features"]
ranking = data["ranking"]
clusters = data["clusters"]
metadata = data["metadata"]

st.markdown(
    """
    <div class="hero">
      <h1>Bức tranh phục hồi kinh tế ASEAN-10</h1>
      <p>Từ cú sốc COVID-19 đến giai đoạn phục hồi · IMF WEO tháng 4/2026 · Dữ liệu 2015–2024</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Khám phá dữ liệu")
    selected = st.multiselect(
        "Chọn quốc gia",
        list(ASEAN_COUNTRIES.values()),
        default=list(ASEAN_COUNTRIES.values()),
        format_func=country_vi,
    )
    st.divider()
    st.markdown("**Câu hỏi của nghiên cứu**")
    st.write(
        "Sau cú sốc COVID-19, nền kinh tế nào lấy lại đà tăng trưởng tốt hơn so với chính mình trước dịch, "
        "và sự phục hồi đó đi cùng những thay đổi nào về lạm phát, nợ công, thất nghiệp và cán cân vãng lai?"
    )
    st.info("Mỗi chỉ tiêu được trình bày riêng. Nghiên cứu không tạo điểm tổng hợp tùy ý và không suy diễn quan hệ nhân quả.")
    with st.expander("Hướng dẫn xem trong 60 giây"):
        st.markdown(
            "1. **Đọc Tổng quan** để nắm câu chuyện chính.\n\n"
            "2. **Mở Từng quốc gia** để xem số liệu qua từng năm.\n\n"
            "3. **Xem Các đánh đổi** để biết phục hồi đi cùng áp lực nào.\n\n"
            "4. **Kiểm tra Dữ liệu & phương pháp** nếu muốn biết con số đến từ đâu."
        )
    st.download_button(
        "Tải bộ dữ liệu IMF đã làm sạch",
        CLEAN_PATH.read_bytes(),
        file_name="du_lieu_imf_weo_asean10.csv",
        mime="text/csv",
        width="stretch",
    )

if not selected:
    st.warning("Hãy chọn ít nhất một quốc gia để tiếp tục.")
    st.stop()

view = add_country_vi(clean[clean["country"].isin(selected)])
feature_view = add_country_vi(features[features["country"].isin(selected)])

tab_overview, tab_country, tab_tradeoff, tab_patterns, tab_method = st.tabs(
    ["Tổng quan", "Từng quốc gia", "Các đánh đổi", "Mẫu hình & câu chuyện", "Dữ liệu & phương pháp"]
)

with tab_overview:
    st.markdown(
        """
        <div class="guide"><strong>Hiểu bài toán trong một phút:</strong><br>
        Lấy tăng trưởng bình quân 2015–2019 làm mức nền → đo cú sốc năm 2020 → tính tăng trưởng bình quân
        2021–2024 → so sánh với mức nền. “Khoảng cách phục hồi” dương nghĩa là tăng trưởng sau dịch cao hơn
        mức trước dịch; số âm nghĩa là nền kinh tế đã tăng trở lại nhưng chưa lấy lại nhịp độ cũ.</div>
        """,
        unsafe_allow_html=True,
    )
    available = int(view["value"].notna().sum())
    expected = len(view)
    overall_coverage = available / expected if expected else 0
    recovery_rows = feature_view.dropna(subset=["recovery_gap"])
    best = recovery_rows.sort_values("recovery_gap", ascending=False).iloc[0]
    worst = recovery_rows.sort_values("recovery_gap").iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Phạm vi phân tích", f"{feature_view['country'].nunique()} nền kinh tế")
    c2.metric("Tỷ lệ dữ liệu có sẵn", f"{overall_coverage:.0%}", f"{available}/{expected} quan sát")
    c3.metric("Phục hồi cao nhất", format_number(best["recovery_gap"], " điểm %"), best["Quốc gia"])
    c4.metric("Phục hồi thấp nhất", format_number(worst["recovery_gap"], " điểm %"), worst["Quốc gia"], delta_color="inverse")

    st.subheader("Ba phát hiện nổi bật")
    story_columns = st.columns(3)
    for column, (_, row) in zip(story_columns, data["stories"].head(3).iterrows()):
        column.markdown(story_card(row), unsafe_allow_html=True)

    st.subheader("Tăng trưởng trước dịch, cú sốc năm 2020 và giai đoạn phục hồi")
    st.caption("Cách đọc: mỗi nhóm cột là một quốc gia; cột xanh lá cho biết tốc độ tăng trưởng bình quân sau dịch.")
    comparison = feature_view[["Quốc gia", "pre_growth", "covid_growth", "recovery_growth", "recovery_gap"]].melt(
        id_vars=["Quốc gia", "recovery_gap"], var_name="Giai đoạn", value_name="Tăng trưởng"
    )
    comparison["Giai đoạn"] = comparison["Giai đoạn"].map(
        {"pre_growth": "Mức nền · 2015–2019", "covid_growth": "Cú sốc · 2020", "recovery_growth": "Phục hồi · 2021–2024"}
    )
    fig = px.bar(
        comparison,
        x="Quốc gia",
        y="Tăng trưởng",
        color="Giai đoạn",
        barmode="group",
        color_discrete_map={"Mức nền · 2015–2019": "#2563eb", "Cú sốc · 2020": "#ef4444", "Phục hồi · 2021–2024": "#0f766e"},
        labels={"Tăng trưởng": "Tăng trưởng GDP thực (%)"},
    )
    fig.update_layout(legend_orientation="h", legend_y=1.12, margin=dict(t=55, b=20))
    st.plotly_chart(fig, width="stretch")

    table = ranking[ranking["country"].isin(selected)][
        ["country", "covid_shock", "recovery_gap", "inflation_cost", "debt_cost", "tradeoff_profile"]
    ].copy()
    table["country"] = table["country"].map(country_vi)
    table["tradeoff_profile"] = table["tradeoff_profile"].map(PROFILE_VI).fillna(table["tradeoff_profile"])
    table = table.rename(columns={
        "country": "Quốc gia", "covid_shock": "Cú sốc 2020", "recovery_gap": "Khoảng cách phục hồi",
        "inflation_cost": "Áp lực lạm phát", "debt_cost": "Thay đổi nợ công", "tradeoff_profile": "Hồ sơ phục hồi",
    })
    st.dataframe(table.round(2), hide_index=True, width="stretch")
    st.caption("Đơn vị các cột thay đổi: điểm phần trăm; nợ công là điểm phần trăm GDP.")

with tab_country:
    st.subheader("Theo dõi từng nền kinh tế qua thời gian")
    left, right = st.columns([1, 2])
    with left:
        indicator = st.selectbox("Chọn chỉ tiêu", list(INDICATOR_LABELS), format_func=INDICATOR_LABELS.get)
        focus = st.multiselect(
            "Chọn quốc gia để so sánh", selected, default=selected[: min(4, len(selected))],
            format_func=country_vi, key="country_lens_selection",
        )
        st.info("Vùng xanh dương là giai đoạn trước dịch; đường đỏ đánh dấu năm 2020; vùng xanh lá là giai đoạn phục hồi.")
    with right:
        period = view[(view["indicator_code"] == indicator) & view["country"].isin(focus)]
        fig = px.line(
            period, x="year", y="value", color="Quốc gia", markers=True, color_discrete_map=COUNTRY_COLORS,
            labels={"year": "Năm", "value": INDICATOR_LABELS[indicator]},
        )
        fig.add_vrect(x0=2015, x1=2019, fillcolor="#3b82f6", opacity=0.05, line_width=0)
        fig.add_vline(x=2020, line_dash="dash", line_color="#dc2626")
        fig.add_vrect(x0=2021, x1=2024, fillcolor="#10b981", opacity=0.06, line_width=0)
        fig.update_layout(legend_orientation="h", legend_y=1.14, margin=dict(t=50, b=20))
        st.plotly_chart(fig, width="stretch")
    if focus:
        detail = feature_view[feature_view["country"].isin(focus)][
            ["Quốc gia", "covid_shock", "recovery_gap", "inflation_cost", "debt_cost", "unemployment_change", "current_account_change"]
        ].rename(columns=FEATURE_LABELS)
        st.subheader("Hồ sơ phục hồi")
        st.dataframe(detail.round(2), hide_index=True, width="stretch")

with tab_tradeoff:
    st.subheader("Phục hồi kinh tế đi cùng những áp lực nào?")
    st.caption("Điểm càng cao trên trục dọc nghĩa là phục hồi càng tốt so với mức nền. Di chuyển sang phải cho thấy lạm phát hoặc nợ công tăng nhiều hơn.")
    left, right = st.columns(2)
    trade = feature_view.dropna(subset=["recovery_gap"])
    with left:
        fig = px.scatter(
            trade.dropna(subset=["inflation_cost"]), x="inflation_cost", y="recovery_gap", color="Quốc gia", text="Quốc gia",
            color_discrete_map=COUNTRY_COLORS, hover_data={"covid_shock": ":.2f", "debt_cost": ":.2f"},
            labels={"inflation_cost": "Mức tăng áp lực lạm phát (điểm %)", "recovery_gap": "Khoảng cách phục hồi (điểm %)"},
            title="Phục hồi và áp lực lạm phát",
        )
        fig.update_traces(textposition="top center", marker_size=12)
        fig.add_hline(y=0, line_color="#94a3b8")
        fig.add_vline(x=0, line_color="#94a3b8")
        st.plotly_chart(fig, width="stretch")
    with right:
        fig = px.scatter(
            trade.dropna(subset=["debt_cost"]), x="debt_cost", y="recovery_gap", color="Quốc gia", text="Quốc gia",
            color_discrete_map=COUNTRY_COLORS, hover_data={"inflation_cost": ":.2f", "current_account_change": ":.2f"},
            labels={"debt_cost": "Mức thay đổi nợ công (điểm % GDP)", "recovery_gap": "Khoảng cách phục hồi (điểm %)"},
            title="Phục hồi và thay đổi nợ công gộp",
        )
        fig.update_traces(textposition="top center", marker_size=12)
        fig.add_hline(y=0, line_color="#94a3b8")
        fig.add_vline(x=0, line_color="#94a3b8")
        st.plotly_chart(fig, width="stretch")
    st.warning(
        "Các biểu đồ chỉ cho thấy những biến số xuất hiện cùng nhau, không chứng minh biến này gây ra biến kia. "
        "Nợ công gộp cũng không phải nợ ròng; riêng Singapore cần được đọc cùng bối cảnh tài sản của chính phủ."
    )

with tab_patterns:
    cluster_column, story_column = st.columns([1.1, 1])
    with cluster_column:
        st.subheader("Các nhóm có đặc điểm phục hồi tương tự")
        st.caption("Thuật toán nhóm các quốc gia có bộ chỉ số gần nhau; đây là công cụ khám phá, không phải bảng xếp hạng.")
        cluster_view = add_country_vi(clusters[clusters["country"].isin(selected)]).dropna(subset=["pca_1", "pca_2"])
        if cluster_view.empty:
            st.warning("Không đủ dữ liệu để thực hiện phân nhóm.")
        else:
            cluster_view["Nhãn nhóm"] = cluster_view["cluster_label"].map(cluster_label_vi)
            if not data["cluster_eval"].empty and not data["cluster_eval"]["economically_reviewable"].any():
                st.warning(
                    "Mọi phương án từ 2 đến 5 nhóm đều tạo ra ít nhất một nhóm chỉ có một quốc gia. "
                    "Vì vậy, kết quả này chỉ mang tính khám phá và chưa phải một phân loại ổn định của ASEAN-10."
                )
            fig = px.scatter(
                cluster_view, x="pca_1", y="pca_2", color="Nhãn nhóm", text="Quốc gia",
                hover_data={"cluster": True, "pca_1": ":.2f", "pca_2": ":.2f"},
                labels={"pca_1": "Chiều tổng hợp 1", "pca_2": "Chiều tổng hợp 2"},
            )
            fig.update_traces(textposition="top center", marker_size=14)
            fig.update_layout(legend_orientation="h", legend_y=1.16, margin=dict(t=65, b=20))
            st.plotly_chart(fig, width="stretch")
        with st.expander("Cách chọn mô hình phân nhóm"):
            evaluation = data["cluster_eval"].rename(columns={
                "method": "Phương pháp", "k": "Số nhóm", "silhouette": "Điểm silhouette",
                "smallest_cluster": "Nhóm nhỏ nhất", "economically_reviewable": "Có thể diễn giải",
            })
            st.write("So sánh K-means và phân cụm phân cấp Ward với số nhóm từ 2 đến 5.")
            st.dataframe(evaluation, hide_index=True, width="stretch")
    with story_column:
        st.subheader("Các câu chuyện đáng chú ý")
        for index, row in data["stories"].iterrows():
            story = story_content(row)
            countries = ", ".join(country_vi(name.strip()) for name in str(row["countries_involved"]).split(";"))
            with st.expander(f"{index + 1}. {story['title']}", expanded=index < 2):
                st.markdown(f"**Quốc gia liên quan:** {countries}")
                st.markdown(f"**Bằng chứng:** {story['evidence']}")
                st.markdown(f"**Cách hiểu:** {story['interpretation']}")
                st.markdown(f"**Giải thích khác có thể có:** {story['alternative']}")
                st.markdown(f"**Giới hạn:** {story['limitation']}")

with tab_method:
    st.subheader("Dữ liệu được xử lý như thế nào?")
    st.caption("Toàn bộ quy trình có thể kiểm tra và chạy lại từ phản hồi gốc của IMF.")
    steps = [
        ("1 · Thu thập", "IMF SDMX 2.1", "Giữ nguyên phản hồi XML gốc"),
        ("2 · Đọc dữ liệu", "Chuỗi và quan sát", "Tạo đủ khung 500 dòng"),
        ("3 · Kiểm tra", "Trùng lặp và thiếu", "Độ phủ theo nước × chỉ tiêu"),
        ("4 · Tính toán", "Cú sốc và phục hồi", "Công thức minh bạch"),
        ("5 · Khám phá", "Ngoại lệ và phân nhóm", "Gợi ý câu chuyện"),
    ]
    for column, (number, title, detail) in zip(st.columns(5), steps):
        column.markdown(
            f'<div class="step"><strong>{number}</strong><br>{title}<br><span class="small-note">{detail}</span></div>',
            unsafe_allow_html=True,
        )

    st.subheader("Mức độ đầy đủ của dữ liệu theo quốc gia và chỉ tiêu")
    coverage = data["coverage"].copy()
    unavailable_lur = coverage[(coverage["indicator_code"] == "LUR") & (coverage["available_2015_2024"] == 0)]["country"].map(country_vi).tolist()
    if unavailable_lur:
        st.info(
            "Đây không phải lỗi tải dữ liệu. IMF WEO tháng 4/2026 không cung cấp chuỗi tỷ lệ thất nghiệp "
            f"giai đoạn 2015–2024 cho {', '.join(unavailable_lur)}. Hệ thống giữ nguyên giá trị thiếu, "
            "không nội suy và không lấy nguồn khác để điền vào bộ dữ liệu IMF."
        )
    coverage_matrix = coverage.pivot(index="country", columns="indicator_code", values="coverage_2015_2024")
    coverage_matrix.index = coverage_matrix.index.map(country_vi)
    coverage_matrix = coverage_matrix.rename(columns=INDICATOR_LABELS).reindex(columns=list(INDICATOR_LABELS.values()))
    fig = px.imshow(
        coverage_matrix, zmin=0, zmax=1,
        color_continuous_scale=[(0, "#fecaca"), (0.7, "#fef3c7"), (1, "#99f6e4")],
        text_auto=".0%", aspect="auto", labels={"x": "Chỉ tiêu", "y": "", "color": "Tỷ lệ có dữ liệu"},
    )
    st.plotly_chart(fig, width="stretch")

    left, right = st.columns(2)
    with left:
        st.markdown("**Chi tiết độ phủ dữ liệu**")
        coverage_table = coverage.copy()
        coverage_table["country"] = coverage_table["country"].map(country_vi)
        coverage_table["indicator_code"] = coverage_table["indicator_code"].map(INDICATOR_LABELS)
        coverage_table = coverage_table.rename(columns={
            "country_code": "Mã nước", "country": "Quốc gia", "indicator_code": "Chỉ tiêu",
            "available_2015_2024": "Số năm có dữ liệu", "coverage_2015_2024": "Tỷ lệ đầy đủ",
            "missing_years": "Năm bị thiếu", "serious_gap": "Thiếu nghiêm trọng",
        })
        st.dataframe(coverage_table, hide_index=True, width="stretch")
    with right:
        st.markdown("**Quan sát khác biệt mạnh (|z| ≥ 2)**")
        outliers = data["outliers"].copy()
        outliers["country"] = outliers["country"].map(country_vi)
        outliers["feature"] = outliers["feature"].map(FEATURE_LABELS).fillna(outliers["feature"])
        outliers["classification"] = outliers["classification"].replace({
            "negative_outlier": "Ngoại lệ theo hướng bất lợi", "positive_outlier": "Ngoại lệ theo hướng thuận lợi",
        })
        outliers["economic_direction"] = outliers["economic_direction"].replace({
            "lower_is_better": "Thấp hơn thường tốt hơn", "higher_is_better": "Cao hơn thường tốt hơn",
        })
        outliers = outliers.rename(columns={
            "country_code": "Mã nước", "country": "Quốc gia", "feature": "Đặc trưng", "value": "Giá trị",
            "z_score": "Điểm z", "classification": "Phân loại", "economic_direction": "Chiều diễn giải",
        })
        st.dataframe(outliers.round(2), hide_index=True, width="stretch")

    st.subheader("Đối chiếu tăng trưởng GDP với dữ liệu Ngân hàng Thế giới")
    wb_comparison = add_country_vi(data["wb_comparison"])
    wb_summary = data["wb_summary"].copy()
    wb_summary["country"] = wb_summary["country"].map(country_vi)
    paired = wb_comparison.dropna(subset=["imf_gdp_growth", "world_bank_gdp_growth"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Số cặp quan sát", f"{len(paired)}/100")
    c2.metric("Chênh lệch tuyệt đối bình quân", f"{paired['absolute_difference_pp'].mean():.3f} điểm %")
    c3.metric("Chênh lệch lớn nhất", f"{paired['absolute_difference_pp'].max():.3f} điểm %")
    st.caption(
        "Chỉ tiêu NY.GDP.MKTP.KD.ZG của Ngân hàng Thế giới chỉ dùng để kiểm tra chéo tăng trưởng GDP thực. "
        "Nguồn này không thay thế và không được dùng để lấp dữ liệu IMF còn thiếu."
    )
    left, right = st.columns([1.2, 1])
    with left:
        fig = px.scatter(
            paired, x="world_bank_gdp_growth", y="imf_gdp_growth", color="Quốc gia",
            hover_data={"year": True, "difference_pp": ":.3f"},
            labels={
                "world_bank_gdp_growth": "Tăng trưởng GDP theo Ngân hàng Thế giới (%)",
                "imf_gdp_growth": "Tăng trưởng GDP theo IMF WEO (%)",
            },
        )
        low = min(paired["world_bank_gdp_growth"].min(), paired["imf_gdp_growth"].min())
        high = max(paired["world_bank_gdp_growth"].max(), paired["imf_gdp_growth"].max())
        fig.add_shape(type="line", x0=low, y0=low, x1=high, y1=high, line_dash="dash", line_color="#64748b")
        st.plotly_chart(fig, width="stretch")
    with right:
        wb_summary = wb_summary.rename(columns={
            "country_code": "Mã nước", "country": "Quốc gia", "paired_observations": "Số cặp quan sát",
            "world_bank_missing_years": "Năm WB bị thiếu", "mean_difference_pp": "Chênh lệch bình quân",
            "mean_absolute_difference_pp": "Chênh lệch tuyệt đối bình quân", "max_absolute_difference_pp": "Chênh lệch lớn nhất",
        })
        st.dataframe(wb_summary.round(3), hide_index=True, width="stretch")

    with st.expander("Nguồn gốc dữ liệu và thông tin bộ dữ liệu"):
        metadata_labels = {
            "dataset": "Bộ dữ liệu", "dataset_code": "Mã bộ dữ liệu", "provider": "Đơn vị cung cấp",
            "vintage": "Phiên bản", "retrieved_at": "Ngày truy xuất", "api_family": "Họ API",
            "frequency": "Tần suất", "historical_analysis_period": "Giai đoạn phân tích",
            "countries_count": "Số quốc gia", "indicators_count": "Số chỉ tiêu",
        }
        metadata_table = pd.DataFrame(
            [(metadata_labels.get(key, key), str(value)) for key, value in metadata.items()],
            columns=["Thông tin", "Giá trị"],
        )
        st.dataframe(metadata_table, hide_index=True, width="stretch")
        st.markdown("**Địa chỉ truy vấn IMF SDMX 2.1**")
        st.code(
            "https://api.imf.org/external/sdmx/2.1/data/IMF.RES,WEO,+/"
            "BRN+KHM+IDN+LAO+MYS+MMR+PHL+SGP+THA+VNM."
            "NGDP_RPCH+PCPIPCH+GGXWDG_NGDP+LUR+BCA_NGDPD.A"
            "?startPeriod=2015&endPeriod=2024"
        )
