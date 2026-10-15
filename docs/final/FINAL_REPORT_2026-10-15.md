# Báo cáo hoàn thiện phần triển khai và trạng thái nghiệm thu

**Dự án:** BigData Job Analy · **Ngày:** 15/10/2026 · **Phạm vi MVP:** phân tích mô tả tin tuyển dụng IT quốc tế theo nguồn, nghề, kỹ năng, tháng. Thị trường Việt Nam được đóng băng theo Final Plan. Dự báo chưa đủ bằng chứng (`NO_GO`).

## 1. Câu hỏi, phương pháp và sản phẩm

Dự án trả lời trong **mẫu đã thu thập**: nguồn nào có quan sát, các nhóm nghề xuất hiện bao nhiêu lần, kỹ năng nào được ghi nhận trong từng nghề và tỷ lệ quan sát thay đổi ra sao theo tháng. Luồng xử lý gồm Bronze bất biến và manifest → Spark làm sạch, dedup, provenance → năm bảng Gold mô tả → Parquet/MongoDB → dashboard JobScope. Dashboard phân biệt tháng không quan sát với tỷ lệ bằng 0, và giữ `source_tags` khác `extracted_from_jd`.

Đầu ra bàn giao: mã nguồn collector/ETL/Gold/serving/dashboard, cấu hình taxonomy, audit JSON, bộ kiểm thử, [README](../../README.md), [sơ đồ tiến độ](../planning/PROJECT_PROGRESS_DIAGRAM_2026-10-15.md), [nội dung slide](PRESENTATION.md) và [kịch bản demo](DEMO_SCRIPT.md). Bronze và Parquet dung lượng lớn, MongoDB local cùng log chạy nằm trên máy thực nghiệm; repository chứa hash/audit để đối chiếu và hướng dẫn tái tạo.

## 2. Dữ liệu và chất lượng

| Tập | Số liệu đã kiểm chứng | Ý nghĩa |
|---|---:|---|
| Archive local 2023 | 785.741 Bronze | File lịch sử, một năm; không đại diện toàn thị trường. |
| API snapshot dùng trong Gold | 666 Bronze | Arbeitnow và Remotive, phạm vi `partial/scoped`. |
| ETL local đã khóa | 786.407 input → 786.300 Silver | 1 quarantine, 106 trùng identity; provenance 1:1. |
| Gold đã khóa | 15 market, 127 occupation, 234 skill evidence, 4.538 skill stats, 4.538 skill trends | Chỉ phân tích đã quan sát; [audit](../data/phase03_analytics_audit.json) chứa checksum. |
| Bronze 2026 mới | 19.706 ID nguồn duy nhất từ 23 run | Arbeitnow 12.952, Remotive 15, USAJOBS Historic 6.739; `US_FEDERAL` tách riêng. |

[Audit Bronze 2026](../data/2026_ingestion_audit.json) ghi 21 khoảng USAJOBS hoàn chỉnh từ 01/01 đến 15/10, còn Arbeitnow và Remotive là snapshot đang hoạt động. 18.064/19.706 title (91,7%) rơi vào `Other IT` của taxonomy v0.1; nhãn này chỉ báo không khớp quy tắc, không xác nhận IT. Đợt Bronze mới được hiển thị trên một trang kiểm kê riêng; chưa chuyển thành Silver/Gold. Mẫu **95 tin** theo nguồn × title matched/unmatched nằm local tại `tmp/m4_annotation_sample.csv` để gán nhãn độc lập. [Công cụ đánh giá](../../src/skills/label_eval.py) tách coverage khỏi precision/recall/F1; hiện **0/95 đã gán nhãn**, vì vậy không có metric chất lượng M4 được công bố.

## 3. HDFS và Spark ETL

