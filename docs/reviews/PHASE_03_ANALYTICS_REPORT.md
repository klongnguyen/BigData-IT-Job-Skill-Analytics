# Báo cáo Phase 03 — Gold mô tả và cổng dự báo

**Ngày kiểm tra:** 04/10/2026

**Kết quả:** Gold mô tả đã chạy trên toàn bộ archive hiện có cùng một snapshot API có phạm vi giới hạn. **NO-GO cho predictive claims**; không huấn luyện mô hình hay xuất dự báo. M2/HDFS của Phase 02 vẫn OPEN.

## 1. Phạm vi và bằng chứng đầu vào

Phase 03 đọc **một ETL manifest được chỉ định và khóa bằng SHA-256**, không đọc mặc định Silver cũ. Mã kiểm tra checksum Silver/provenance, số dòng, `job_id` duy nhất và nối 1:1 trước khi ghi Gold. Fresh run `partial` chỉ được dùng khi truyền `--allow-scoped-inputs`.

| Artifact | Run / SHA-256 | Phạm vi |
|---|---|---|
| Bronze historical | `20261004T103235056713Z-0811f6613d3c` / `48492bae64ab9e68a0ab93bc96814ced958a6ca7cc78af0e26e21bbd4207480a` | Toàn bộ CSV archive đang có: **785.741** dòng năm 2023; manifest `complete/full_input`. “Toàn bộ” chỉ là toàn bộ file local, không đại diện toàn thị trường. |
| Bronze fresh | `20261004T075332383635Z-c9fddef628d7` / `a9f14604497ca92f9579c71ff96f4e440565ac454c2f3f87de7cc91d5cc95b51` | **666** dòng: Arbeitnow 650 và Remotive 16; manifest `partial` vì giới hạn trang/phạm vi API. |
| ETL Silver/provenance | `8c8a0ca26b38404a96a9b97fa8fd6e02` / `7d767fca4ed3b728892dcac3a2d5bfbb57dfd5cc4601b14e889149dc403acb4c` | **786.407 input → 786.406 hợp lệ → 786.300 Silver = 786.300 provenance**; **106** bản trùng source identity bị gộp, **1** dòng historical thiếu title vào quarantine. |
| Gold | `20261004T110131548191Z-e38fa7303cf4` / `2b37892022882e834b5437555c5c567aa2ab31103dc1d581b9b2f18cd9e7c74d` | Các bảng mô tả local theo source/tháng; manifest tại `data/gold/global/runs/<run_id>/manifest.json`. |

Bản tóm tắt máy đọc được là [`phase03_analytics_audit.json`](../data/phase03_analytics_audit.json). Manifest ETL và log chạy nằm trong `tmp/phase03_acceptance/`; Gold Parquet nằm ở `data/gold/global/runs/20261004T110131548191Z-e38fa7303cf4/`. Các thư mục lớn là artifact local không đưa vào Git. Cả Gold manifest lẫn audit có thể commit đều ghi ETL SHA, checksum Silver/provenance, taxonomy/config/policy SHA, bộ lọc, loại phân tích, môi trường Python 3.11.9 / Spark 4.2.0 / Java 17.0.10, phạm vi input và quyết định gate.

## 2. Thống kê dữ liệu quan sát được

### 2.1 Nguồn và tháng

| Source | Tháng thực sự có tin | Tin Silver | Tin có ít nhất một skill chuẩn hóa | `Other IT` | Country có giá trị | Experience có giá trị |
|---|---:|---:|---:|---:|---:|---:|
| Archive 2023 | 12 | 785.639 | 629.764 (**80,16%**) | 180.251 (**22,94%**) | 785.461 | 0 |
| Arbeitnow 2026 | 2 | 645 | 284 (**44,03%**) | 558 (**86,51%**) | 0 | 0 |
| Remotive 2026 | 1 | 16 | 10 (**62,50%**) | 10 (**62,50%**) | 0 | 0 |

`Country có giá trị` là độ đầy trường sau ETL, **không phải** độ đúng địa lý. `Experience` hiện trống toàn bộ. Tỷ lệ `Other IT` cao trong snapshot fresh cho thấy taxonomy title chưa bao phủ tốt nguồn này; không dùng các tỷ lệ fresh nhỏ để suy rộng thị trường.

