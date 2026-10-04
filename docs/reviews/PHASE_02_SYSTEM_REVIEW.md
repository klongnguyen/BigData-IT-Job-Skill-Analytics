# Review Phase 02 — Data Ingestion & Big Data Storage

**Ngày review:** 04/10/2026  
**Phạm vi:** ingestion dữ liệu lịch sử và dữ liệu mới, Bronze, Spark ETL, Silver, provenance, quarantine và tiêu chí M2 trong Final Plan.  
**Phiên bản đối chiếu:** `main` tại `5362d41`; working tree sạch trước khi tạo báo cáo này. Review C2C đã đọc độc lập workspace và đối chiếu lại các phát hiện với mã, tài liệu và artifact tại máy.

> **Lưu ý cập nhật 04/10/2026:** Các phát hiện bên dưới ghi trạng thái tại thời điểm review ban đầu. Phần **Trạng thái sau khắc phục** cuối tài liệu ghi rõ hạng mục đã sửa, kết quả chạy mới và cổng HDFS còn mở.

## Kết luận

**Repository có mã ingestion/Spark ETL cục bộ và các artifact Bronze/Silver từ lần chạy trước; ETL theo mã hiện tại chưa được chạy lại hoặc xác minh, nên chưa đủ bằng chứng nghiệm thu M2.** Final Plan yêu cầu một đường **HDFS Bronze → Spark Read** và thống kê đầu vào/đầu ra tái lập được (`FINAL_PLAN_BigData_IT_Job_Market_Skill_Forecasting.md:1100–1133`). Mã hiện dùng đường dẫn thư mục cục bộ và Spark `local[*]`; chưa có artifact HDFS end-to-end hoặc manifest của lần chạy ETL theo mã hiện tại. `README.md` vẫn đánh dấu Phase 02 hoàn thành và nêu 50.087 dòng Silver, trong khi `docs/planning/phase_01_02_summary.md` đã rút lại số liệu cũ như bằng chứng nghiệm thu.

**Đề xuất trạng thái:** *Prototype cục bộ đã triển khai; M2 đang chờ xác thực và HDFS*. Không dùng số 50.087 hoặc sự hiện diện của file Silver để kết luận bản ETL mới đã chạy thành công.

## Điểm mạnh

| Hạng mục | Bằng chứng và giá trị |
|---|---|
| Có đường xử lý thực tế | `src/ingestion/historical_ingestion.py` đọc CSV theo dòng và chia batch; `src/ingestion/fresh_ingestion.py` thu snapshot từ hai nguồn API; `src/processing/spark_etl.py` đọc Bronze và viết Silver Parquet theo năm/tháng. Đây là nền tảng tốt để kiểm thử kỹ thuật. |
| Định danh và truy vết đã được cải thiện trong mã | Collector hiện sinh `ingestion_id`, `collected_at`, `raw_checksum`, `source_record_id`; ETL sinh `job_id` xác định từ nguồn và ID nguồn, có thiết kế bảng provenance riêng. |
| Xử lý dữ liệu thiếu thận trọng hơn | ETL giữ trường không có nguồn ở `null`, tách `posted_at` với `collected_at`, quarantine dòng thiếu/sai thời gian hoặc title/identity; không dùng ngày thu thập để thay ngày đăng. |
| Có cơ chế bảo vệ output ETL | `run_etl()` ghi vào staging, từ chối thay output mặc định, và chỉ thay khi có `--replace-existing` kèm backup/rollback. Thiết kế này hạn chế ghi đè nhầm Silver. |
| Hợp đồng dữ liệu rõ hơn | `src/common/schema.py`, `docs/data/schema_mapping.md` và `docs/data/deduplication_rules.md` mô tả 18 trường Silver, provenance và ranh giới giữa quy tắc dedup đã có với fuzzy/repost còn ở kế hoạch. |

## Điểm yếu và vấn đề cần khắc phục

