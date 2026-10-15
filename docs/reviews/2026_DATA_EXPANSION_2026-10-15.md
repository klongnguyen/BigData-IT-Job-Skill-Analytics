# Bổ sung dữ liệu tuyển dụng năm 2026 — 15/10/2026

## Kết quả và phạm vi

Đã thu dữ liệu thật từ ba nguồn công khai vào các run Bronze bất biến, rồi kiểm tra manifest, hash file, ID nguồn và ngày đăng. [Audit máy đọc được](../data/2026_ingestion_audit.json) chọn **23 run** (1 run API hỗn hợp có Remotive, 1 run Arbeitnow đầy đủ, 21 run USAJOBS hoàn chỉnh) và ghi nhận **19.706 bản ghi duy nhất** trong năm 2026. Không cộng các nguồn này thành một chuỗi nhu cầu tuyển dụng chung.

| Nguồn | Phạm vi | Bản ghi duy nhất 2026 | Tháng quan sát | Tình trạng thu |
|---|---|---:|---|---|
| Arbeitnow | API việc làm chủ yếu tại châu Âu, gắn `market=GLOBAL` theo quy ước dự án | **12.952** | 10/2026 | 91 trang, run đầy đủ; 13.225 dòng thô trong run, 273 ID lặp được audit khử trùng. |
| Remotive | Snapshot việc làm remote đang hoạt động, `market=GLOBAL` | **15** | 09–10/2026 | Endpoint trả 15 dòng; đây không phải backfill lịch sử. 9 dòng tháng 09, 6 dòng tháng 10. |
| USAJOBS Historic | **Chỉ** thông báo tuyển dụng liên bang Mỹ, `PositionSeries=2210`, `market=US_FEDERAL` | **6.739** | 01–10/2026 | 21 khoảng ngày liên tiếp, 01/01–15/10, đều `complete`; không có khe hở giữa các khoảng. |

Tổng dòng thô trong các run được chọn là **21.435**; audit khử **1.729** lần lặp ID nguồn, gồm 1.456 Arbeitnow trùng giữa run thử và run đầy đủ, cùng 273 lần lặp ngay trong run đầy đủ. Không có ID rỗng, ngày đăng không hợp lệ hoặc bản ghi ngoài năm 2026 trong tập đã chọn. Các run USAJOBS thử nghiệm theo tháng bị `partial` và các bản thu trước khi sửa địa điểm/telework vẫn được giữ tại local, nhưng **không** nằm trong audit cuối.

### Phân bố USAJOBS theo tháng

| Tháng 2026 | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 (đến 15/10) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Số thông báo | 500 | 599 | 754 | 747 | 719 | 772 | 771 | 820 | 760 | 297 |

Số tháng 10 là **tháng chưa kết thúc**, không so trực tiếp với tháng trọn vẹn. Khoảng có bản ghi theo USAJOBS không lấp chỗ trống của `GLOBAL`: Remotive chỉ có 15 tin trong 09–10, Arbeitnow chỉ quan sát 10/2026. Khoảng không quan sát **không có nghĩa là 0 nhu cầu**.

## Chất lượng và giới hạn phân tích