HDFS Docker NameNode + một DataNode đã chạy. Đường tích hợp mới sao chép Bronze đã xác minh manifest lên `hdfs://namenode:8020/bigdata_job_analy/phase02_etl/<run_id>`, Spark đọc JSON từ URI HDFS và ghi Silver/provenance local. Run `88b3bb76201d40ee80aa8a49b32944c9` dùng fresh Bronze `20261004T075332383635Z-c9fddef628d7`: **666 input = 666 valid + 0 quarantine = 661 Silver + 5 duplicate identity**, provenance **661**. [Audit HDFS ETL](../data/m2_hdfs_etl_audit.json) ghi SHA-256 manifest, HDFS URI, Spark/Java và checksum output. Đây là minh chứng HDFS→ETL→Silver thực, riêng với run Gold chính.

HDFS FSCK cho đường run trên trả `HEALTHY`, một file/một block, **0 missing, 0 corrupt, 0 under-replicated** sau khi đặt replica 1 cho đường đó. Cấu hình một DataNode là lab **không chịu lỗi node**; các run HDFS cũ có thể còn under-replicated. M2 vẫn cần thu fresh nhiều kỳ, giám sát ổn định API và chấp thuận cấu hình lab. [Review M2 trước đó](../reviews/M2_HDFS_REVIEW_2026-10-15.md) lưu smoke archive đầy đủ 785.741 và fresh 666.

## 4. Analytics, serving và dashboard

Gold run `20261004T110131548191Z-e38fa7303cf4` có manifest SHA-256 `2b37892022882e834b5437555c5c567aa2ab31103dc1d581b9b2f18cd9e7c74d`. MongoDB local database `jobscope` chứa đủ năm collection Gold. [Mongo serving audit](../data/mongo_serving_audit.json) pin run, manifest và SHA-256 canonical row từng bảng. Publisher kiểm tra Parquet trước, ghi/đọc lại từng collection và chỉ công bố metadata run sau khi cả năm bảng đạt. Dashboard ở backend Mongo tải theo run được audit pin và đối chiếu digest với audit đã commit; không chọn run mới nhất.

JobScope có **6 trang**: Tổng quan; Nhóm nghề; Kỹ năng & xu hướng; So sánh nghề; Dự báo & bằng chứng; Dữ liệu 2026. Trang cuối chỉ tóm tắt Bronze và cảnh báo giới hạn. Hai backend dùng cùng Gold run. Kiểm thử AppTest khi dùng Mongo mở trang tổng quan và `NO_GO` không lỗi; server local cổng 8502 trả HTTP health 200. [Runbook](../planning/dashboard_runbook.md) có lệnh chạy.

## 5. Quyết định dự báo

[Hồ sơ M7 `NO_GO`](../reviews/M7_NO_GO_ACCEPTANCE.md) đối chiếu [gate Gold](../data/phase03_analytics_audit.json): giữa 2023-01 và 2026-10 có **32 tháng không quan sát** trong run Gold; 19 ô nghề–tháng dưới 30 tin; các nguồn/cách đo không có chuỗi chung đã hiệu chỉnh; taxonomy chưa có nhãn độc lập. Bronze 2026 mới không lấp các thiếu hụt này vì snapshot và USAJOBS có phạm vi khác. Do đó M6 feature/label tương lai và model M7 không được mở. Không có Macro-F1, confusion matrix hoặc nhãn dự báo hợp lệ để báo.

Theo Final Plan, nhánh M7 có thể nghiệm thu bằng `NO_GO` có bằng chứng. Hồ sơ đã soạn, nhưng chưa có quyết định của nhóm/giảng viên. Khi có dữ liệu nhiều kỳ và đánh giá taxonomy, cần xét lại gate trước khi thiết kế rolling-origin backtest.

## 6. Kiểm thử ngày 15/10/2026