**Mức ưu tiên:** P0 = chặn nghiệm thu M2 hoặc khiến trạng thái nghiệm thu được công bố sai; P1 = lỗi/rủi ro dữ liệu cần xử lý trước khi chạy lại để nghiệm thu; P2 = cải thiện khả năng vận hành và tái lập.

| Ưu tiên | Phát hiện | Tác động | Việc cần làm |
|---|---|---|---|
| **P0** | **Trạng thái tài liệu mâu thuẫn.** `README.md:184–211,296–320` ghi Phase 02 ✅ và Silver 50.087 dòng. Final Plan `:1128` chỉ đóng M2 sau khi có bằng chứng HDFS và số liệu tái lập; `docs/planning/phase_01_02_summary.md:19–21` nói kết quả Bronze/Silver cũ không còn là số liệu nghiệm thu. | Người đọc có thể hiểu prototype là hệ thống đã được nghiệm thu. | Đồng bộ README, summary và bảng trạng thái theo một quyết định: M2 đang mở; mọi số cũ phải ghi rõ là kết quả lịch sử chưa xác nhận lại. |
| **P0** | **Chưa chứng minh luồng HDFS → Spark.** Các hằng `BRONZE_*_DIR` và `SILVER_GLOBAL_DIR` trong `src/processing/spark_etl.py:30–36` là đường dẫn local; session dùng `.master("local[*]")` ở `:94`. Không tìm thấy cấu hình/command đọc và ghi HDFS có thể chạy trong repo. | Chưa có bằng chứng nghiệm thu P2-01, P2-08, P2-09, P2-11 và M2 theo Final Plan; việc cài đặt HDFS ngoài repo chưa được kiểm tra. | Tạo một luồng thực nghiệm HDFS Bronze → Spark đọc → output, lưu lệnh, cấu hình, log, checksum và đếm dòng. Cho đến khi có bằng chứng, giữ M2 chưa hoàn thành. |
| **P1** | **Bronze lịch sử có thể bị ghi đè hoặc trộn nhiều lần chạy.** `src/ingestion/historical_ingestion.py:51–65` luôn ghi `historical_batch_001.json`, `002.json`... bằng chế độ `w`. Chạy lại với ít batch hơn để lại file batch cũ ở số thứ tự cao hơn. | Có thể mất dữ liệu Bronze cũ hoặc tạo tập đầu vào pha trộn mà không nhận ra. | Ghi từng run vào thư mục bất biến theo run ID, ghi staging rồi publish; manifest liệt kê checksum file gốc, từng batch, số dòng và tổng dòng. Kiểm thử chạy lại với giới hạn khác nhau. |
| **P1** | **Snapshot mới không có trạng thái nguồn bền vững.** `src/ingestion/fresh_ingestion.py:36–89` ghi subset nếu một nguồn lỗi, nhưng lỗi chỉ được `print`; tên file chính xác đến giây nên có thể trùng trong cùng giây. Mỗi nguồn hiện chỉ được gọi một lần, chưa có cơ chế xác nhận đã thu hết các trang dữ liệu nếu API phân trang. | Không phân biệt được batch đầy đủ và batch thiếu nguồn; có thể ghi đè snapshot hoặc đếm thiếu. | Dùng tên run duy nhất và output bất biến; lưu manifest theo nguồn gồm trạng thái, thời điểm, số dòng, checksum, lỗi, số trang/trạng thái hoàn tất; kiểm thử lỗi từng nguồn và chạy hai lần liên tiếp. |
| **P1** | **Artifact hiện có không chứng minh ETL mới.** Kiểm kê tại máy thấy Bronze historical **50.000** dòng, fresh **267** dòng (Arbeitnow 250, Remotive 17). Hai file Bronze này thuộc định dạng cũ: historical thiếu `source_record_id` và `raw_checksum`; fresh dùng `raw_id` và thiếu `source_record_id`/`raw_checksum`. Có Silver Parquet nhưng chưa có output tại đường provenance và quarantine mặc định. Trong khi đó `spark_etl.py:319,347–348` hiện ghi cả ba output. | Không thể xác nhận số dòng, ID/provenance 1:1, quarantine và kết quả dedup của phiên bản mã hiện tại từ artifact cũ. | Chạy ETL trên input cố định vào thư mục output mới, lưu manifest/checksum, assert số dòng trước/sau, khóa `job_id` duy nhất, provenance 1:1, quarantine theo lý do và nguồn. Giữ dữ liệu cũ để so sánh; không ghi đè output mặc định khi review. |
| **P1** | **Dedup chưa bảo đảm khóa Silver duy nhất qua snapshot.** `spark_etl.py:296–300,330–333` tạo `job_id` từ `source + source_record_id`, nhưng chọn survivor theo `job_hash` từ company, title, location và ngày đăng. Nếu cùng source ID thay title/location/ngày, hai `job_hash` khác nhau có thể giữ hai dòng chung `job_id`; ngược lại hai tin khác ID nhưng trùng bốn thuộc tính có thể bị gộp. Đây là rủi ro suy ra từ quy tắc mã, chưa phải lỗi đã đo trên output. | Sai cardinality Silver/provenance và số tin khi tái thu thập. | Quy định thứ tự dedup theo source identity và content; tạo bộ ca kiểm thử duplicate, update, repost và trùng thuộc tính; assert `job_id` duy nhất, báo số dòng bị loại theo lý do. |
| **P1** | **Thiếu regression test Phase 02.** `tests/` chỉ có `test_phase01_feasibility.py`, thực chất là script diagnostic, không có assertion test cho ingestion/ETL. `python -m pytest -q` trả về `no tests ran` (pytest exit code 5). | Không phát hiện tự động lỗi rerun, ghi đè, partial source, schema, timestamp, dedup hoặc rollback. | Bổ sung test nhỏ cho collector/manifest và integration test Spark trên fixture cố định; lưu kết quả test cùng run manifest. |
| **P2** | **Môi trường và log khó tái lập.** `requirements.txt` không khóa phiên bản; Spark session đặt fallback Windows `JAVA_HOME`/`HADOOP_HOME` và `local[*]` (`spark_etl.py:88–99`); quá trình ingest chủ yếu dùng `print`. | Khó tái chạy và đối chiếu kết quả giữa máy hoặc lần chạy. | Khóa/ghi phiên bản Python–PySpark–Java, cấu hình đường dẫn qua tham số hoặc biến môi trường, lưu log có run ID và manifest môi trường. |

