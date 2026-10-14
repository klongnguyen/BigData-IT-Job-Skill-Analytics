# Tiến độ thực tế — 12/10/2026

Đã triển khai tiếp từ scaffold 19 dòng thành **JobScope**, dashboard Streamlit đọc 5 bảng Gold thật qua lớp serving Parquet. Xem [runbook](dashboard_runbook.md) để mở web và chạy demo.

| Thành phần | Bằng chứng hiện có | Còn lại |
|---|---|---|
| Bronze → Spark → Silver | Run 04/10: 786.300 Silver, provenance 1:1 | M2/HDFS chưa nghiệm thu runtime |
| Gold descriptive | 5 bảng, giữ nguyên run `20261004T110131548191Z-e38fa7303cf4` | Kiểm định taxonomy độc lập và nguồn/license |
| Serving Parquet | Loader kiểm tra audit/manifest/hash/file/row/schema/key trước khi render | MongoDB chưa triển khai, nếu cần theo yêu cầu môn học |
| Web UI | 5 chuyên mục, biểu đồ, bộ lọc, bảng và CSV; chạy trên máy bằng Streamlit | Nghiệm thu M8/M9 tích hợp và review của nhóm |
| Dự báo | Hiển thị NO_GO / Insufficient evidence, gate checks và 32 tháng thiếu | Thu thập chuỗi liên tục, future test, xét lại gate trước feature/model |
| Báo cáo cuối | Có snapshot tiến độ, báo cáo Phase 01–03, runbook UI | Hồ sơ nghiệm thu và trình bày end-to-end |

## Số liệu kiểm tra trên UI

- Archive 2023: 785.639 tin; 629.764 có skill chuẩn hóa; coverage 80,16% (UI tổng quan làm tròn 80,2%).
- Data Engineer / SQL / source_tags: 131.898 / 200.880 = 65,66%.
- Arbeitnow / Software Engineer / Python / extracted_from_jd: 28 / 47 = 59,57%.
- Snapshot API giữ cảnh báo partial/scoped; đổi nguồn không trộn các chế độ đo.
- Không có quan sát sau bộ lọc → thông báo rỗng; tháng thiếu là gap, không phải tỷ lệ 0.

## Kiểm thử ngày 12/10

- Dashboard: **13 passed**, gồm integrity/weighted denominator/zero-vs-gap/source separation và Streamlit AppTest cho 5 chuyên mục, thay nguồn và bộ lọc rỗng.
- Pipeline Phase 01–03: **15 passed, 1 skipped**, 3 cảnh báo môi trường PySpark/Pandas/Arrow; skip là HDFS live chưa có URI/dịch vụ.
- Hai bộ test chạy trong môi trường tương ứng: UI `.venv-dashboard`, pipeline Python/Spark đã có. Không thay đổi môi trường Spark khi cài UI.
- Kiểm tra trực tiếp web: các màn và số liệu ví dụ nêu trên; app được giữ chạy để người dùng xem.
- Log kiểm thử local: `tmp/dashboard_pytest.txt` và `tmp/dashboard_pipeline_regression.txt` (không đưa vào Git).

Đây là **demo descriptive local**, chưa phải tuyên bố hoàn tất toàn bộ đồ án hoặc nghiệm thu M8/M9. Bản snapshot ngày 07/10 được giữ làm lịch sử. Các thay đổi Phase 03 chưa commit có sẵn được bảo toàn.

## Tiếp theo tại thời điểm 12/10

1. Hoàn tất đường chạy HDFS → Spark với evidence để đóng M2 theo tiêu chí môn học.
2. Xác minh nguồn/license; đánh giá taxonomy trên tập gán nhãn độc lập, nhất là tỷ lệ Other IT cao ở API.
3. Chốt nghiệm thu serving/dashboard cùng nhóm; bổ sung MongoDB nếu cần truy vấn serving trong tiêu chí chấm.
4. Thu thập fresh định kỳ, bổ sung dữ liệu thật cho các tháng thiếu; chuẩn bị hồ sơ M7 theo nhánh NO-GO.
5. Hoàn thiện báo cáo tích hợp và demo cuối. Chỉ triển khai model khi gate được xét lại thành GO bằng dữ liệu mới.

## Cập nhật 13/10/2026 — hồ sơ M7 nhánh NO-GO

Đã tạo [biên bản đề xuất nghiệm thu M7](../reviews/M7_NO_GO_ACCEPTANCE.md) và [dossier JSON có SHA-256 nguồn](../data/m7_no_go_dossier.json) từ audit Phase 03. Hồ sơ khóa Gold run, chính sách GO/NO-GO, taxonomy, sáu gate checks và các số liệu **32 tháng thiếu / 19 occupation-month dưới ngưỡng / 8 chuỗi đạt hỗ trợ cơ bản**. Trạng thái là **sẵn sàng để xét nghiệm thu**, không phải M7 đã được nhóm/giảng viên chấp thuận hoặc có model dự báo.

Kiểm thử mới: **11 test dossier đạt**; regression Spark/pipeline **26 passed, 1 skipped** (HDFS live); dashboard **13 passed** trong môi trường UI riêng. `PHASE02_HDFS_URI` chưa được cấu hình, vì vậy **M2 vẫn OPEN**. M4 còn chờ tập nhãn độc lập; nhánh model của M7 và M6 vẫn bị khóa bởi gate `NO_GO`.
