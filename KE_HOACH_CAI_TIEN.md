# Kế hoạch cải thiện Skill Radar

> Ngày lập: 2026-11-16. Tài liệu nền: [GIAI_THICH_SAU.md](GIAI_THICH_SAU.md).
> Cập nhật trạng thái ở mục 7 sau mỗi giai đoạn.

## 1. Vấn đề hiện tại

| Khía cạnh | Hiện trạng | Hệ quả |
| --- | --- | --- |
| Dashboard | 3 trang, ~4 loại biểu đồ (thanh ngang, đường, sai số, bảng) | Chỉ trả lời một câu hỏi: "tỷ lệ nhắc tới kỹ năng X theo quý" |
| Dữ liệu | Pipeline chỉ giữ 1 con số cho mỗi (kỹ năng, quý). Văn bản 93 nghìn tin và 285 nghìn cặp tin–kỹ năng gần như không được dùng | Phần lớn thông tin trong dữ liệu bị bỏ phí |
| Lưu trữ | Kết quả nằm trong file `radar_manifest.json`, `hn_report.json` và các file `.parquet` rời | Khó truy vấn, khó kiểm tra chéo, không có lược đồ |
| Phân tích | Không có so sánh kỹ năng, quan hệ giữa kỹ năng, ngữ cảnh thị trường | Người xem không hiểu sâu số liệu |

## 2. Dữ liệu sẵn có chưa khai thác

Số liệu từ phép đếm regex thô, sẽ được kiểm chứng kỹ ở giai đoạn 1.

| Chiều | Quan sát nhanh | Câu chuyện |
| --- | --- | --- |
| Remote | 14% (2011) → 83% (2022) → 54% (2026) | COVID đẩy remote lên đỉnh, sau đó giảm |
| Công khai lương | 0,5% → ~21% (2026) | Minh bạch lương tăng mạnh |
| Equity | 4% → ~22% | Văn hóa startup thay đổi |
| Cấp bậc | Tin nhắc senior/staff/lead tăng từ 14% lên ~55%; junior/intern ~3% | Thị trường nghiêng về người có kinh nghiệm |
| Địa điểm | SF ~16%, NYC ~8%, London ~7%; Việt Nam ~0,1% | Nhu cầu tập trung ở Mỹ/châu Âu |
| Đồng xuất hiện | Trung bình 4 kỹ năng mỗi tin | Bản đồ công nghệ và "stack" |
| Nhà tuyển dụng | ~57% tin đến từ tác giả đăng ≥5 lần | Phân tích nhà tuyển dụng lặp lại |

Lưu ý: nhãn ONSITE/REMOTE chỉ trở thành quy ước đăng bài của HN từ khoảng 2015, nên các chỉ số work-mode chỉ so sánh được từ 2015Q3.

## 3. Quyết định kiến trúc: lưu trữ trong cơ sở dữ liệu

Dùng **SQLite** (thư viện chuẩn Python, không phụ thuộc thêm), hai cơ sở dữ liệu theo mô hình medallion:

| Tầng | File | Git | Nội dung |
| --- | --- | --- | --- |
| Bronze + Silver | `skill_radar/data/warehouse.db` | bỏ qua (lớn, có văn bản) | `bronze_comment`, `postings`, `posting_skills`, `posting_features`, `demand_month`, `demand_quarter`, `etl_report` |
| Gold | `skill_radar/data/gold.db` | theo dõi (nhỏ) | Bảng dự báo, lịch sử, backtest, lead-lag, bảng phân tích cho dashboard (xem mục 5) |

- Không còn `radar_manifest.json`: kết quả backtest, kiểm chứng hướng, lead-lag được chuẩn hóa thành bảng quan hệ.
- File `.json.gz` tải từ API chỉ còn là bộ nhớ đệm tải xuống; dữ liệu thô được nạp vào bảng `bronze_comment`.
- Dashboard chỉ đọc `gold.db`.

## 4. Dashboard mới (6 trang)

1. **Tổng quan**: thẻ KPI, "điểm nổi bật" tự sinh từ dữ liệu, treemap kỹ năng theo nhóm, cơ cấu lượt nhắc theo nhóm (vùng xếp chồng 100%), bump chart xếp hạng.
2. **Xu hướng**: heatmap kỹ năng × năm, dumbbell chart so sánh hai năm, bong bóng "mức hiện tại × động lượng" chia 4 góc phần tư, đường so sánh có chuẩn hóa và chú thích sự kiện.
3. **Hồ sơ kỹ năng**: một kỹ năng, mọi góc nhìn: lịch sử + dự báo (quạt), xếp hạng theo thời gian, tỷ lệ remote/lương/cấp bậc, kỹ năng hay đi kèm.
4. **Hệ sinh thái**: bản đồ công nghệ (cụm + cạnh), ma trận lift, kỹ năng đi kèm một kỹ năng.
5. **Skill Navigator**: chọn kỹ năng đã biết → % tin phù hợp, gợi ý kỹ năng tiếp theo làm tăng độ phủ nhiều nhất.
6. **Dự báo & độ tin cậy**: dự báo toàn bộ, thực tế so với dự đoán trên holdout, ma trận nhầm lẫn của nhãn hướng, sai số theo kỳ hạn, tín hiệu cộng đồng (npm/Stack Overflow) và lead-lag.

## 5. Bảng Gold mới