| Source | Month | Tin duy nhất | Source | Month | Tin duy nhất |
|---|---|---:|---|---|---:|
| Archive | 2023-01 | 91.816 | Archive | 2023-07 | 63.767 |
| Archive | 2023-02 | 64.571 | Archive | 2023-08 | 75.145 |
| Archive | 2023-03 | 64.073 | Archive | 2023-09 | 62.350 |
| Archive | 2023-04 | 62.916 | Archive | 2023-10 | 66.600 |
| Archive | 2023-05 | 52.101 | Archive | 2023-11 | 64.443 |
| Archive | 2023-06 | 61.566 | Archive | 2023-12 | 56.291 |
| Arbeitnow | 2026-09 | 41 | Arbeitnow | 2026-10 | 604 |
| Remotive | 2026-09 | 16 | — | — | — |

Giữa tháng đầu 2023-01 và tháng cuối 2026-10 có **32 tháng không quan sát**, gồm toàn bộ 2024–2025 và 2026-01 đến 2026-08. Đây là **thiếu dữ liệu**, không phải nhu cầu bằng 0. Không nối thẳng archive và API thành một chuỗi tăng trưởng; hai nguồn có phạm vi và cách đo kỹ năng khác nhau.

### 2.2 Phân bố nhóm nghề

| Occupation | Archive 2023 | Arbeitnow 2026 | Remotive 2026 |
|---|---:|---:|---:|
| Data Engineer | 200.880 | 6 | 0 |
| Data Analyst | 184.410 | 1 | 0 |
| Data Scientist | 181.591 | 7 | 1 |
| Other IT | 180.251 | 558 | 10 |
| Software Engineer | 17.742 | 47 | 2 |
| Machine Learning Engineer | 9.027 | 11 | 2 |
| DevOps Engineer | 8.436 | 9 | 0 |
| Backend Developer | 2.813 | 5 | 1 |
| Frontend Developer | 489 | 1 | 0 |

Đây là **phân bố trong từng nguồn đã thu thập**. Không so sánh số tin tuyệt đối của archive với các API như thể chúng có cùng coverage.

### 2.3 Nhu cầu kỹ năng trong nguồn

`demand_rate = skill_job_count / occupation_job_count` trong cùng source, occupation và tháng. Khi gộp các tháng để minh họa dưới đây, tử số là tổng tin chứa skill và mẫu số là tổng tin của nghề trong **cùng source**; job không có skill vẫn nằm trong mẫu số. `skill_evidence_coverage` được báo riêng. `source_tags` của archive và `extracted_from_jd` của API không được gộp thành một phép đo.

| Nguồn / chứng cứ | Nghề | Skill | Tin có skill / tin nghề | Tỷ lệ mô tả |
|---|---|---|---:|---:|
| Archive / `source_tags` | Data Engineer | SQL | 131.898 / 200.880 | **65,66%** |
| Archive / `source_tags` | Data Analyst | SQL | 96.213 / 184.410 | **52,17%** |
| Archive / `source_tags` | Data Scientist | Python | 132.392 / 181.591 | **72,91%** |
| Arbeitnow / `extracted_from_jd` | Software Engineer | Python | 28 / 47 | **59,57%** — mẫu scoped nhỏ |

Archive có 629.764/785.639 job có ít nhất một skill chuẩn hóa. Với Data Engineer archive, `skill_evidence_jobs` là 183.490/200.880; phần thiếu evidence **không bị loại khỏi mẫu số**. Trong cùng source–occupation–evidence scope, skill đã từng xuất hiện có `demand_rate=0` ở tháng nghề được quan sát nhưng skill không xuất hiện; **335** dòng Gold như vậy. Không tạo dòng 0 cho tháng không quan sát. Bảng `skill_trends` có **4.538** dòng diễn biến đã quan sát; **3.955** dòng có tháng trước liền kề để tính `observed_delta_pp`, còn các cặp có gap giữ `null`.

## 3. Gold outputs và khả năng tái lập

| Bảng Gold | Rows | SHA-256 của tập file output |
|---|---:|---|
| `market_stats` | 15 | `b9158f24bbdef70f3568c62f3f8fd9f5f5993065f423fe9e827ef56408cc8007` |
| `occupation_stats` | 127 | `01215ae60057c600745513e619c87c1b4001e28de22e9b814be23b3a1d00e8b3` |
| `skill_evidence_stats` | 234 | `238ae0890cdad7154c8c35ace682f6eab86d2ab76b782df9b1ff058ea3a71edb` |
| `skill_stats` | 4.538 | `fc1b169e0caa7eeffd8ee5dee448e63fe7cb31f60bb7280844b86e604774596c` |
| `skill_trends` | 4.538 | `9776edbd6c105ca9d378d81f0e6cae63402223c2465509ff15d4633a48cfd96b` |

