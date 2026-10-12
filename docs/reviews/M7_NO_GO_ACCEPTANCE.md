# Hồ sơ đề xuất nghiệm thu M7 — nhánh NO-GO có bằng chứng

**Ngày lập:** 13/10/2026

**Trạng thái:** sẵn sàng để nhóm/giảng viên xét nghiệm thu nhánh `NO-GO`; **chưa tự nhận M7 đã nghiệm thu**. M6 và nhánh huấn luyện/công bố mô hình của M7 vẫn bị chặn.

## 1. Quyết định và phạm vi

[Final Plan, Phase 7](../../FINAL_PLAN_BigData_IT_Job_Market_Skill_Forecasting.md#phase-7--trend-prediction) cho phép M7 kết thúc bằng “Forecast Model Ready **hoặc NO-GO có bằng chứng**”. Cổng dự báo của run hiện hành trả `NO_GO` / `Insufficient evidence`. Hồ sơ này cung cấp bằng chứng cho **nhánh thứ hai**; không có nhãn `t+1`, thí nghiệm A/B/C/D, metric mô hình hay dự báo Growing/Stable/Declining.

Đầu ra máy đọc được: [m7_no_go_dossier.json](../data/m7_no_go_dossier.json), sinh bằng `python -m src.analytics.m7_no_go_dossier`. Generator chỉ đọc [audit Phase 03](../data/phase03_analytics_audit.json) và [quyết định GO/NO-GO hiện hành](../planning/go_no_go_report.md). Nó từ chối audit bị đổi sang `GO`, chính sách đã đổi SHA, mất gate check/ngưỡng hoặc thêm output prediction.

| Khóa bằng chứng | Giá trị |
|---|---|
| SHA-256 audit Phase 03 | `4655c11eb24ec1f51fac66f6449c22dc1aa28cc2828c486bca00737cfd4b210f` |
| Gold run / manifest SHA-256 | `20261004T110131548191Z-e38fa7303cf4` / `2b37892022882e834b5437555c5c567aa2ab31103dc1d581b9b2f18cd9e7c74d` |
| ETL run | `8c8a0ca26b38404a96a9b97fa8fd6e02` |
| Taxonomy | `v0.1`; chưa có kiểm định trên tập nhãn độc lập |
| SHA-256 chính sách GO/NO-GO | `f4766fe6b7fcb5ee2e8c6032a1658e378283e8c8b51286051e15dc59645222e8` |
| SHA-256 dossier này ở dạng JSON | `a7b946777249e0639b0c534ace89b201d28f8eb6fa748589492e543399a5f00e` |

Audit được tạo từ **785.741** dòng archive 2023 và **666** tin fresh có trạng thái `partial`: ETL local ra **786.300** Silver/provenance 1:1. Gold có năm bảng mô tả, trong đó `skill_stats` và `skill_trends` mỗi bảng **4.538** dòng. Dossier giữ các hash bảng Gold để người kiểm tra lần theo đúng run; Parquet lớn vẫn là artifact local ngoài Git. Xem [báo cáo Phase 03](PHASE_03_ANALYTICS_REPORT.md) cho số dòng, checksum và giới hạn chi tiết.

## 2. Ma trận bằng chứng theo Final Plan mục 16–21

| Điều kiện | Bằng chứng từ audit hiện tại | Trạng thái |
|---|---|---|
| Quyết định chính sách | GO/NO-GO report còn `NO-GO` cho predictive claims; SHA trùng audit. | **FAIL** |
| Liên tục lịch | 12 tháng archive năm 2023; API chỉ có 2026-09/10. Có **32 tháng không quan sát** giữa 2023-01 và 2026-10, gồm 2024–2025. Khoảng trống là thiếu quan sát, không phải demand bằng 0. | **FAIL** |
| Khả năng so sánh nguồn | Không có tháng quan sát chung giữa archive và API; archive dùng `source_tags`, API dùng `extracted_from_jd`; chưa hiệu chỉnh source mix. | **FAIL** |
| Ngưỡng cơ bản nghề–tháng | **19** occupation-month dưới 30 tin. **8** chuỗi source–occupation của archive có 12 tháng đạt hỗ trợ số lượng cơ bản và cửa sổ cutoff tiềm năng. Đây chưa phải nhãn kỹ năng đủ chắc hoặc future test đại diện. | **PASS một phần**, không mở forecast |
| Phạm vi input | Fresh Bronze run `partial/scoped`; archive là toàn bộ file local nhưng chỉ năm 2023. | **FAIL** |
| Feature/label thời gian theo mục 16–17 | Không tạo feature `t/t−1…` hoặc nhãn `t+1` khi chưa qua gate. | **Chưa đủ điều kiện** |
| Chiến lược Model A/B/C/D và recency theo mục 18–20 | Không huấn luyện/đánh giá; không có Macro-F1, Balanced Accuracy hoặc confusion matrix để báo cáo. | **Chưa chạy đúng cổng** |
| Rolling-origin future test theo mục 21 | Không có tập test tương lai cố định cùng scope, nhãn vượt kiểm tra độ bất định và so sánh baseline. | **NOT ELIGIBLE** |

Các ngưỡng cổng MVP vẫn là **≥30 tin duy nhất cho nghề–tháng**, **≥12 tháng liên tiếp có thể so sánh** và **≥3 cutoff có nhãn**; phải kiểm tra thêm nguồn, taxonomy, nhãn kỹ năng hiếm và tính đại diện của future test. Không chọn lại ngưỡng để hợp thức hóa dữ liệu hiện có.

## 3. Kết quả được phép công bố

- Phân tích mô tả Gold và **xu hướng đã quan sát** trong từng nguồn/tháng/nghề, luôn kèm `n`, provenance, taxonomy và phạm vi thu thập.
- Dashboard [JobScope](../planning/dashboard_runbook.md) có thể hiển thị `NO_GO` / `Insufficient evidence` cùng các kiểm tra gate, không biến 32 tháng thiếu thành số 0 hoặc nối archive với API thành chuỗi tăng trưởng.
- Kết luận nghiên cứu: dữ liệu hiện tại **chưa đủ cơ sở cho dự báo**. Đây là kết quả hợp lệ của nhánh NO-GO M7 nhưng cần nhóm/giảng viên ký hoặc ghi quyết định nghiệm thu.

Không công bố dự báo Growing/Stable/Declining, điểm mô hình, nhận định thị trường toàn cầu từ mẫu đã thu thập, hoặc phát biểu rằng M2/HDFS, M4 taxonomy hay M8/M9 tích hợp đã nghiệm thu.

## 4. Điều kiện xét lại GO

1. Xác minh URL/phiên bản/ngày tải/checksum và quyền sử dụng của nguồn lịch sử, nguồn fresh mới.
2. Bổ sung dữ liệu thật cho khoảng thiếu; lập lại audit nguồn × nghề × tháng sau dedup, tách tháng không quan sát khỏi tỷ lệ quan sát bằng 0.
3. Đánh giá title/skill taxonomy trên nhãn độc lập theo nguồn/nghề; báo precision/recall/F1 riêng với coverage.
4. Chứng minh mỗi nghề được thử đáp ứng ngưỡng hỗ trợ, có nhãn kỹ năng đủ chắc và nguồn/cách đo có thể so sánh.
5. Cố định future test, chạy rolling-origin backtest không rò rỉ thời gian, so sánh baseline trên cùng scope; sau đó cập nhật GO/NO-GO report và tạo lại Gold audit. Chỉ khi gate chuyển `GO` mới mở M6 và nhánh model M7.

## 5. Kiểm thử và mục còn mở

`python -m pytest -q tests/test_m7_no_go_dossier.py`: **11 passed**. Test dùng audit thật để đối chiếu 32/19/8, xác nhận output tái lập, và từ chối gate bị đổi sang GO, thiếu claim/check, ngưỡng sai, output prediction, phạm vi input bị che, lịch thiếu không nhất quán, cờ basic support sai hoặc file chính sách bị sửa. Kết quả regression toàn dự án được cập nhật sau khi chạy lại.

Preflight ngày 13/10: `PHASE02_HDFS_URI` chưa được cấu hình; Docker CLI có nhưng daemon chưa chạy. Không có round-trip `hdfs://` mới, nên **M2 vẫn OPEN**. M4 còn mở vì chưa có tập gán nhãn độc lập; nguồn/license chưa được xác minh. Hồ sơ này **không thay thế biên bản nghiệm thu chính thức** của nhóm/giảng viên.
