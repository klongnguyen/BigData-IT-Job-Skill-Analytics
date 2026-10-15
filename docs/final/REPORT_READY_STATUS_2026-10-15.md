# Trạng thái sẵn sàng báo cáo · 15/10/2026

**Mức tiến độ:** khoảng **90% theo các hạng mục bàn giao**. Pipeline mô tả 2026 và dashboard đã chạy thật, Gold audit `passed`, kiểm thử đạt. Mốc 100% là khi máy trình bày và slide được kiểm tra, các giới hạn được chấp thuận, đánh giá độc lập được hoàn thành hoặc được ghi rõ là việc sau đồ án, và có biên bản nghiệm thu. Phần trăm này không phản ánh độ chính xác taxonomy hay năng lực dự báo.

## Kiến trúc và deliverables đã chạy

`Bronze 23 run + manifest → Spark ETL/dedup/scope → Silver 8.370 + provenance 8.370 → Gold 5 bảng → JobScope sáu trang`. HDFS → Spark ETL → Silver đã chạy trên run fresh 666→661 riêng. Gold cũ 2023 được giữ nguyên, Gold JobScope 2026 ở namespace riêng. Catalog chỉ cho mở các run có audit pin; dashboard có bộ lọc Dataset → Market → Source → Month → Occupation.

| Bằng chứng | Run / giá trị | SHA-256 hoặc nguồn |
| --- | --- | --- |
| Bronze 2026 | 21.435 raw; 19.706 unique; 1.729 duplicate | [Audit Bronze](../data/2026_ingestion_audit.json) `e3325b36bc841002c012a5b37b47089de00da218eefb78391c14ef1a2c1e4e92` |
| Input selection | 23 Bronze runs; đúng một partial được cho phép | [Selection](../data/2026_silver_input_selection.json) `e1e8c9443b98ca64368ed1ca31cae11947c7919ff9d62050ac61575d40fe87fe` |
| Silver 2026 | `10d0710787d2402186356858d3331e50`; 8.370 analytical/provenance; 548 excluded; 10.788 unresolved; 0 quarantine | ETL manifest `817c24b15a12436ce47c2fce08a891ce50f31cb87221bc3ce2b74a028a7b15c9`; [Silver audit](../data/2026_silver_run_audit.json) `022342d20493ed9130a0f8c2f166eb27a3896951eb2a3f8f8f80c2d1475090d1` |
| Gold 2026 | `20261015T144634600577Z-8d531796a5f6`; 5 bảng 13/66/66/401/401 | Manifest `c9208520cecf115591d524120fc13bc1501de893a30897072e0f61c30c3cf1cd`; [Gold audit](../data/2026_gold_run_audit.json) `4e130c088954ecb112b9939c64a9ccf891e51b6f81162348c7d67c5c1e9e0b11` |
| Legacy Gold | `20261004T110131548191Z-e38fa7303cf4`; vẫn mở được | Manifest `2b37892022882e834b5437555c5c567aa2ab31103dc1d581b9b2f18cd9e7c74d` |

Gold 2026: `GLOBAL` 1.631 (Arbeitnow 1.621, Remotive 10); `US_FEDERAL` 6.739 (USAJOBS 2210). Tổng `market_stats.job_count`, `occupation_stats.job_count`, `skill_evidence_stats.origin_job_count` đều 8.370. Không trộn market và không đưa excluded/unresolved vào denominator. Arbeitnow chỉ tháng 10; Remotive 8 tin tháng 9, 2 tin tháng 10; USAJOBS Jan–Oct. Tháng không quan sát giữ gap. Forecast vẫn `NO_GO`, không có model hoặc prediction artifact.

## Kiểm thử 15/10/2026

| Lệnh/kiểm tra | Kết quả |
| --- | --- |
| Spark container: `python3 -m pytest -q tests/test_phase03_analytics.py tests/test_phase03_predictive_gate.py` | **8 passed**; market keys, denominator/lag, SHA sai, partial trái phép, Silver bị sửa, Gold cũ, `NO_GO`. |
| Spark container: `python3 -m pytest -q tests/test_2026_input_selection.py tests/test_2026_scope_policy.py tests/test_2026_spark_etl.py` | **7 passed**; input selection, scope policy và multi-run ETL regression. |
| `.venv-dashboard`: `python -m pytest -q tests/test_dashboard.py tests/test_mongo_gold.py` | **18 passed**; catalog, scoped Gold thật, market filters, mẫu số, sáu trang AppTest, Mongo. |
| `.venv-dashboard`: `python -m compileall -q dashboard src scripts tests` | **Đạt**. |
| `git diff --check` | **Đạt**; chỉ có cảnh báo chuẩn hóa LF/CRLF của Git trên Windows. |
| Dashboard local `http://127.0.0.1:8501/_stcore/health` | **HTTP 200**. |
| SHA manifest Gold cũ | Vẫn đúng `2b37892022882e834b5437555c5c567aa2ab31103dc1d581b9b2f18cd9e7c74d`. |

## Giới hạn phải nêu khi báo cáo

- 10.788 Arbeitnow unresolved có thể chứa IT; không gọi là non-IT. `GLOBAL` 2026 chỉ gồm title đủ bằng chứng theo policy. Mẫu 175 dòng là **AI-assisted**, chưa phải human ground truth; chưa có precision/recall/F1 độc lập.
- USAJOBS chỉ tuyển dụng liên bang Mỹ PositionSeries 2210; không đại diện toàn thị trường Mỹ và chưa có skill evidence chuẩn hóa. Snapshot API không phải lịch sử liên tục; không so số lượng 2023–2026 như cùng sampling frame.
- HDFS lab một DataNode không chịu lỗi node. Raw/Parquet lớn và MongoDB local không nằm trong Git; bản clone cần khôi phục artifact đúng SHA.
- Gold 2026 không đủ điều kiện dự báo. Quyết định `NO_GO` không được đổi để phục vụ demo.

## Khoảng 10% còn lại

1. **Trước buổi báo cáo:** kiểm tra dashboard trên máy trình bày, bảo đảm artifact và Python sẵn; cập nhật PPTX cũ theo [outline 10 slide](PRESENTATION_OUTLINE_2026-10-15.md); diễn tập theo [demo script](DEMO_SCRIPT.md).
2. **Nghiệm thu:** nhóm/giảng viên xác nhận phạm vi market và chính sách unresolved, HDFS lab, Gold mô tả và hồ sơ `NO_GO`; ghi biên bản với run ID/SHA.
3. **Sau hoặc theo yêu cầu hội đồng:** đánh giá taxonomy/scope trên nhãn độc lập, kiểm tra license/attribution nguồn trước khi công bố dữ liệu thô, thu thêm snapshot liên tục nếu muốn mở lại gate dự báo.

4. **Bàn giao và mã nguồn:** Toàn bộ mã nguồn hệ thống, cấu hình chính sách, test suite, dashboard, script audit và hồ sơ báo cáo nghiệm thu đã được hoàn tất, kiểm thử toàn diện và đẩy lên kho lưu trữ GitHub (`origin/main`). Dữ liệu thô lớn và thư mục chạy Parquet/MongoDB cục bộ được quản lý an toàn qua `.gitignore` và neo giữ bằng các tệp manifest và mã băm SHA-256 đã kiểm toán.