Output dùng run ID riêng, publish sau khi số dòng ghi ra được đọc lại và khóa Gold không trùng. Manifest/checksum cho phép phát hiện input Silver/provenance bị sửa. Không tạo Gold prediction mới.

## 4. Cổng dự báo theo Final Plan mục 16–21

| Điều kiện | Kết quả | Bằng chứng |
|---|---|---|
| Quyết định GO/NO-GO hiện hành | **FAIL** | [GO/NO-GO](../planning/go_no_go_report.md) vẫn `NO-GO` cho forecasting. |
| Chuỗi thời gian liên tục | **FAIL** | 32 tháng không có input giữa 2023-01 và 2026-10; 2024–2025 trống hoàn toàn. |
| Nguồn/cách đo có thể so sánh | **FAIL** | Không có tháng quan sát giao nhau giữa cả archive và hai API; source tags và trích JD là hai chế độ đo khác nhau, chưa hiệu chỉnh source mix. |
| Ngưỡng nghề–tháng cơ bản | **PASS một phần** | 8 chuỗi source–occupation archive có 12 tháng liên tiếp đạt ≥30 tin và đủ cửa sổ tiềm năng; **19** occupation-month dưới 30 tin. Điều này không chứng minh nhãn kỹ năng đủ chắc hoặc future test đại diện. |
| Phạm vi input | **FAIL** | Fresh Bronze run `partial`; archive là toàn bộ file local nhưng chỉ năm 2023. |
| Rolling-origin future test, nhãn đủ chắc | **NOT ELIGIBLE** | Chưa tạo nhãn `t+1`, bootstrap CI hoặc future test cùng scope; không điền điểm mô hình giả. |

**Quyết định máy đọc được: `NO_GO`; predictive claims: `Insufficient evidence`.** Helper `require_predictive_go()` dừng future feature/model/prediction entrypoint khi gate chưa là `GO`. Audit không tự cấp phép `GO` chỉ vì một số chuỗi archive đạt ngưỡng tối thiểu.

## 5. Kiểm thử và giới hạn

| Kiểm tra | Kết quả |
|---|---|
| `python -m pytest -q` với `TEMP/TMP=C:\jtmp` | **15 passed, 1 skipped**; skip duy nhất là HDFS live test chưa có server/URI. Có 3 cảnh báo môi trường PySpark/Pandas/Arrow, không làm test thất bại. |
| Phase 03 fixture Spark | Kiểm chứng khóa manifest/checksum, từ chối provenance trùng, mẫu số demand rate gồm job thiếu skill, skill vắng ở tháng có quan sát tạo rate 0 và delta giảm, tháng gap không sinh dòng 0/delta giả, tách source/evidence origin, Gold key duy nhất, audit giữ metadata và không có prediction artifact. |
| Full archive ETL + Gold local | Đã chạy thật và ghi manifest/checksum như mục 1–3. |
| `git diff --check` | Đạt. |

**Không thực hiện vì gate `NO_GO`:** feature `t/t−1…`, nhãn `t+1`, train Model A/B/C/D, recency weighting, Macro-F1, Balanced Accuracy, confusion matrix và dự báo Growing/Stable/Declining. Không có chỉ số model để báo cáo. Đánh giá taxonomy trên nhãn độc lập, license/điều khoản archive, HDFS runtime và chuỗi thời gian nhiều năm vẫn là việc còn mở trước các milestone tương ứng.

### Lệnh chạy lại

```powershell
$env:TEMP = 'C:\jtmp'; $env:TMP = 'C:\jtmp'
python -m src.analytics.phase03_gold `
  --etl-manifest tmp/phase03_acceptance/etl_manifests/etl_8c8a0ca26b38404a96a9b97fa8fd6e02.json `
  --etl-manifest-sha256 7d767fca4ed3b728892dcac3a2d5bfbb57dfd5cc4601b14e889149dc403acb4c `
  --allow-scoped-inputs `
  --output-root data/gold/global/runs `
  --audit-json docs/data/phase03_analytics_audit.json
python -m pytest -q
git diff --check
```