## Kiểm tra đã thực hiện và giới hạn

- Đọc mã, tài liệu, git status, Bronze JSON và sự hiện diện của các output; review C2C xác nhận workspace `BigData_Job_Analy`, commit `5362d41` và các phát hiện chính.
- Đếm trực tiếp hai file Bronze đang có: **50.267** dòng đầu vào, gồm 50.000 historical và 267 fresh. Đây là **kiểm kê file hiện có**, không phải một lần chạy ingestion/ETL mới.
- `python -m pytest -q`: **không có test được thu thập**. Không dùng script diagnostic Phase 01 làm bằng chứng kiểm thử Phase 02.
- Thử đọc Silver bằng Spark theo chế độ chỉ đọc nhưng SparkContext không khởi tạo được trên máy này do lỗi Netty/loopback. Do đó **chưa xác minh được số dòng Silver hiện tại**, schema thực tế hay quan hệ Silver–provenance. Lỗi khởi tạo này chưa đủ để kết luận ETL có lỗi trên môi trường khác.
- Không gọi lại API, không ghi đè Bronze/Silver, không chạy HDFS hoặc ETL end-to-end trong lượt review này.

## Thứ tự khắc phục và điều kiện đóng M2

1. **Sửa trạng thái công bố ngay:** README và mọi bảng tiến độ phải phân biệt prototype cục bộ với M2 được nghiệm thu; bỏ số liệu Silver chính xác nếu chưa có manifest kiểm chứng.
2. **Làm Bronze tái lập được:** output bất biến theo run, manifest nguồn/batch/checksum/count, đánh dấu partial source và không để batch cũ lẫn lần chạy mới.
3. **Kiểm định pipeline trên input cố định:** test dữ liệu hợp lệ và lỗi; đo `Bronze = valid + quarantine`, `valid = Silver + dedup_removed` theo định nghĩa đã chốt; assert uniqueness và provenance 1:1; chạy lại cho kết quả ổn định.
4. **Chứng minh tiêu chí storage:** lưu một lần chạy HDFS Bronze → Spark Read → output với log/manifest đọc được và thống kê đầu vào/đầu ra. Nếu HDFS không còn là tiêu chí môn học, sửa Final Plan bằng quyết định phạm vi rõ ràng trước khi đóng M2.
5. **Sau khi có bằng chứng**, cập nhật summary, README và biên bản nghiệm thu bằng cùng run ID, checksum, phiên bản môi trường, số dòng và đường dẫn artifact; khi đó mới chuyển trạng thái M2 sang hoàn thành.