- Taxonomy `v0.1` chỉ gán được **1.642/19.706** tiêu đề vào 8 nhóm nghề; **18.064/19.706 (91,7%)** rơi vào `Other IT`. Nhãn này nghĩa là **chưa khớp quy tắc tiêu đề**, không chứng minh tin là nghề IT. Feed Arbeitnow có cả tin ngoài IT; USAJOBS series 2210 có nhiều dạng `IT SPECIALIST` không thuộc 8 nhãn cụ thể. Chưa dùng các số này để suy diễn xu hướng 8 nghề.
- USAJOBS Historic có ngày mở tuyển dụng, ID, cơ quan và địa điểm, nhưng payload kiểm tra không có JD và URL riêng cho từng tin; nguồn truy vấn cùng checksum vẫn ở manifest/record. Không suy ra kỹ năng từ tiêu đề hay tự điền JD.
- Một thông báo USAJOBS có thể có nhiều địa điểm. Bronze giữ toàn bộ `locations_raw` và chuỗi địa điểm không lặp; `country` chỉ được gán nếu mọi địa điểm cùng một quốc gia. `teleworkEligible` chỉ nói đủ điều kiện telework: lưu riêng `telework_eligible`, còn `remote=null` khi Historic JOA không chứng minh vị trí remote.
- Arbeitnow và Remotive là snapshot tin đang có, có thể biến động giữa các ngày thu. Remotive công bố API cho tin active, có độ trễ công bố và yêu cầu ghi nguồn/liên kết; bản ghi Remotive giữ `source_url` để phục vụ attribution. Vì vậy không dùng snapshot để suy ra số lượng tuyển dụng theo các tháng không được quan sát.
- [Điều khoản API Arbeitnow](https://www.arbeitnow.com/terms) yêu cầu đặt liên kết về Arbeitnow.com trên nền tảng dùng API và có thể thu hồi quyền dùng API. Run hiện được giữ local để nghiên cứu; trước khi hiển thị/công bố tin từ nguồn này cần đáp ứng điều kiện dẫn nguồn. Không đưa raw job feed vào GitHub công khai.
- Bản ghi USAJOBS là **thị trường liên bang Mỹ**, không đại diện toàn nước Mỹ hoặc toàn cầu; chuỗi này không so trực tiếp với nguồn API quốc tế hoặc archive Kaggle 2023. Khoảng trống 2024–2025 và khác biệt nguồn/cách đo vẫn giữ cổng dự báo **`NO_GO`**.
- Run Gold `20261004T110131548191Z-e38fa7303cf4` và dashboard JobScope hiện vẫn dùng snapshot 666 dòng cũ. Dữ liệu mới ở Bronze/audit, **chưa** được nghiệm thu vào Silver/Gold hoặc giao diện. Cần sàng lọc phạm vi nghề, kiểm chứng taxonomy trên mẫu gán nhãn và quyết định nguồn nào phù hợp trước khi tạo Gold mới.

## Thay đổi và bằng chứng tái lập

- Bộ thu Arbeitnow theo toàn bộ `links.next`, có giới hạn trang, retry/backoff và loại ID lặp ngay lúc thu cho **các run sau**. Run đầy đủ ở lần này được tạo trước bản sửa khử trùng nên audit xử lý 273 ID lặp mà không sửa run bất biến.
- Bộ thu Remotive dùng endpoint đầy đủ, giữ `publication_date`, `source_url`, `collected_at` và checksum. Bộ thu USAJOBS Historic tách đường Bronze `data/bronze/us_federal/historic/runs/`, giữ `positionOpenDate`, `usajobsControlNumber`, tất cả địa điểm, cờ telework độc lập và `market=US_FEDERAL`.
- Audit trong `src/collection/audit_2026_bronze.py` kiểm tra hash/manifest, khử trùng theo `(source, source_record_id)`, tổng hợp nguồn × thị trường × tháng × nghề, liệt kê tháng không quan sát và kiểm tra 21 khoảng USAJOBS liên tiếp. File kết quả là [`docs/data/2026_ingestion_audit.json`](../data/2026_ingestion_audit.json), SHA-256 `e3325b36bc841002c012a5b37b47089de00da218eefb78391c14ef1a2c1e4e92`.
- Dữ liệu Bronze dung lượng lớn nằm local và được `.gitignore` bỏ qua; audit, mã, test và báo cáo là các tệp có thể đưa vào Git. Không chỉnh sửa run Bronze/Gold đã khóa trước đó.

### Kiểm thử ngày 15/10/2026

| Kiểm tra | Kết quả |
|---|---|
| `python -m pytest -q tests/test_2026_collectors.py tests/test_phase02_ingestion.py tests/test_phase02_identity.py` | **14 passed**, 0 failed (0,44 s). Bao gồm ngày đăng đúng nguồn, pagination, run bất biến, khử ID lặp, hash/manifest, phát hiện khoảng ngày thiếu, telework và nhiều địa điểm. |
| Kiểm tra audit trên 23 run thực | **Đạt**: 19.706 ID duy nhất; tổng các ô nguồn–tháng bằng 19.706; 21 khoảng USAJOBS `complete`, nối từ 01/01 đến 15/10; 0 ID/ngày lỗi. 6.739 bản ghi liên bang có `remote=null`, 1.392 tin có nhiều địa điểm. |

Log local: `tmp/2026_ingestion/collector_tests.log`, `tmp/2026_ingestion/audit_verify.log`, `tmp/2026_ingestion/federal_semantics_verify.log`. Đây là kiểm thử collector/audit; **không** phải kiểm thử ETL/Gold/dashboard với 19.706 tin mới.

## Việc cần làm tiếp

1. Lấy mẫu gán nhãn độc lập theo từng nguồn, đặc biệt `Other IT`, để đo precision/recall và chọn quy tắc lọc tin IT. Ưu tiên tách `IT SPECIALIST` thành nhãn có ý nghĩa nếu phù hợp Final Plan; giữ nguyên raw Bronze.
2. Thu Arbeitnow/Remotive theo lịch nhiều kỳ, lưu thời điểm thu và đối chiếu thay đổi ID; tránh diễn giải số tháng 01–08 của `GLOBAL` là 0.
3. Sau khi chốt phạm vi nguồn và taxonomy, tạo run Silver/Gold mới riêng; chỉ đổi dashboard sang run đó khi audit và nghiệm thu đạt. Tiếp tục giữ `US_FEDERAL` tách biệt.
4. Xét lại cổng dự báo bằng dữ liệu so sánh được qua thời gian, tiêu chí chất lượng và future holdout của Final Plan. Trạng thái hiện tại vẫn **`NO_GO`**.

## Tài liệu nguồn

- [Arbeitnow Job Board API](https://www.arbeitnow.com/blog/job-board-api)
- [Arbeitnow Terms — mục API](https://www.arbeitnow.com/terms)
- [Remotive API và điều kiện ghi nguồn](https://github.com/remotive-com/remote-jobs-api), [Remotive API page](https://remotive.com/remote-jobs/api)
- [USAJOBS Historic API](https://developer.usajobs.gov/api-reference/get-api-historicjoa), [USAJOBS API terms](https://developer.usajobs.gov/guides/terms-of-service)
