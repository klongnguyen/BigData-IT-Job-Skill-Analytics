# C2C 2026 → Dashboard — Giai đoạn 1 hạ tầng

**Cập nhật iteration 2:** Mẫu 175 dòng đã được rà soát bằng AI; xem [báo cáo AI-assisted](2026_IT_SCOPE_AI_REVIEW_2026-10-15.md). Trạng thái chờ review thủ công dưới đây là điểm dừng của iteration 1, không phải trạng thái hiện hành.

**Task:** `c2c_2026_to_dashboard`, iteration 1. **Trạng thái:** chờ review mẫu IT thủ công; chưa tạo Silver/Gold production mới và chưa chuyển audit dashboard.

## Input được pin

[`2026_silver_input_selection.json`](../data/2026_silver_input_selection.json) khóa đúng 23 Bronze run trong audit 2026 bằng đường dẫn tương đối workspace, run ID, manifest SHA-256, trạng thái, nguồn và số dòng. SHA-256 của selection: `e1e8c9443b98ca64368ed1ca31cae11947c7919ff9d62050ac61575d40fe87fe`. Loader đối chiếu SHA của selection, audit, từng manifest và từng record file trước khi cho ETL đọc.

Tập chọn có 21.435 dòng Bronze. Chỉ run `20261015T024120862520Z-6d0ef660e16f` với manifest SHA `74d13bc94ebc2ea2eae7d02eb856570d0c93aafe18d614ddbc91dc87a38a8a6c` được phép `partial`. Kiểm tra thực tế cho thấy 15 ID Remotive duy nhất từ run này; 1.456 ID Arbeitnow của nó đều có mặt trong run Arbeitnow `complete`, nên số ID Arbeitnow độc quyền từ `partial` là 0. Run `partial` khác, hoặc thay run ID/SHA/status, bị từ chối.

## ETL đã chuẩn bị

- `--fresh-run` nhận nhiều lần; `--input-selection` + `--input-selection-sha256` kích hoạt contract 2026. Chế độ này không cho `--replace-existing` hoặc generic `--allow-partial-inputs`.
- Mỗi Bronze run được đọc riêng, gắn `input_run_id`, `input_manifest_sha256`, trạng thái và loại run trước khi union/dedup. HDFS staging đặt theo `kind/run_id`.
- Provenance của mỗi Silver row có survivor run ID/SHA và `input_lineage` gồm mọi observation hợp lệ cùng ID, với `ingestion_id`, `collected_at`, `raw_checksum`, `selected_survivor`.
- Record hợp lệ ngoài rule phạm vi đi vào artifact `scope_excluded` có SHA/lineage riêng trong ETL manifest; quarantine chỉ chứa record invalid. Manifest có accounting và bảng `source × market × occupation × month`.
- Rule strict-title cho Arbeitnow/Remotive **chưa được nghiệm thu**; USAJOBS `PositionSeries=2210` giữ nhãn `Other IT` nếu taxonomy chưa map. Kiểm thử dùng fixture nhỏ, không chạy pipeline production trên 23 run.

## Mẫu cần người dùng gán nhãn

[`2026_it_scope_sample.csv`](../data/2026_it_scope_sample.csv) có 175 dòng: Arbeitnow 80 (40 mapped, 40 `Other IT`), Remotive toàn bộ 15 (7 mapped, 8 `Other IT`), USAJOBS 80 (40 mapped, 40 `Other IT`). Cả 175 dòng đều để trống `manual_label`, `in_scope_it`, `review_reason`. SHA-256 mẫu chưa gán nhãn: `34be349a016de434f3bcc3c29bacc5601226004d68e63479cbf3795165d0d54a`. Xem [hướng dẫn review](2026_IT_SCOPE_SAMPLE_GUIDE.md). Không công bố precision/recall/F1 từ mẫu chưa gán nhãn.

## Kiểm thử và bảo toàn run cũ

Chạy trong container Spark/HDFS hiện có:

```text
docker exec -w /workspace hdfs-project-smoke python3 -m pytest -q tests/test_2026_input_selection.py tests/test_2026_spark_etl.py tests/test_phase02_spark_etl.py tests/test_2026_collectors.py tests/test_phase02_ingestion.py tests/test_phase02_identity.py
21 passed
```

Test tích hợp chứng minh multi-run dedup, hai manifest SHA trong lineage của một ID, `scope_excluded` có lineage, Remotive từ exact partial run, market đúng, quarantine/accounting và artifact cũ bất biến. `python -m py_compile` và `git diff --check` đạt.

Gold cũ `20261004T110131548191Z-e38fa7303cf4` vẫn load được qua audit cũ; manifest SHA thực tế `2b37892022882e834b5437555c5c567aa2ab31103dc1d581b9b2f18cd9e7c74d` khớp audit. ETL manifest cũ cũng khớp SHA `7d767fca4ed3b728892dcac3a2d5bfbb57dfd5cc4601b14e889149dc403acb4c`. Forecast gate vẫn `NO_GO`.

## Điểm dừng

Review thủ công mẫu IT, đối chiếu các trường hợp taxonomy nhận sai hoặc bỏ sót. Chỉ sau khi rule được duyệt mới chạy Silver production mới, audit accounting, rồi thiết kế Gold/descriptive và dashboard tách `GLOBAL` với `US_FEDERAL`.