## Trạng thái sau khắc phục — 04/10/2026

| Phát hiện ban đầu | Trạng thái hiện tại |
|---|---|
| README công bố M2 hoàn thành và số Silver cũ | **Đã sửa tài liệu.** README và summary phân biệt kết quả local mới với M2/HDFS; số 50.087 cũ được ghi là chưa xác minh theo mã mới. |
| HDFS → Spark | **Còn mở.** Đã có `src/processing/hdfs_smoke.py` yêu cầu URI `hdfs://` thật và test `hdfs` riêng. Máy này chưa có dịch vụ/URI HDFS hoạt động; không có evidence HDFS runtime. |
| Bronze historical ghi đè/trộn batch | **Đã sửa và test.** Mỗi lần ingest tạo `runs/<run_id>/` bất biến, publish sau staging, kèm checksum và số dòng từng file. Test chạy lại với giới hạn khác chứng minh không trộn batch. |
| Fresh partial failure và trùng tên file | **Đã sửa và test.** Manifest ghi status/coverage/page/count/error theo nguồn; run ID có UUID, dữ liệu không được ghi đè; tất cả nguồn lỗi tạo run `failed` không có success batch. Pagination chỉ ghi `complete` khi payload chứng minh trang cuối. |
| Silver cũ không chứng minh ETL mới | **Đã tạo bằng chứng local mới.** ETL trên 50.000 dòng historical từ CSV gốc và 666 dòng fresh scoped sinh 50.659 Silver và 50.659 provenance, loại 7 snapshot trùng `job_id`, quarantine 0. Manifest/checksum và output ở `tmp/phase02_acceptance/`; output legacy không bị thay. Đây là input có phạm vi giới hạn, chưa phải nghiệm thu M2. |
| Dedup theo `job_hash` gây gộp sai/ID trùng | **Đã sửa và test fixture Spark.** Survivor chọn theo `job_id` và timestamp/checksum, có tie-break `source_url`/`ingestion_id` khi snapshot trùng giây; hai native ID khác nhau vẫn giữ riêng; test xác nhận uniqueness và provenance 1:1 qua hai lần chạy. |
| Không có regression test Phase 02 | **Đã sửa.** `python -m pytest -q` thu thập và chạy assertion tests: **10 passed, 1 skipped**. Có test bác manifest khai sai số dòng dù checksum file đúng. Skip là test HDFS cần server thật, không được tính là bằng chứng M2. |
| Môi trường và log khó tái lập | **Cải thiện.** `requirements-phase02.txt` khóa phiên bản đã chạy; ETL manifest ghi phiên bản Python/PySpark/Spark/Java, taxonomy/config checksum, input/output checksum và metric. Môi trường HDFS vẫn chưa được nghiệm thu. |

**Kết luận mới:** các lỗi code Phase 02 đã được sửa và pipeline local đã qua test + một lần chạy có manifest; **M2 vẫn OPEN** cho đến khi phép thử HDFS → Spark thành công trên dịch vụ HDFS thật. Không dùng kết quả local scoped để tuyên bố đủ dữ liệu dự báo.
