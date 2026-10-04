# Tổng kết Phase 01 và ghi chú Phase 02

## Phase 01 — Feasibility & Project Definition

Phase 01 được mở lại để sửa kết luận khả thi dựa trên bằng chứng trong repository. Review chi tiết ở [`PHASE_01_SYSTEM_REVIEW.md`](../reviews/PHASE_01_SYSTEM_REVIEW.md); số liệu kiểm kê và checksum ở [`phase01_data_audit.json`](../data/phase01_data_audit.json); quyết định mới ở [`go_no_go_report.md`](go_no_go_report.md).

| Hạng mục | Bằng chứng hiện có | Trạng thái |
|---|---|---|
| Historical archive | 785.741 dòng, 12 tháng năm 2023; có title/date/source tags; không có JD hoặc native job ID | Đủ cho prototype và descriptive analytics giới hạn |
| Fresh data | Snapshot đã lưu từ API công khai; không chứng minh API đang hoạt động liên tục | Dùng làm ví dụ snapshot, không ghép thành chuỗi lịch sử |
| Occupation/skill taxonomy | Bộ từ điển V0 và deterministic matcher; chưa có independent labeled set | Coverage có thể thống kê, accuracy chưa biết |
| Unified schema | 18 trường; các trường không có nguồn giữ null; provenance lưu riêng | Đặc tả đã đồng bộ, cần chạy ETL ở môi trường đích trước nghiệm thu vận hành |
| Time series / forecast | Chỉ có archive 2023 và snapshot rời rạc | **NO-GO** cho forecast/predictive claims |

**Quyết định hiện tại:** GO cho prototype; conditional GO cho mô tả dữ liệu theo đúng nguồn và giới hạn; NO-GO cho dự báo. Quality gate Phase 01 còn mở cho đến khi nguồn, điều khoản sử dụng, nhãn taxonomy và chuỗi thời gian đáp ứng các điều kiện trong GO/NO-GO report.

Các câu hỏi nghiên cứu RQ1–RQ6 là mục tiêu cần trả lời, không phải kết quả đã đo được. Phạm vi mong muốn 2022–2026 không đồng nghĩa với coverage quan sát được.

## Phase 02 — Ingestion & Storage

Kết quả 50.087 dòng Silver từ lần chạy cũ **không còn là số liệu nghiệm thu**. Mã Phase 02 hiện tạo Bronze run bất biến kèm checksum/manifest, ETL chỉ nhận run được chỉ định, chọn survivor theo `job_id`, ghi Silver + provenance + quarantine qua staging và lưu ETL manifest sau khi các output được kiểm tra.

**Bằng chứng local ngày 04/10/2026:** CSV lịch sử gốc được đọc với giới hạn 50.000 dòng (`historical` run `20261004T075529651874Z-33588af6ce76`, manifest SHA-256 `0F886D454179CCFA702028FEAF6071426199110AFD31F443EBFF0027829001A1`). Snapshot mới có 666 dòng, gồm 650 Arbeitnow/2 trang và 16 Remotive/1 trang (`fresh` run `20261004T075332383635Z-c9fddef628d7`, manifest SHA-256 `A9F14604497CA92F9579C71FF96F4E440565AC454C2F3F87DE7CC91D5CC95B51`). Cả hai input có trạng thái `partial`: lịch sử bị giới hạn dòng, fresh bị giới hạn trang hoặc chỉ có phạm vi API. ETL run `dd88fe9332284358a2346f9bc1ab1ad9` (manifest SHA-256 `987AEE785426B9C685354CFB95C01A8BB71BC4FC7BA5C4BC02C8C76F7D2C6743`) xác nhận **50.666 input = 50.659 Silver/provenance + 7 snapshot trùng ID**, quarantine 0. Các manifest và Parquet của lượt này ở `tmp/phase02_acceptance/`; output Silver cũ không bị ghi đè.

`python -m pytest -q` có **10 passed, 1 skipped** khi Spark khởi tạo được bằng thư mục tạm Windows ngắn. Test HDFS bị skip vì chưa có URI/dịch vụ HDFS hoạt động. Mã `src/processing/hdfs_smoke.py` yêu cầu `hdfs://` thật, upload Bronze, đọc bằng Spark và kiểm tra output HDFS; đến khi có evidence chạy thành công, **M2 vẫn OPEN**. Số local trên chỉ chứng minh pipeline kỹ thuật trong phạm vi mẫu đã chọn, không mở cổng dự báo hoặc khẳng định coverage toàn bộ archive/API.
