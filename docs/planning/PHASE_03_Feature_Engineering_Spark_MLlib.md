# Phase 03 — Gold mô tả và kiểm toán cổng dự báo

**Trạng thái:** triển khai analytics trên một ETL run Phase 02 được chỉ định rõ; phần feature engineering, Spark MLlib và dự báo vẫn bị khóa theo [GO/NO-GO hiện hành](go_no_go_report.md). Tên file được giữ để các liên kết cũ không bị gãy. Bản kế hoạch trước đây dùng 50.087 Silver và chia train 2023/test 2026 đã lỗi thời; không dùng các số hoặc phép chia đó làm bằng chứng.

## Quan hệ với Final Plan

[Final Plan](../../FINAL_PLAN_BigData_IT_Job_Market_Skill_Forecasting.md) đặt cổng dữ liệu tại mục 21: ít nhất 30 tin duy nhất cho nghề–tháng, 12 tháng liên tiếp có thể so sánh, ít nhất 3 cutoff có nhãn, nguồn có phạm vi so sánh được và rolling-origin future test. Mục 16–20 chỉ áp dụng khi cổng này đạt. Trong repository hiện có archive 2023 và snapshot API 2026 rời rạc; khoảng 2024–2025 không có quan sát. M2/HDFS Phase 02 vẫn mở. Vì vậy công việc hiện tại xây Gold mô tả, không gán nhãn Growing/Stable/Declining và không huấn luyện A/B/C/D.

Final Plan gọi Phase 3 là ETL/Silver và Phase 4–5 là skill extraction/analytics. Tài liệu công việc này dùng tên “Phase 03” theo nhịp thực hiện hiện có của repository; các milestone M3/M4/M5 chỉ được nghiệm thu theo bằng chứng của từng milestone, không tự đóng bằng tên file.

## Input bắt buộc

- Một ETL manifest `status=completed`, SHA-256 kỳ vọng được truyền tường minh. Không quét mặc định thư mục Silver cũ.
- Kiểm tra checksum từng output Silver/provenance, số dòng khai báo, `job_id` duy nhất và nối 1:1 trước khi xây Gold.
- Bronze input `partial` cần cờ `--allow-scoped-inputs`. Kết quả phải ghi rõ phạm vi source và trạng thái coverage.
- Dùng `skills_origin` và `taxonomy_version` trong provenance để không trộn source tags lịch sử với kỹ năng trích từ JD mới thành cùng một phép đo.

## Gold mô tả

Chạy `python -m src.analytics.phase03_gold` để tạo một run bất biến trong `data/gold/global/runs/<run_id>/`:

| Bảng | Khóa | Diễn giải |
|---|---|---|
| `market_stats` | source, month | Số tin đã quan sát, công ty phân biệt, coverage country/work mode/experience/skill. |
| `occupation_stats` | source, month, occupation | Tin duy nhất của nghề, tổng tin cùng source–month, tỷ trọng nghề. `Other IT` giữ riêng để báo coverage taxonomy. |
| `skill_evidence_stats` | source, month, occupation, skills_origin, taxonomy_version | Số job theo nguồn chứng cứ, số job có ít nhất một skill và coverage. Gồm cả nhóm không có skill. |
| `skill_stats` | thêm skill | `skill_job_count / occupation_job_count`; mẫu số gồm cả job thiếu skill. Skill đã xuất hiện trong một series có tỷ lệ 0 ở tháng cùng scope có quan sát nhưng không có skill đó; tháng không quan sát vẫn vắng mặt. |
| `skill_trends` | như `skill_stats` | `observed_delta_pp` chỉ có khi tháng quan sát trước liền kề và cùng source/occupation/evidence scope. Tháng thiếu không được điền 0. |

Mỗi run có `manifest.json` chứa input ETL/run/checksum, taxonomy/config checksum, số dòng và checksum Gold, source scope, môi trường Spark/Java/Python, quyết định cổng dự báo. `docs/data/phase03_analytics_audit.json` là bản tóm tắt nhỏ có thể commit và giữ cả phiên bản taxonomy, config/policy checksum, môi trường, bộ lọc và loại phân tích; Parquet lớn vẫn là artifact local. Không ghi vào `data/gold/.../predictions`.

## Cổng dự báo

`src.analytics.predictive_gate.assess_predictive_gate` kiểm toán source × occupation × month, số tháng liên tiếp đạt ngưỡng và khoảng trống không quan sát. Kết quả **NO_GO** khi chính sách hiện hành chưa mở dự báo hoặc chưa có future test đại diện. `require_predictive_go` phải được gọi bởi mọi entrypoint feature/model/prediction về sau; nếu gate chưa là `GO`, chương trình dừng trước khi ghi artifact. Audit không sinh nhãn `t+1` hay chỉ số model.

## Chạy và kiểm thử

```powershell
$env:TEMP = 'C:\jtmp'; $env:TMP = 'C:\jtmp'
python -m src.analytics.phase03_gold `
  --etl-manifest <path-to-completed-etl-manifest.json> `
  --etl-manifest-sha256 <verified-sha256> `
  --allow-scoped-inputs `
  --output-root data/gold/global/runs `
  --audit-json docs/data/phase03_analytics_audit.json
python -m pytest -q
git diff --check
```

Xem [báo cáo Phase 03](../reviews/PHASE_03_ANALYTICS_REPORT.md) cho run, thống kê và kết quả kiểm thử đã xác minh. Chỉ xét lại ML/dự báo sau khi có dữ liệu mới, kiểm toán nguồn/taxonomy và rolling-origin backtest theo Final Plan.
