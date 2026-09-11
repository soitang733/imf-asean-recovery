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
    "recovery_growth": "Tăng trưởng bình quân 2021–2024",
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
        "title": "Cú sốc tăng trưởng tương đồng và sự phân hóa trong giai đoạn phục hồi",
        "interpretation": "Mặc dù mức suy giảm tăng trưởng năm 2020 có quy mô gần tương đương, hai nền kinh tế ghi nhận khoảng cách phục hồi khác biệt đáng kể trong giai đoạn 2021–2024.",
        "alternative": "Sự khác biệt có thể liên quan đến cơ cấu ngành, thời điểm tái mở cửa, hiệu ứng mức nền và quy mô hỗ trợ chính sách.",
        "limitation": "Kết quả là bằng chứng mô tả và không cho phép xác định yếu tố gây ra sự phân hóa.",
    },
    "Strong recovery with a high inflation bill": {
        "title": "Phục hồi tăng trưởng và sự gia tăng áp lực lạm phát",
        "interpretation": "Khoảng cách phục hồi dương và mức lạm phát cao hơn đường cơ sở được ghi nhận đồng thời trong giai đoạn quan sát.",
        "alternative": "Biến động giá lương thực, năng lượng và các cú sốc cung toàn cầu có thể tác động đến lạm phát độc lập với cầu trong nước.",
        "limitation": "Sự đồng diễn biến giữa hai chỉ tiêu không cấu thành bằng chứng về quan hệ nhân quả.",
    },
    "Debt rose while recovery stayed weak": {
        "title": "Gia tăng nợ công và phục hồi tăng trưởng hạn chế",
        "interpretation": "Trong phạm vi thống kê mô tả, mức tăng của tỷ lệ nợ công đồng thời xuất hiện với khoảng cách phục hồi âm.",
        "alternative": "Biến động tỷ giá, phạm vi ghi nhận nợ, hiệu ứng mẫu số GDP và các cú sốc đặc thù quốc gia có thể ảnh hưởng đến kết quả.",
        "limitation": "Chỉ tiêu nợ công gộp không phản ánh nợ ròng hoặc đầy đủ bảng cân đối tài sản của khu vực chính phủ.",
    },
    "Recovery with contained inflation and debt costs": {
        "title": "Phục hồi tăng trưởng trong điều kiện áp lực lạm phát và nợ tương đối thấp",
        "interpretation": "Trên các chiều đo được lựa chọn, Brunei ghi nhận tổ hợp kết quả tương đối thuận lợi so với phân bố của mẫu ASEAN-10.",
        "alternative": "Giá hàng hóa, thay đổi của mẫu số GDP và vị thế tài khóa ban đầu có thể ảnh hưởng đến các chỉ tiêu quan sát.",
        "limitation": "Kết luận chỉ có ý nghĩa tương đối trong phạm vi mẫu và giai đoạn nghiên cứu, không phải thước đo tổng quát về khả năng chống chịu.",
    },
    "ASEAN's clearest statistical outlier": {
        "title": "Ngoại lệ thống kê về mức độ biến động tăng trưởng sau dịch",
        "interpretation": "Mức độ biến động tăng trưởng của Myanmar lệch đáng kể so với trung bình của mẫu ASEAN-10 theo tiêu chuẩn điểm z.",
        "alternative": "Đặc điểm cơ cấu, các biến cố trong nước và khác biệt về quy ước đo lường có thể đóng góp vào độ lệch quan sát được.",
        "limitation": "Với cỡ mẫu 10 quốc gia, điểm z nhạy với từng quan sát và không nên được xem là bằng chứng độc lập về bất thường cấu trúc.",
    },
    "Positive growth, but still below the old baseline": {
        "title": "Tăng trưởng dương nhưng thấp hơn đường cơ sở trước đại dịch",
        "interpretation": "Việc tăng trưởng trở lại mức dương không đồng nghĩa tốc độ tăng trưởng trung bình đã trở về đường cơ sở 2015–2019.",
        "alternative": "Mức tăng trưởng trước đại dịch có thể chịu hiệu ứng chu kỳ hoặc cao hơn mức có thể duy trì trong dài hạn.",
        "limitation": "Giá trị bình quân theo giai đoạn có thể che khuất biến động và các điểm ngoặt trong từng năm.",
    },
    "Growth recovery without equal labor-market improvement": {
        "title": "Sự khác biệt giữa phục hồi tăng trưởng và điều chỉnh của thị trường lao động",
        "interpretation": "Tăng trưởng GDP và tỷ lệ thất nghiệp không nhất thiết điều chỉnh đồng thời hoặc với cùng mức độ.",
        "alternative": "Thay đổi tỷ lệ tham gia lực lượng lao động, cơ cấu việc làm và độ trễ điều chỉnh có thể ảnh hưởng đến tỷ lệ thất nghiệp.",
        "limitation": "WEO không cung cấp chuỗi thất nghiệp đầy đủ cho toàn bộ ASEAN-10, do đó khả năng so sánh khu vực bị hạn chế.",
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


def story_evidence(
    row: pd.Series,
    feature_data: pd.DataFrame,
    outlier_data: pd.DataFrame,
) -> tuple[str, pd.DataFrame]:
    """Build every quantitative claim from the loaded analytical outputs."""
    title = row["title"]
    indexed = feature_data.set_index("country_code")
    records: list[dict[str, object]] = []

    def value(code: str, feature: str) -> float:
        return float(indexed.loc[code, feature])

    def add(code: str, feature: str, indicator: str, formula: str) -> None:
        records.append(
            {
                "Quốc gia": country_vi(indexed.loc[code, "country"]),
                "Biến phân tích": FEATURE_LABELS.get(feature, feature),
                "Giá trị": value(code, feature),
                "Chỉ tiêu IMF gốc": indicator,
                "Phương pháp tính": formula,
            }
        )

    if title == "Similar COVID shock, different recovery":
        for code in ("LAO", "SGP"):
            add(code, "covid_shock", "NGDP_RPCH", "Tăng trưởng 2020 − bình quân 2015–2019")
            add(code, "recovery_gap", "NGDP_RPCH", "Bình quân 2021–2024 − bình quân 2015–2019")
        evidence = (
            f"Cú sốc tăng trưởng năm 2020 của Lào và Singapore lần lượt là {value('LAO', 'covid_shock'):.2f} và "
            f"{value('SGP', 'covid_shock'):.2f} điểm phần trăm. Trong giai đoạn 2021–2024, khoảng cách phục hồi "
            f"ước tính của Lào là {value('LAO', 'recovery_gap'):+.2f} điểm, trong khi Singapore ghi nhận "
            f"{value('SGP', 'recovery_gap'):+.2f} điểm."
        )
    elif title == "Strong recovery with a high inflation bill":
        add("SGP", "recovery_gap", "NGDP_RPCH", "Bình quân 2021–2024 − bình quân 2015–2019")
        add("SGP", "inflation_cost", "PCPIPCH", "Lạm phát bình quân 2021–2024 − bình quân 2015–2019")
        evidence = (
            f"Singapore ghi nhận khoảng cách phục hồi {value('SGP', 'recovery_gap'):+.2f} điểm phần trăm. "
            f"Chênh lệch giữa lạm phát bình quân giai đoạn 2021–2024 và đường cơ sở 2015–2019 là "
            f"{value('SGP', 'inflation_cost'):+.2f} điểm."
        )
    elif title == "Debt rose while recovery stayed weak":
        add("MMR", "debt_cost", "GGXWDG_NGDP", "Nợ công năm 2024 − nợ công năm 2019")
        add("MMR", "recovery_gap", "NGDP_RPCH", "Bình quân 2021–2024 − bình quân 2015–2019")
        evidence = (
            f"Tỷ lệ nợ công gộp của Myanmar năm 2024 cao hơn năm 2019 "
            f"{value('MMR', 'debt_cost'):+.2f} điểm phần trăm GDP. Trong cùng phạm vi phân tích, "
            f"khoảng cách phục hồi tăng trưởng được ước tính ở mức {value('MMR', 'recovery_gap'):+.2f} điểm."
        )
    elif title == "Recovery with contained inflation and debt costs":
        add("BRN", "recovery_gap", "NGDP_RPCH", "Bình quân 2021–2024 − bình quân 2015–2019")
        add("BRN", "inflation_cost", "PCPIPCH", "Lạm phát bình quân 2021–2024 − bình quân 2015–2019")
        add("BRN", "debt_cost", "GGXWDG_NGDP", "Nợ công năm 2024 − nợ công năm 2019")
        evidence = (
            f"Brunei ghi nhận khoảng cách phục hồi {value('BRN', 'recovery_gap'):+.2f} điểm. Chênh lệch lạm phát "
            f"bình quân so với đường cơ sở là {value('BRN', 'inflation_cost'):+.2f} điểm, trong khi tỷ lệ nợ công thay đổi "
            f"{value('BRN', 'debt_cost'):+.2f} điểm phần trăm GDP."
        )
    elif title == "ASEAN's clearest statistical outlier":
        outlier = outlier_data[
            (outlier_data["country_code"] == "MMR")
            & (outlier_data["feature"] == "growth_volatility_post")
        ].iloc[0]
        records.append(
            {
                "Quốc gia": "Myanmar",
                "Biến phân tích": "Biến động tăng trưởng sau dịch",
                "Giá trị": float(outlier["value"]),
                "Chỉ tiêu IMF gốc": "NGDP_RPCH",
                "Phương pháp tính": f"Độ lệch chuẩn 2021–2024; điểm z = {float(outlier['z_score']):.2f}",
            }
        )
        evidence = (
            f"Độ lệch chuẩn của tăng trưởng Myanmar trong giai đoạn 2021–2024 là {float(outlier['value']):.2f}. "
            f"Điểm z tương ứng đạt {float(outlier['z_score']):.2f}, vượt ngưỡng nhận diện ngoại lệ |z| ≥ 2."
        )
    elif title == "Positive growth, but still below the old baseline":
        add("LAO", "recovery_growth", "NGDP_RPCH", "Tăng trưởng bình quân 2021–2024")
        add("LAO", "recovery_gap", "NGDP_RPCH", "Bình quân 2021–2024 − bình quân 2015–2019")
        evidence = (
            f"Tăng trưởng GDP thực bình quân của Lào đạt {value('LAO', 'recovery_growth'):.2f}% trong giai đoạn "
            f"2021–2024. So với đường cơ sở 2015–2019, khoảng cách phục hồi là "
            f"{value('LAO', 'recovery_gap'):+.2f} điểm phần trăm."
        )
    elif title == "Growth recovery without equal labor-market improvement":
        add("SGP", "recovery_gap", "NGDP_RPCH", "Bình quân 2021–2024 − bình quân 2015–2019")
        add("SGP", "unemployment_change", "LUR", "Thất nghiệp bình quân 2021–2024 − bình quân 2015–2019")
        evidence = (
            f"Singapore ghi nhận khoảng cách phục hồi {value('SGP', 'recovery_gap'):+.2f} điểm. Chênh lệch tỷ lệ "
            f"thất nghiệp bình quân giữa giai đoạn 2021–2024 và đường cơ sở 2015–2019 là "
            f"{value('SGP', 'unemployment_change'):+.2f} điểm phần trăm."
        )
    else:
        evidence = str(row["evidence"])

    return evidence, pd.DataFrame(records)


def story_card(row: pd.Series, feature_data: pd.DataFrame, outlier_data: pd.DataFrame) -> str:
    story = story_content(row)
    evidence, _ = story_evidence(row, feature_data, outlier_data)
    countries = ", ".join(country_vi(name.strip()) for name in str(row["countries_involved"]).split(";"))
    return (
        '<div class="story-card">'
        f"<h4>{story['title']}</h4>"
        f"<p><strong>{countries}</strong></p>"
        f"<p>{evidence}</p>"
        '<p class="small-note"><strong>Nguồn dữ liệu:</strong> IMF WEO tháng 4/2026 · giai đoạn 2015–2024</p>'
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
            "1. **Đọc Tổng quan** để nắm các kết quả chính.\n\n"
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
    ["Tổng quan", "Từng quốc gia", "Các đánh đổi", "Kết quả phân tích", "Dữ liệu & phương pháp"]
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

    st.subheader("Ba kết quả định lượng nổi bật")
    story_columns = st.columns(3)
    for column, (_, row) in zip(story_columns, data["stories"].head(3).iterrows()):
        column.markdown(story_card(row, features, data["outliers"]), unsafe_allow_html=True)

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
        st.caption("Thuật toán phân nhóm các quốc gia có đặc trưng định lượng tương đồng; kết quả mang tính khám phá và không cấu thành bảng xếp hạng.")
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
        st.subheader("Các kết quả định lượng đáng chú ý")
        for index, row in data["stories"].iterrows():
            story = story_content(row)
            evidence, evidence_table = story_evidence(row, features, data["outliers"])
            countries = ", ".join(country_vi(name.strip()) for name in str(row["countries_involved"]).split(";"))
            with st.expander(f"{index + 1}. {story['title']}", expanded=index < 2):
                st.markdown(f"**Phạm vi quan sát:** {countries}")
                st.markdown(f"**Bằng chứng định lượng:** {evidence}")
                st.dataframe(
                    evidence_table.style.format({"Giá trị": "{:+.2f}"}),
                    hide_index=True,
                    width="stretch",
                )
                st.caption(
                    "Nguồn: IMF World Economic Outlook, phiên bản tháng 4/2026. Các đại lượng dẫn xuất được "
                    "tính từ chuỗi quan sát 2015–2024 trong data/clean_imf_weo.csv và được lưu tại "
                    "data/country_features.csv để bảo đảm khả năng tái lập."
                )
                st.markdown(f"**Diễn giải thống kê:** {story['interpretation']}")
                st.markdown(f"**Các yếu tố giải thích thay thế:** {story['alternative']}")
                st.markdown(f"**Giới hạn suy luận:** {story['limitation']}")

with tab_method:
    st.subheader("Dữ liệu được xử lý như thế nào?")
    st.caption("Toàn bộ quy trình có thể kiểm tra và chạy lại từ phản hồi gốc của IMF.")
    steps = [
        ("1 · Thu thập", "IMF SDMX 2.1", "Giữ nguyên phản hồi XML gốc"),
        ("2 · Đọc dữ liệu", "Chuỗi và quan sát", "Tạo đủ khung 500 dòng"),
        ("3 · Kiểm tra", "Trùng lặp và thiếu", "Độ phủ theo nước × chỉ tiêu"),
        ("4 · Tính toán", "Cú sốc và phục hồi", "Công thức minh bạch"),
        ("5 · Khám phá", "Ngoại lệ và phân nhóm", "Tổng hợp kết quả"),
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
        st.markdown("**Ngoại lệ thống kê theo ngưỡng |z| ≥ 2**")
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
