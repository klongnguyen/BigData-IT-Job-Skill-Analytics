# Báo cáo triển khai BigData Job Analy · cập nhật 15/10/2026

## 1. Mục tiêu và phạm vi

JobScope trả lời các câu hỏi mô tả trong **mẫu tin đã thu**: bao nhiêu tin theo nguồn, tháng và nhóm nghề; kỹ năng nào được ghi nhận; tỷ lệ tin có kỹ năng là bao nhiêu trong đúng mẫu số nghề. Đây không phải ước lượng quy mô toàn thị trường. Thị trường Việt Nam chưa nằm trong MVP. Nhánh dự báo chưa đủ bằng chứng và giữ `NO_GO`.

## 2. Kiến trúc và đường dữ liệu đã chạy

`Bronze bất biến + manifest → Spark ETL (validation, dedup, scope) → Silver + provenance → 5 bảng Gold mô tả → dashboard JobScope`.

HDFS Bronze → Spark ETL → Silver đã được chứng minh trên run fresh riêng: 666 input, 661 Silver/provenance, 5 ID trùng, 0 quarantine. [Audit HDFS](../data/m2_hdfs_etl_audit.json) khóa run và output. HDFS lab có một DataNode và không chịu lỗi node.

Đường 2026 dùng [23 Bronze run được pin](../data/2026_silver_input_selection.json), trong đó duy nhất một partial run được cho phép bằng run ID và manifest SHA. Không ghép JSON raw thủ công. Mỗi observation giữ lineage; dedup giữ toàn bộ input lineage của survivor và tách record ngoài hoặc chưa rõ scope. Silver mới nằm trong namespace `jobscope`, các run cũ không bị ghi đè.

## 3. Dữ liệu 2026 và scope

| Chỉ tiêu | Số tin |
| --- | ---: |
| Raw Bronze | 21.435 |
| ID nguồn duy nhất | 19.706 |
| Trùng loại sau dedup | 1.729 |
| Silver analytical = provenance | 8.370 |
| Ngoài phạm vi IT, lưu riêng | 548 |
| Chưa đủ căn cứ, lưu riêng | 10.788 |
| Quarantine | 0 |

Silver run `10d0710787d2402186356858d3331e50`, manifest SHA-256 `817c24b15a12436ce47c2fce08a891ce50f31cb87221bc3ce2b74a028a7b15c9`. [Audit Silver](../data/2026_silver_run_audit.json) có SHA-256 `022342d20493ed9130a0f8c2f166eb27a3896951eb2a3f8f8f80c2d1475090d1`. `GLOBAL` gồm Arbeitnow 1.621 và Remotive 10; `US_FEDERAL` gồm USAJOBS PositionSeries 2210: 6.739. Không cộng hai market thành một tỷ lệ hoặc mẫu số thị trường.

[Taxonomy v0.2](../../configs/job_title_mapping_v0_2.json) và [scope policy v1](../../configs/job_scope_policy_2026_v1.json) được pin SHA trong manifest. Mẫu 175 dòng được review ngữ nghĩa với **AI assistance**, có thể phân biệt IT ngoài tám nhóm, ngoài IT và chưa đủ thông tin. Đây không phải tập nhãn độc lập do con người kiểm chứng; không công bố precision, recall hay F1. `Other IT` được giữ nếu policy xác lập in-scope, đặc biệt với USAJOBS series 2210. 10.788 dòng unresolved không được suy ra là non-IT.

## 4. Gold mô tả 2026 và dashboard

Gold immutable run `20261015T144634600577Z-8d531796a5f6`, manifest SHA-256 `c9208520cecf115591d524120fc13bc1501de893a30897072e0f61c30c3cf1cd`. [Audit Gold](../data/2026_gold_run_audit.json) có SHA-256 `4e130c088954ecb112b9939c64a9ccf891e51b6f81162348c7d67c5c1e9e0b11`, trạng thái `passed`.

| Bảng Gold | Số dòng | Khóa phân tích |
| --- | ---: | --- |
| `market_stats` | 13 | market, month, source |
| `occupation_stats` | 66 | thêm occupation |
| `skill_evidence_stats` | 66 | thêm occupation, origin, taxonomy |
| `skill_stats` | 401 | thêm skill |
| `skill_trends` | 401 | cùng khóa skill, có lag theo market |

