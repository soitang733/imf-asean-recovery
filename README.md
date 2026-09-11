# Phục hồi kinh tế hậu COVID-19 của ASEAN-10

Pipeline Python phân tích IMF World Economic Outlook (WEO), vintage April 2026, cho ASEAN-10. IMF SDMX 2.1 API là nguồn dữ liệu duy nhất của dataset phân tích chính; DataMapper không được sử dụng.

Dashboard được trình bày hoàn toàn bằng tiếng Việt và thiết kế theo lối kể chuyện dành cho cả người chưa có nền tảng kinh tế hoặc phân tích dữ liệu. Luồng đọc gồm: hiểu bài toán trong một phút, xem kết luận chính, khám phá từng quốc gia, nhận diện các đánh đổi, rồi kiểm tra nguồn dữ liệu và phương pháp.

Mỗi kết quả định lượng trên dashboard được tạo từ dữ liệu đang nạp, kèm bảng bằng chứng, mã chỉ tiêu IMF và công thức tính. Các con số không được nhập cứng vào phần trình bày; khi dữ liệu đầu vào thay đổi, bằng chứng hiển thị cũng thay đổi theo.

**Deploy Streamlit Cloud:** repo `soitang733/imf-asean-recovery`, entrypoint `streamlit_app.py`, branch `main`.

## Phạm vi dữ liệu

- Provider và dataset: `IMF.RES,WEO,+` (`+` chọn latest vintage, hiện là April 2026).
- Tần suất: Annual (`A`).
- Quốc gia: `BRN+KHM+IDN+LAO+MYS+MMR+PHL+SGP+THA+VNM`.
- Chỉ tiêu: `NGDP_RPCH+PCPIPCH+GGXWDG_NGDP+LUR+BCA_NGDPD`.
- Giai đoạn phân tích: 2015–2024; không tải 2025–2026.
- Định dạng raw: SDMX 2.1 structure-specific XML.

```text
IMF SDMX 2.1 XML
→ lưu nguyên phản hồi raw
→ parse Series và Obs
→ country × indicator × year grid
→ giữ NA, không nội suy và không lấy nguồn khác để lấp thiếu
→ coverage, features, outliers, clustering, stories và figures
```

## Cài đặt và chạy

```powershell
cd D:\stock_analysis-main\imf_asean_resilience
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_pipeline.py --force-download
python run_crosscheck.py --force-download
pytest -q
streamlit run app.py
```

Bỏ `--force-download` để tái chạy từ phản hồi XML đã lưu mà không gọi mạng.

## API chính

```text
https://api.imf.org/external/sdmx/2.1/data/IMF.RES,WEO,+/BRN+KHM+IDN+LAO+MYS+MMR+PHL+SGP+THA+VNM.NGDP_RPCH+PCPIPCH+GGXWDG_NGDP+LUR+BCA_NGDPD.A?startPeriod=2015&endPeriod=2024
```

Header yêu cầu XML:

```text
Accept: application/vnd.sdmx.structurespecificdata+xml;version=2.1
```

Parser đọc `COUNTRY`, `INDICATOR`, `FREQUENCY` tại cấp Series và `TIME_PERIOD`, `OBS_VALUE` tại cấp Obs. File sạch có đúng các trường:

```text
country_code,country,year,indicator_code,indicator_name,value,frequency
```

## Tệp dữ liệu chính

- `data/raw_imf_weo.xml`: nguyên phản hồi API.
- `data/clean_imf_weo.csv`: full grid 10 × 5 × 10; quan sát IMF không có được giữ là NA.
- `data/metadata.json`: metadata của lần lấy dữ liệu.
- `data/crawl_audit.json`: checksum và kết quả kiểm tra crawl lại, gồm các truy vấn LUR tách riêng.
- `data/raw_imf_weo_sdmx3.json`: response SDMX 3.0 dùng để đối chiếu; không thay thế nguồn SDMX 2.1 chính vì coverage 2015–2024 giống nhau.
- `data/crosscheck/raw_world_bank_gdp_growth.json`: phản hồi World Bank Indicators API cho `NY.GDP.MKTP.KD.ZG`.
- `data/crosscheck/imf_worldbank_gdp_growth_comparison.csv`: đối chiếu IMF–World Bank theo country × year.
- `data/crosscheck/imf_worldbank_gdp_growth_summary.csv`: MAE và chênh lệch lớn nhất theo quốc gia.
- `outputs/data_coverage.csv`: coverage theo country × indicator.
- `data/country_features.csv`: biến phân tích dẫn xuất.
- `outputs/data_coverage.csv`, `outputs/outliers.csv` và `outputs/candidate_stories.csv`: đầu ra kiểm tra và phân tích đã lưu.
- `docs/report_vi.md`: báo cáo diễn giải tiếng Việt đã đối chiếu với dữ liệu.

## Kiến trúc mã

- `src/config.py`: provider, dataset, vintage, ASEAN-10, 5 indicators và 2015–2024.
- `src/data.py`: URL, tải XML, parse, full grid, coverage, raw preservation và metadata.
- `src/features.py`: baseline, COVID shock, recovery và cost metrics.
- `src/outliers.py`, `src/clustering.py`, `src/story_mining.py`: phân tích khám phá.
- `src/visualization.py`: bảy hình chính.
- `src/pipeline.py`: điều phối và tạo báo cáo.
- `app.py`: dashboard Streamlit theo luồng executive overview → country lens → trade-offs → patterns → method & QA.
- `docs/design_review.md`: các nguyên tắc thiết kế học từ bài tham khảo và cách chuyển sang đề tài IMF.

Clustering chỉ dùng các đặc trưng có coverage đầy đủ cho cả ASEAN-10; không điền giá trị thiếu. Nhãn recovery profile là so với trung vị của mẫu, không đồng nghĩa recovery gap dương.
Dashboard tính lại ranking và clustering trực tiếp từ `data/country_features.csv`, nên repository không giữ các CSV ranking/clustering cũ có thể gây nhầm lẫn. Chạy pipeline đầy đủ sẽ tái tạo các output này bằng logic hiện hành.

World Bank chỉ là lớp kiểm tra chéo cho tăng trưởng GDP thực. Pipeline không ghi giá trị World Bank vào `clean_imf_weo.csv`, không dùng nó để lấp `LUR`, và không thay đổi nguồn chính IMF WEO SDMX 2.1.

WEO April 2026 có `PUBLICATION_DATE=2026-04-14` trong SDMX response. Số version kỹ thuật bên trong dataflow vẫn có thể được IMF biểu diễn riêng; URL dùng `+` để tránh khóa pipeline vào một version cũ.