`skills`, `radar_series`, `radar_paths`, `radar_history`, `demand_quarter`, `posting`, `posting_skill`, `market_quarter`, `city_year`, `skill_year`, `skill_pair_year`, `skill_attr_year`, `employer`, `skill_cluster`, `events`, `signal_npm_month`, `signal_se_quarter`, `backtest_cell`, `run_info`, `model_score`, `model_horizon_error`, `label_score`, `selection_score`, `leadlag`, `leadlag_skill`.

## 6. Phân tích và mô hình bổ sung

| Hạng mục | Mô tả | Giai đoạn |
| --- | --- | --- |
| Trích xuất đặc trưng tin | remote/onsite/hybrid, lương (USD/năm), equity, cấp bậc, visa, loại hợp đồng, thành phố, nhà tuyển dụng | 1 |
| Đồng xuất hiện | Số tin chứa cả A và B theo năm, tính lift và xác suất có điều kiện | 1 |
| Phân cụm kỹ năng | Phân cụm phân cấp trên PPMI của đồng xuất hiện + tọa độ 2D (SpectralEmbedding) | 3 |
| Skill Navigator | Tham lam trên ma trận tin × kỹ năng | 2 |
| Topic modeling (NMF) | Rút "vai trò" từ văn bản | 3 (chưa làm) |
| Change-point | Phát hiện điểm gãy trong chuỗi kỹ năng | 3 (chưa làm) |
| Gán nhãn tay 200–300 tin | Đo precision/recall của bộ nhận diện kỹ năng | 3 (cần người gán nhãn) |
| Dự báo theo nhóm kỹ năng | Chuỗi gộp ít nhiễu hơn; báo cáo trung thực dù có thắng baseline hay không | 3 (chưa làm) |
| Hoàn tất Stack Overflow | Cần `SE_API_KEY` của người dùng | chờ khóa |

Không dùng Spark: dữ liệu 46 MB, không cần. GitHub Archive (~17 GB) là phần duy nhất thật sự cần công nghệ dữ liệu lớn nếu sau này làm.

## 7. Lộ trình và trạng thái (cập nhật 2026-11-16)

| GĐ | Nội dung | Tiêu chí rubric | Trạng thái |
| --- | --- | --- | --- |
| 1 | Cơ sở dữ liệu (warehouse + gold), trích xuất đặc trưng, bảng phân tích, test | Xử lý dữ liệu 20% | ✅ xong |
| 2 | Dashboard 6 trang + Skill Navigator (trang Thị trường đã bỏ theo yêu cầu, 2026-11-17) | Trực quan hóa/ứng dụng 25% | ✅ xong |
| 3a | Phân cụm kỹ năng (Ward trên PPMI, k chọn theo silhouette có ràng buộc kích thước, bố cục t-SNE) | Mô hình/công nghệ 25% | ✅ xong |
| 3d | Phân tích "vì sao tăng/giảm" (bước ngoặt, shift-share, độ rộng nhà tuyển dụng, đồng biến, mô hình dựa vào gì) | Mô hình/công nghệ 25% | ✅ xong (2026-11-16, `drivers.py`) |
| 3b | Topic model (NMF), bước ngoặt đã làm ở 3d; còn lại: gán nhãn tay 200–300 tin, dự báo theo nhóm kỹ năng | Mô hình/công nghệ 25% | ⬜ chưa làm |
| 3c | Hoàn tất Stack Overflow (cần `SE_API_KEY` của người dùng) | Mô hình/công nghệ 25% | ⬜ chờ khóa |
| 4 | Cập nhật báo cáo (`PROJECT_REPORT.md`), ảnh chụp màn hình, phân công nhóm | Báo cáo 10% | ⬜ chưa làm |

### Ghi chú khi thực hiện
- Dữ liệu gốc khớp bản cũ: 93.354 tin, 71.571 tin có kỹ năng, 79.180 tin trong cửa sổ mô hình 2015Q3–2026Q3.
- Kết quả dự báo giữ nguyên. F1 nhãn hướng đổi từ 0,4662 sang 0,4672 và khoảng tin cậy dịch nhẹ do khác biệt môi trường; chạy lại hai lần cho kết quả giống hệt nhau. Mọi kết luận không đổi.
- Phân cụm: ban đầu chọn k theo silhouette thuần cho ra một cụm khổng lồ (62/68 kỹ năng) và vài cụm 1–3 kỹ năng. Đã sửa bằng Ward + ràng buộc mỗi cụm có 5 đến 35% số kỹ năng. Kết quả 6 cụm dễ hiểu nhưng silhouette chỉ 0,15: cụm là gợi ý, không phải ranh giới cứng (đã ghi trên dashboard).
- Các chỉ số mới (remote, lương, cấp bậc…) là đếm theo regex; "công khai lương" bắt thiếu các định dạng lạ, "senior" có thể nhầm vài trường hợp. Chưa đo precision/recall (việc gán nhãn tay ở GĐ 3b).

## 8. Nguyên tắc giữ nguyên

- Kết quả trung thực: báo cáo cả kết quả âm tính (tín hiệu cộng đồng chưa chứng minh đi trước).
- Quy trình backtest đặt trước (chọn mô hình đến 2022Q4, chấm holdout 2023–2026 một lần) không đổi.
- Mọi chỉ số mới là thống kê mô tả; chỉ nhãn hướng đã kiểm chứng mới được gọi là "dự báo đã kiểm chứng".
