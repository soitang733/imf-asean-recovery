# Phục hồi hậu COVID của ASEAN-10: dữ liệu IMF cho thấy điều gì?

## Câu hỏi nghiên cứu

Phân tích sử dụng IMF World Economic Outlook, vintage April 2026, để xem xét ba câu hỏi: nền kinh tế nào lấy lại tốc độ tăng trưởng trước COVID-19, quá trình phục hồi đi cùng thay đổi nào về lạm phát và nợ công, và các quốc gia có tạo thành những nhóm hành vi tương tự hay không. Kết quả chỉ mô tả các biến động diễn ra đồng thời, không xác lập quan hệ nhân quả.

## Dữ liệu và cách xử lý thiếu dữ liệu

Dataset gồm 10 nước ASEAN, 5 chỉ tiêu và 10 năm từ 2015 đến 2024, tương ứng 500 vị trí trong lưới country × indicator × year. IMF cung cấp 470 quan sát, đạt coverage 94%. Toàn bộ 30 giá trị thiếu thuộc chỉ tiêu thất nghiệp (`LUR`) của Campuchia, Lào và Myanmar.

Các giá trị này được giữ là `NA`. Pipeline không nội suy, không lấy nguồn khác để lấp và không đưa `LUR` vào phân cụm vì chỉ tiêu này không có coverage đầy đủ cho ASEAN-10. Phân tích thất nghiệp riêng chỉ sử dụng bảy quốc gia có quan sát hợp lệ.

Tăng trưởng GDP thực được kiểm tra chéo với chỉ tiêu `NY.GDP.MKTP.KD.ZG` của World Bank cho đủ 100 cặp country × year. World Bank chỉ dùng để đánh giá mức độ nhất quán giữa hai nguồn; dữ liệu này không ghi đè dataset IMF và không được dùng để lấp bất kỳ giá trị thiếu nào.

## Kết quả chính

### Cùng mức sốc, tốc độ phục hồi khác nhau

Lào và Singapore có mức giảm tốc tăng trưởng năm 2020 khá gần nhau, lần lượt -6,85 và -6,72 điểm phần trăm so với baseline 2015–2019. Tuy nhiên, tăng trưởng trung bình 2021–2024 của Singapore cao hơn baseline 2,12 điểm phần trăm, trong khi Lào thấp hơn baseline 3,35 điểm phần trăm. Dữ liệu cho thấy hai quỹ đạo phục hồi khác nhau nhưng không đủ để xác định nguyên nhân.

### Phục hồi và lạm phát

Singapore có recovery gap cao nhất mẫu, +2,12 điểm phần trăm, đồng thời có inflation cost +3,81 điểm phần trăm. Đây là quan hệ đồng thời trong dữ liệu. Không thể từ đó kết luận phục hồi gây ra lạm phát; giá lương thực, năng lượng và các yếu tố cung toàn cầu có thể cùng tác động.

### Nợ tăng nhưng phục hồi yếu

Myanmar có recovery gap thấp nhất, -8,31 điểm phần trăm, trong khi nợ chính phủ gộp tăng 13,02 điểm phần trăm GDP từ 2019 đến 2024. Chỉ tiêu sử dụng là gross debt, không phải net debt, nên cần thận trọng khi so sánh giữa các thể chế tài khóa khác nhau.

## So sánh theo từng khía cạnh

| Quốc gia | Cú sốc 2020 | Recovery gap | Inflation cost | Debt cost (pp GDP) |
|---|---:|---:|---:|---:|
| Singapore | -6,72 | +2,12 | +3,81 | +38,36 |
| Malaysia | -10,36 | +0,34 | +0,62 | +12,76 |
| Brunei Darussalam | +0,66 | +0,01 | +1,62 | -0,25 |
| Indonesia | -7,10 | -0,26 | -1,03 | +9,60 |
| Philippines | -16,10 | -0,45 | +2,24 | +19,65 |
| Thailand | -9,51 | -1,06 | +1,89 | +21,85 |
| Vietnam | -4,22 | -1,31 | +0,33 | -9,83 |
| Campuchia | -10,64 | -2,82 | +0,49 | +4,90 |
| Lào | -6,85 | -3,35 | +18,46 | +25,55 |
| Myanmar | -15,35 | -8,31 | +16,06 | +13,02 |

Ba nước có recovery gap dương là Singapore, Malaysia và Brunei Darussalam. Bảy nước còn lại có tốc độ tăng trưởng trung bình 2021–2024 thấp hơn baseline trước dịch. Nhãn profile trên dashboard dùng cụm từ “trên trung vị” và “dưới trung vị”, không dùng “phục hồi cao” và “phục hồi thấp”, vì Indonesia và Philippines nằm trên trung vị của mẫu dù recovery gap vẫn âm.

## Phân cụm

Pipeline so sánh KMeans và hierarchical clustering với k từ 2 đến 5. Các đặc trưng đầu vào chỉ gồm những biến có coverage đầy đủ cho cả 10 nước; không có bước điền giá trị thiếu. Nghiệm có silhouette cao nhất tạo một cụm chỉ gồm Brunei và một cụm gồm chín nước còn lại.

Một cụm đơn lẻ có thể phản ánh outlier hơn là một nhóm kinh tế ổn định. Vì mọi nghiệm được thử đều có ít nhất một cụm chỉ gồm một quốc gia, kết quả phân cụm chỉ nên được xem là khám phá. Nhóm chín nước được ghi là “các nền kinh tế ASEAN còn lại, có tính không đồng nhất”, thay vì gán nhãn “chi phí thấp, ít biến động”.

## Điểm bất thường

Các outlier đáng chú ý gồm độ biến động tăng trưởng hậu COVID và recovery gap của Myanmar, mức giảm thất nghiệp của Brunei, cùng inflation cost và thay đổi cán cân vãng lai của Lào. Với mẫu chỉ 10 quốc gia, z-score nhạy với từng quan sát và chỉ nên dùng để xác định trường hợp cần xem xét thêm.

## Giới hạn

- IMF có thể điều chỉnh lại số liệu WEO trong các vintage sau.
- Phân tích chỉ dùng 2015–2024 và không trộn dự báo 2025–2026.
- Thiếu dữ liệu thất nghiệp làm giảm khả năng so sánh Campuchia, Lào và Myanmar trên thị trường lao động.
- Gross debt không tương đương net debt; Singapore là trường hợp cần đọc cùng bối cảnh thể chế.
- Trung bình theo giai đoạn có thể che khuất biến động từng năm và hiệu ứng nền.
- Clustering và outlier trên mẫu 10 nước không nên được diễn giải như bằng chứng nhân quả hoặc dự báo.
