# Audit Silver 2026

- Kết quả: **PASS**; ETL run `10d0710787d2402186356858d3331e50`.
- Manifest SHA-256: `817c24b15a12436ce47c2fce08a891ce50f31cb87221bc3ce2b74a028a7b15c9`.
- Input 21,435; valid 21,435; duplicate 1,729; quarantine 0.
- Silver 8,370; provenance 8,370; ngoài IT 548; chưa xác định 10,788.

## Silver theo nguồn và market

| Source | Market | Rows |
|---|---|---:|
| arbeitnow | GLOBAL | 1,621 |
| remotive | GLOBAL | 10 |
| usajobs_historic | US_FEDERAL | 6,739 |

## Kiểm chứng

- SHA manifest, tất cả thư mục Parquet và gate preflight khớp.
- Job ID của Silver và provenance 1:1; mỗi dòng có input lineage.
- Remotive trong Silver có 10 dòng từ partial đã pin; 5 dòng ngoài IT lưu riêng.
- USAJOBS PositionSeries=2210 chỉ ở US_FEDERAL; GLOBAL không trộn mẫu số.
- SHA taxonomy v0.1, ETL/Gold manifest cũ và Silver/provenance cũ còn nguyên.
- 10.788 dòng chưa xác định được giữ riêng, không đưa vào Silver hoặc quarantine.
- Forecast gate giữ NO_GO; chưa tạo Gold hoặc dashboard trong iteration này.

## Giới hạn

Mẫu 175 dòng là AI-assisted, không phải human ground truth. 83,3% Arbeitnow còn unresolved; phân tích GLOBAL hiện chỉ đại diện cho các tiêu đề có bằng chứng IT theo policy v1.