Tổng `job_count` của market và occupation, cùng `origin_job_count` của evidence, đều là **8.370**. Không đưa 548 excluded hoặc 10.788 unresolved vào mẫu số. Arbeitnow quan sát tháng 10; Remotive 8 tin tháng 9 và 2 tin tháng 10; USAJOBS có quan sát tháng 1–10. Tháng không quan sát là gap, không phải 0. `Other IT` đã xác lập in-scope vẫn là nhóm analytical hợp lệ.

Dashboard chọn Dataset → Market → Source → Month → Occupation qua [catalog audit](../data/dashboard_gold_catalog.json). Gold 2023 cũ vẫn dùng run `20261004T110131548191Z-e38fa7303cf4`, manifest SHA-256 `2b37892022882e834b5437555c5c567aa2ab31103dc1d581b9b2f18cd9e7c74d`. Gold 2026 dùng namespace riêng. Cả hai backend được kiểm tra manifest và output; MongoDB chỉ phục vụ Gold cũ, 2026 đọc Parquet. Dashboard có sáu trang, gồm phân tích 2026 và trang pipeline Bronze → Silver → Gold. USAJOBS chưa có kỹ năng chuẩn hóa nên trang kỹ năng hiển thị thiếu chứng cứ, không tạo tỷ lệ giả.

## 5. Quyết định dự báo

Gate tiếp tục **`NO_GO`**; không có model, nhãn Growing/Stable/Declining, prediction artifact hoặc metric mô hình. Trong Gold 2026, dù USAJOBS có 10 tháng quan sát, không có source–occupation series nào đạt đồng thời điều kiện tối thiểu 12 tháng liên tục và 30 tin/nghề/tháng; snapshot GLOBAL chỉ có 1–2 tháng. USAJOBS liên bang và nguồn GLOBAL không có phương pháp hiệu chỉnh khung lấy mẫu để so sánh. Gold 2023 và 2026 cũng không tạo thành một chuỗi thống nhất. [Hồ sơ quyết định](../reviews/M7_NO_GO_ACCEPTANCE.md) cần nhóm/giảng viên nghiệm thu.

## 6. Kiểm thử và giới hạn

Gold audit đọc lại cả năm Parquet, xác minh khóa, tổng số, lineage và checksum; manifest Gold cũ vẫn đúng SHA. Kiểm thử analytics bao phủ khóa market, denominator, lag theo market, input bị sửa, SHA sai, partial trái phép và gate. Kiểm thử dashboard bao phủ catalog/audit pin, bộ lọc thị trường, mẫu số, sáu trang và `NO_GO`. Kết quả lệnh kiểm thử cuối cùng được lưu ở [mức sẵn sàng báo cáo](REPORT_READY_STATUS_2026-10-15.md).

Giới hạn chính: snapshot Arbeitnow/Remotive không phải lịch sử liên tục; USAJOBS chỉ là tuyển dụng liên bang Mỹ; tỷ lệ trong Silver GLOBAL dựa trên title có đủ bằng chứng theo policy; 10.788 unresolved có thể chứa nghề IT; taxonomy chưa được kiểm định trên ground truth độc lập; dữ liệu kỹ năng USAJOBS thiếu; HDFS lab một DataNode; raw/Parquet lớn và MongoDB local không có trong Git. Bản [slide PPTX cũ](BigData_Job_Analy_Final_2026-10-15_v2.pptx) chưa cập nhật kết quả Gold 2026; dùng [outline mới](PRESENTATION_OUTLINE_2026-10-15.md) để chỉnh trước buổi báo cáo.

## 7. Kết luận và công việc còn lại

Phần triển khai mô tả 2026 đã đi trọn từ Bronze đến dashboard, có audit và giới hạn diễn giải rõ. Mức sẵn sàng khoảng **90% theo deliverables**. Để nghiệm thu 100%, cần kiểm tra demo trên máy trình bày, cập nhật slide, đánh giá taxonomy/scope bằng nhãn độc lập, chấp thuận phạm vi nguồn và hồ sơ `NO_GO`, rồi ký biên bản. Xem [trạng thái report-ready](REPORT_READY_STATUS_2026-10-15.md) và [demo script](DEMO_SCRIPT.md).