| Lớp | Lệnh/kiểm tra | Kết quả |
|---|---|---|
| Pipeline trong container Spark/HDFS | `python -m pytest -q tests --ignore=tests/test_dashboard.py --ignore=tests/test_mongo_gold.py` | **37 passed**, 1 cảnh báo Arrow fallback; gồm test M4 evaluator. |
| Dashboard/serving trong `.venv-dashboard` | `python -m pytest -q tests/test_dashboard.py tests/test_mongo_gold.py` | **14 passed**. |
| HDFS→ETL live | Fresh Bronze 666 → Silver/provenance; tạo audit bằng `src.processing.hdfs_etl_audit` | **Đạt**, số dòng và checksum khớp. |
| HDFS FSCK run ETL | `/bigdata_job_analy/phase02_etl/88b3bb76201d40ee80aa8a49b32944c9` | `HEALTHY`, 0 missing/corrupt/under-replicated sau `setrep 1` riêng run. |
| MongoDB live | Publish/readback Gold 5 bảng; loader đối chiếu serving audit | **Đạt**, row count 15/127/234/4.538/4.538. |
| Dashboard backend Mongo | AppTest overview/forecast; GET `/_stcore/health` cổng 8502 | **0 exception**, HTTP **200**. |
| M4 sample | `sample` và `evaluate` trên mẫu local | 95 dòng; 0 nhãn độc lập, trạng thái `awaiting_independent_labels`. |

Các test trên chứng minh luồng kỹ thuật và phép tính fixture; chúng chưa đo tính đại diện thị trường, độ chính xác taxonomy hay vận hành nhiều kỳ.

## 7. Điểm mạnh, điểm yếu và việc cần khắc phục

**Điểm mạnh:** provenance và manifest/hash theo run; dedup theo source identity; HDFS→Spark ETL chạy thật; Gold có mẫu số và scope rõ; MongoDB/Parquet đọc cùng run; dashboard không dựng forecast khi gate thất bại; Bronze 2026 tách thị trường và tháng thiếu.

**Điểm yếu còn lại:** archive chỉ năm 2023, API fresh chưa có nhiều snapshot, USAJOBS chỉ liên bang Mỹ, taxonomy v0.1 có coverage title thấp, chưa có nhãn JD độc lập, bản clone Git không có raw/Gold/Mongo, HDFS lab chỉ một DataNode, quyền sử dụng/attribution từng nguồn cần được rà lại trước công bố dữ liệu thô. Các lỗi phát hiện sau demo được ghi riêng để sửa ở vòng tiếp theo; những điều kiện dữ liệu này là cổng nghiên cứu và nghiệm thu, không thể đổi tên thành “lỗi giao diện”.

**Việc cần làm bởi nhóm/giảng viên:**

1. Hai người gán nhãn độc lập mẫu JD local, phân xử bất đồng; chạy evaluator và quyết định taxonomy/phạm vi IT. Giữ raw Bronze bất biến. Chưa publish Gold mới trước bước này.
2. Thu Arbeitnow/Remotive theo lịch nhiều kỳ; kiểm tra coverage, duplicate, độ trễ và thay đổi điều khoản nguồn. Tách US_FEDERAL khi phân tích.
3. Chấp thuận hoặc yêu cầu bổ sung bằng chứng M2 (một DataNode), M3/M5 dataset, M7 nhánh `NO_GO`, M8/M9 demo; ghi biên bản có run ID/hash.
4. Khôi phục artifact trên máy bàn giao, chạy kịch bản demo, trình bày và ký nghiệm thu M10. Nếu dự báo vẫn `NO_GO`, trình bày kết quả quan sát và giới hạn như trong báo cáo này.

## 8. Lệnh tái lập chính

```powershell
# Dashboard Parquet
./run_dashboard.ps1

# Publisher MongoDB local và dashboard Mongo
./.venv-dashboard/Scripts/python.exe -m src.serving.mongo_gold
$env:JOB_GOLD_BACKEND = 'mongo'
./run_dashboard.ps1 -Port 8502

# Tạo mẫu gán nhãn từ 23 Bronze run local
python -m src.skills.label_eval sample --output tmp/m4_annotation_sample.csv
# Sau khi người đánh giá điền nhãn
python -m src.skills.label_eval evaluate --labels tmp/m4_annotation_sample.csv --output tmp/m4_evaluation.json
```

Đường HDFS live cần Docker Compose tại `C:\Users\KIM LONG\docker-hdfs\docker-compose.yml` và Bronze run local. Lệnh chạy cụ thể cùng run ID trong [demo script](DEMO_SCRIPT.md). Một bản clone GitHub đơn lẻ không có dữ liệu lớn để tái chạy ngay.
