# Review Phase 01 — Đánh giá hệ thống đã xây dựng

**Dự án:** BigData IT Job Skill Analytics  
**Ngày đánh giá:** 03/10/2026 (Asia/Saigon)  
**Phương pháp:** C2C: ChatGPT đọc repository, lập kế hoạch và review; Codex đối chiếu mã, kiểm kê dữ liệu thực tế và viết báo cáo. Trao đổi bằng tiếng Việt, giữ nhãn giao thức tiếng Anh.  
**Phạm vi:** Phase 01 — Data Feasibility & Project Definition. Ingestion/Spark thuộc Phase 02 chỉ được xem xét để kiểm tra tính nhất quán của hợp đồng dữ liệu Phase 01.

## 1. Kết luận điều hành

Hệ thống có nền tảng thiết kế tương đối rõ: đã có tài liệu phạm vi, câu hỏi nghiên cứu, taxonomy nghề/kỹ năng, thiết kế schema, mẫu dữ liệu, mã collector và profiling. Đã có file lịch sử thật, Bronze và các phân vùng Silver trên máy. Đây là bằng chứng tiến triển thực tế, vượt mức chỉ có ý tưởng.

Tuy nhiên, **Phase 01 chưa nên được nghiệm thu hoàn tất về tính khả thi dữ liệu cho dự báo**. Báo cáo GO cũ dựa trên mẫu lịch sử do chương trình tự sinh và trộn với fresh; kết luận nhiều năm liên tục, có JD lịch sử thật và độ chính xác trích xuất chưa được dữ liệu thật hỗ trợ. Kế hoạch tổng hiện đã nhận diện vấn đề này và mở lại quality gate, nhưng tài liệu nghiệm thu cũ chưa đồng bộ.

| Mục tiêu | Đánh giá hiện tại | Ý nghĩa |
|---|---|---|
| Tiếp tục thử nghiệm collector, ingestion và pipeline | **GO cho prototype** | Có mã và dữ liệu để kiểm thử kỹ thuật; vẫn phải xử lý các lỗi dữ liệu |
| Phân tích mô tả trên nguồn đã kiểm kê | **GO có điều kiện** | Ghi rõ nguồn, cỡ mẫu, năm, phạm vi nghề và nguồn gốc nhãn; không suy rộng thành toàn thị trường |
| Mô tả xu hướng quan sát trong từng nguồn | **Có điều kiện theo chuỗi** | Chỉ dùng các tháng thật có dữ liệu, mẫu số đúng và đủ support; không nối khoảng trống thành xu hướng liên tục |
| Dự báo tương lai / chứng minh Hybrid vượt baseline | **NO-GO ở trạng thái hiện tại** | Chưa chứng minh đủ chuỗi nghề–skill–tháng, nhãn tương lai và backtest phù hợp |
| Đóng Phase 01 với kết luận “đạt 100%” | **QUALITY GATE REOPENED** | Cần cập nhật feasibility dựa trên dữ liệu thật trước khi đóng lại |

NO-GO ở đây là chưa đủ bằng chứng để công bố predictive claims, không có nghĩa toàn bộ dự án không khả thi. Có thể tiếp tục hoàn thiện pipeline và analytics đồng thời bổ sung dữ liệu.

## 2. Bằng chứng đã kiểm chứng trực tiếp

### 2.1. Kiểm kê dữ liệu trên máy

| Đối tượng | Kết quả kiểm tra ngày 03/10/2026 | Giới hạn |
|---|---|---|
| `data/raw/data_jobs.csv` | **785.741 dòng dữ liệu**, 12 tháng từ 01–12/2023 | Không có cột `job_description`; có `job_title`, `job_posted_date`, `job_skills` |
| Bronze historical | `historical_batch_001.json`: **50.000 dòng**, toàn bộ năm 2023 | Chưa đại diện toàn archive; không suy từ số dòng sang độ phủ nghề/tháng |
| Historical sample | **300 dòng**, 2022–2025, **47 tháng khác nhau**, JD trung bình **415,9 ký tự** | Mẫu synthetic: `build_historical_sample()` dựng title, ngày, công ty, lương, skills và JD |
| Fresh sample | **267 dòng**: Arbeitnow 250, Remotive 17; ngày đăng 19/08–19/09/2026 | Một snapshot trên 2 tháng; chưa kiểm tra API còn hoạt động ở ngày review |
| Silver | Thư mục phân vùng `year=2023`, `year=2026` hiện hữu | Không chạy lại Spark, không xác nhận lại số dòng Parquet trong review này |

Số dòng raw theo tháng 2023, tính bằng `csv.DictReader` quét toàn file:

| Tháng | Số dòng | Tháng | Số dòng |
|---|---:|---|---:|
| 01 | 91.822 | 07 | 63.777 |
| 02 | 64.578 | 08 | 75.162 |
| 03 | 64.084 | 09 | 62.359 |
| 04 | 62.919 | 10 | 66.611 |
| 05 | 52.104 | 11 | 64.450 |
| 06 | 61.572 | 12 | 56.303 |

Đây là số dòng trước khử trùng và lọc nghề. Nhiều dòng trong 12 tháng không tự động chứng minh đủ dữ liệu cho từng nghề–kỹ năng, nhiều chu kỳ mùa vụ hoặc horizon dự báo dài.

### 2.2. Tính lại chỉ số bằng hàm đang dùng trong feasibility script

Codex nạp hàm từ `tests/test_phase01_feasibility.py` bằng `runpy`, rồi tính trên mẫu hiện hữu, không gọi hàm ghi đè kết quả.

| Chỉ số | Historical synthetic | Fresh snapshot | Tổng |
|---|---:|---:|---:|
| Số dòng | 300 | 267 | 567 |
| Ánh xạ vào 8 nghề | 300 (100%) | **43 (16,10%)** | 343 (60,49%) |
| Có ít nhất một skill được trích xuất | 300 (100%) | **112 (41,95%)** | 412 (72,66%) |
| Số tháng khác nhau | 47 | 2 | **49** |

`tests/test_results_phase01.json` lưu **50 tháng** và phân bố 2022/2023/2024/2025 = **62/87/69/82**; mẫu hiện tại cho **68/85/64/83**. Tổng dòng vẫn giống nhưng kết quả đã lưu không khớp dữ liệu hiện tại. Do đó phải gắn kết quả với checksum, phiên bản config và thời điểm chạy.

Các tỷ lệ trên là **coverage**, không phải accuracy, precision hay recall. Tỷ lệ fresh thấp có thể do cả nguồn chứa nghề ngoài phạm vi, ngôn ngữ không phù hợp và thiếu alias; chưa có nhãn chuẩn để phân chia chính xác nguyên nhân.

## 3. Điểm mạnh

### 3.1. Bài toán và đầu ra được định nghĩa rõ

`PHASE_01_Data_Feasibility_Project_Definition.md` liệt kê P1-01–P1-20 với đầu ra và tiêu chí. `docs/planning/research_questions.md` đặt phân tích theo occupation–skill–time, có công thức demand rate và các RQ. Cách này giúp nối yêu cầu nghiên cứu với pipeline, thay vì chỉ xây dashboard rồi tìm câu hỏi sau.

Kế hoạch tổng mới nhất đã tách analytics, observed trend và predictive claims, đặt cổng dữ liệu và backtest. Đây là hướng điều chỉnh đúng. Cần xem đó là chuẩn quyết định hiện tại và cập nhật các tài liệu con tương ứng.

### 3.2. Có hợp đồng dữ liệu và phân biệt thời điểm đăng/thu thập

`docs/data/unified_schema.md` có schema 18 trường, nullable và kiểu PySpark; dictionary và mapping có tài liệu riêng. Thiết kế tách `posted_at` khỏi `collected_at` là nền tảng tốt cho phân tích thời gian và truy vết dữ liệu, dù triển khai hiện còn vi phạm khi timestamp thiếu.

### 3.3. Có prototype có thể kiểm tra

Collector và profiler là mã thực, configs tách khỏi mã, mẫu JSON hiện hữu. File raw và Bronze chứng minh đã có dữ liệu đầu vào thực. Pipeline Spark và Silver hiện hữu cho thấy hợp đồng Phase 01 đã được đưa vào bước triển khai tiếp theo; review này không mặc nhiên coi toàn bộ pipeline đã vượt kiểm thử.

### 3.4. Taxonomy ban đầu gọn, dễ giải thích

8 nhóm nghề và dictionary kỹ năng dựa trên alias giúp kiểm tra nguyên nhân match và sửa nhanh. Đây là baseline phù hợp cho đồ án. Config hiện có **42 khóa kỹ năng**, đủ làm điểm khởi đầu; không nên dùng con số 35 trong báo cáo như số lượng hiện hành.

### 3.5. Đã nhận diện một số giới hạn dữ liệu

Profiling có thống kê thiếu lương, HTML, độ dài JD và timestamp; thiết kế cho phép lương nullable. Hướng Global-first, Vietnam frozen trong kế hoạch cập nhật giúp giảm phạm vi triển khai. Điểm mạnh nằm ở việc nhận diện và thiết kế, chưa đồng nghĩa tất cả rủi ro đã được xử lý bằng mã.

## 4. Điểm yếu và tác động

Quy ước: **P0** chặn nghiệm thu dữ liệu/predictive claims; **P1** cần sửa trước khi tin cậy kết quả analytics; **P2** tăng khả năng bảo trì/tái lập.

### F01 — P0: Mẫu synthetic đang được trình bày như dữ liệu lịch sử thật

**Bằng chứng:** `src/collection/collect_samples.py`, hàm `build_historical_sample()`, dùng `random.seed(42)`, ngày ngẫu nhiên 2022–2025 và JD dựng từ template; trường `source` lại là `kaggle_historical_archive`. `docs/planning/go_no_go_report.md` dùng mẫu này để xác nhận chuỗi lịch sử và JD.

**Tác động:** độ phủ nghề, tháng và extraction trên synthetic dễ đạt cao vì dữ liệu được tạo từ chính taxonomy. Không đo được độ khó thực tế và không xác nhận đặc tính file raw.

**Khuyến nghị:** ghi rõ `synthetic` và mục đích fixture; tách khỏi dữ liệu feasibility và ML. Lấy mẫu thật từ raw theo nguồn/nghề/tháng; lưu URL tải, thời điểm, checksum và phương pháp lấy mẫu. Historical tags có thể dùng cho analytics nhưng không gọi đó là extraction từ JD thật.

### F02 — P0: Kết luận chuỗi liên tục và forecasting vượt bằng chứng

**Bằng chứng:** raw thật chỉ năm 2023; fresh sample chỉ 08–09/2026. Feasibility chỉ đếm tháng có dữ liệu, không kiểm tra các tháng vắng hoặc support của mỗi occupation–skill.

**Tác động:** khoảng trống 2024–2025 và đầu 2026 không phải tháng có nhu cầu bằng 0. Ghép archive và snapshot khác nguồn có thể biến sai lệch nguồn thành “concept drift”. RQ yêu cầu 2022–2026 và test 2026 Q3 chưa được thiết kế dữ liệu hiện tại bảo đảm.

**Khuyến nghị:** lập bảng source × occupation × month sau dedup, ghi tháng thiếu là chưa quan sát. Chỉ mở forecast theo cổng mục 21 của Final Plan với dữ liệu thật, train/validation/test theo thời gian và baseline trên cùng tập test. Khi thiếu bằng chứng, hiển thị `Insufficient evidence`.

### F03 — P1: Feasibility script chưa kiểm định độ chính xác

**Bằng chứng:** `tests/test_phase01_feasibility.py` tính counts/coverage và ghi JSON; không có assertions, bộ nhãn độc lập hay ngưỡng pass/fail. `avg_skills_per_job` chia cho số tin có skill, không phải toàn bộ 567 tin. JSON lưu cũ không khớp mẫu hiện hành.

**Tác động:** gọi “match” là “chính xác” và coverage là accuracy có thể làm nghiệm thu sai. Không phát hiện hồi quy hoặc kết quả cũ sau khi dữ liệu/config thay đổi.

**Khuyến nghị:** giữ script như công cụ mô tả, thêm kiểm thử riêng có assertions và mẫu JD thật gán nhãn theo nghề/nguồn. Báo precision/recall/F1, coverage và mẫu số riêng; version hóa taxonomy, dữ liệu và kết quả.

### F04 — P1: Bộ trích xuất và phân loại nghề có lỗi biên/ngữ cảnh

**Kiểm tra bằng hàm hiện có:**

| Input | Kết quả thực tế | Vấn đề |
|---|---|---|
| `C++` | Không có skill | Regex không bắt alias ở cuối chuỗi |
| `C#` | Không có skill | Cùng lỗi biên với dấu đặc biệt |
| `We use Go.` | Không có skill | Dictionary thiếu alias `Go` độc lập |
| `Excel at communication` | `excel` | False positive ngữ cảnh |
| `Senior Backend Software Engineer` | `Software Engineer` | Match đầu tiên thắng; có thể làm mất chuyên môn backend |
| `Sales Representative` | `Other IT` | Không phân biệt ngoài IT với IT chưa nhận diện |

Dictionary hiện thiếu React/Next.js/HTML/CSS dù mẫu synthetic Frontend sử dụng chúng. Các alias ngắn `py`, `ts`, `tf` cần kiểm tra ngữ cảnh; mapping substring phụ thuộc thứ tự config.

**Khuyến nghị:** thêm trường hợp dấu đặc biệt/đầu-cuối chuỗi, phủ định và từ thường vào bộ test. Tách `Out-of-scope` và `Unknown IT`; định nghĩa ưu tiên nghề chuyên biệt và audit các title đa nghĩa. Không suy rằng mọi tin unmatched là phi IT.

### F05 — P1: Timestamp có thể bị thay bằng thời điểm thu thập

**Bằng chứng:** collector gán thời gian hiện tại nếu nguồn thiếu ngày đăng; Remotive bỏ thông tin timezone khi format. Spark parse một format cố định và gán partition năm 2026/tháng 9 khi `posted_at` không parse được.

**Tác động:** ngày thiếu nhìn như ngày thật, tin cũ có thể bị đưa vào nhóm recent. Partition không còn chứng minh posted timestamp hợp lệ. UTC chưa được bảo đảm chỉ bằng việc ghi chữ UTC trong tài liệu.

**Khuyến nghị:** parse timezone rõ ràng; giữ ngày đăng thiếu/không hợp lệ cùng cờ chất lượng và quarantine. Không dùng `collected_at` thay `posted_at`; không gán partition mặc định như thời gian thật. Archive retrospective phải tách thời điểm nhập archive khỏi dữ liệu sẵn có tại cutoff lịch sử.

### F06 — P1: Schema và tài liệu đang không đồng bộ

**Bằng chứng:** `src/common/schema.py` có **14 trường**, thiếu `city`, `market`, `work_mode`, `currency` so với đặc tả **18 trường**. GO report còn ghi 14; scope nói Việt Nam bổ trợ trong khi kế hoạch mới frozen. Profiling vừa báo JD historical 415,9 ký tự vừa kết luận cả hai nguồn >2.000. Historical evaluation mô tả năm/JD khác raw. License giữa evaluation và Final Plan chưa thống nhất.

**Tác động:** module khác nhau có thể dùng hợp đồng khác nhau; người đọc khó xác định đâu là trạng thái thật. License/quyền sử dụng chưa được review này xác minh từ nguồn bên ngoài.

**Khuyến nghị:** một nguồn schema chuẩn, kiểm thử field/type/nullability; cập nhật tài liệu con theo Final Plan. Báo cáo nguồn phải có phiên bản tải, URL và điều kiện sử dụng được xác minh riêng, không chọn license bằng suy đoán.

### F07 — P1: Dedup/provenance chưa đạt thiết kế

**Bằng chứng:** profiler đếm trùng theo title+company. Tài liệu dedup quy định chuẩn hóa chuỗi, giữ bản mới nhất và fuzzy matching; Spark thực tế hash chuỗi chưa chuẩn hóa rồi `dropDuplicates`, không bảo đảm survivor mới nhất. Historical ID dùng `monotonically_increasing_id()`; chưa có triển khai bảng provenance 1:1 như Final Plan yêu cầu.

**Tác động:** phép đếm trùng trong profiling không phải số duplicate chắc chắn; ID không bảo đảm ổn định khi đổi phân vùng/lần chạy. Không phân biệt được description gốc và text dựng từ tags, gây sai đối chứng extraction và truy vết.

**Khuyến nghị:** ID xác định từ định danh nguồn, test rerun; thực thi dedup có quy tắc chọn survivor và test. Giữ provenance `description_origin`, `skills_origin`, taxonomy version, source_record_id và checksum. Nhãn nguồn không được coi là ground truth độc lập của JD không tồn tại.

### F08 — P1: Fresh collector mới chứng minh lấy snapshot

**Bằng chứng:** Arbeitnow gọi một trang, không duyệt pagination; Remotive giới hạn software-dev. Lỗi được catch rồi tiếp tục lưu; nếu hai nguồn đều lỗi có thể ghi JSON rỗng thay snapshot. Collector/API probe dùng `ssl._create_unverified_context()`. Country có giá trị gom `Europe/Other` hoặc `Worldwide`, không phải quốc gia xác định.

**Tác động:** dữ liệu thiên lệch nguồn/ngôn ngữ/remote; không đại diện thị trường toàn cầu. Kết nối HTTPS không xác thực chứng chỉ. Thành công một lần không chứng minh khả năng thu thập định kỳ, retry, rate-limit hay giữ dữ liệu khi lỗi.

**Khuyến nghị:** xác thực TLS; phân trang đúng contract; retry/backoff có giới hạn, status/count/checksum theo batch và không ghi đè snapshot tốt khi lỗi. Lọc nghề có kiểm định, ghi language và source coverage; dùng country unknown khi chưa xác định. Đánh giá lại API hoạt động/điều khoản riêng trước triển khai định kỳ.

### F09 — P2: Quy trình tái lập và trạng thái repository còn yếu

**Bằng chứng:** kết quả test/profiling thiếu run manifest; README vẫn mô tả trạng thái khởi tạo, chưa phản ánh ingestion/Silver. Module analytics/ML có các file `__init__.py`, chưa là bằng chứng hệ thống dự báo hoàn chỉnh. Spark chạy `local[*]` và có mặc định đường dẫn Windows.

**Tác động:** khó tái tạo kết quả trên máy khác hoặc biết báo cáo tương ứng dữ liệu nào. Có Spark local không đồng nghĩa đã kiểm chứng vận hành phân tán/HDFS; không nên dùng cấu trúc thư mục để khẳng định chức năng hoàn thành.

**Khuyến nghị:** hướng dẫn chạy theo thứ tự, môi trường/dependency khóa phiên bản, manifest và metadata benchmark. Crawler dự phòng hiện là thiết kế, chưa được chứng minh vận hành; Việt Nam tiếp tục frozen theo MVP.

## 5. Mức độ hoàn thành các nhóm công việc Phase 01

| Hạng mục | Đã có | Còn thiếu để nghiệm thu |
|---|---|---|
| P1-01–04: scope, RQ, taxonomy | Tài liệu và config | Đồng bộ MVP, thời gian thật, phiên bản taxonomy |
| P1-05–06: historical evaluation | Candidate review, raw thật | Audit đúng file tải: năm, JD, nghề, nguồn, license |
| P1-07–09: fresh/API/fallback | Sample và mã API; thiết kế crawler | Kiểm tra vận hành hiện tại, quyền dùng, pagination, reliability; crawler chưa thực thi |
| P1-10–11: sample/profiling | JSON và profiler | Tách synthetic, profiling raw và phân tầng source/nghề/tháng |
| P1-12–16: schema/dictionary/dedup/time | Tài liệu thiết kế | Contract test, ngày hợp lệ, stable ID, survivor, provenance |
| P1-17–18: normalization/extraction | Hàm rule-based và coverage | Nhãn độc lập, precision/recall, lỗi biên/ngữ cảnh, phân tích theo nguồn |
| P1-19: temporal feasibility | Đếm năm/tháng và raw 12 tháng 2023 | Missing-month audit, support nghề–skill, comparability, backtest |
| P1-20: GO/NO-GO | Báo cáo GO cũ; Final Plan mở lại cổng | Báo cáo quyết định mới dựa trên thực nghiệm tái lập |

Đánh giá tổng thể: **đã xây dựng đáng kể về thiết kế và prototype; còn thiếu bằng chứng nghiệm thu chất lượng dữ liệu và độ tin cậy khoa học**. Không quy đổi số tài liệu hiện hữu thành phần trăm hoàn thành toàn hệ thống.

## 6. Thứ tự cải thiện đề xuất

| Ưu tiên | Công việc | Tiêu chí hoàn thành đo được |
|---|---|---|
| 1 — P0 | Sửa provenance historical và kết luận GO | Không còn dùng mẫu synthetic chứng minh archive; quyết định riêng prototype/analytics/forecast |
| 2 — P0 | Audit nguồn × nghề × tháng | Có manifest/checksum, count trước/sau dedup, tháng thiếu và support từng chuỗi; cổng forecast có kết luận |
| 3 — P1 | Chốt schema/timestamp/ID/provenance | Schema 18 trường thống nhất; rerun ID ổn định; ngày lỗi quarantine; provenance 1:1 |
| 4 — P1 | Đánh giá taxonomy trên dữ liệu thật | Bộ nhãn độc lập, precision/recall/F1 theo nguồn/nghề và kiểm thử lỗi đã nêu |
| 5 — P1 | Củng cố collector và dedup | TLS xác thực, phân trang, không mất snapshot khi lỗi; test survivor/repost/idempotency |
| 6 — P2 | Đồng bộ hồ sơ nghiệm thu | README, scope, evaluation, profiling và GO phản ánh cùng một run/phiên bản |

Ngưỡng support và chất lượng phải được chốt trước khi đánh giá theo Final Plan; không tự chọn ngưỡng sau khi xem kết quả để làm cho dự án đạt GO. Chỉ phát hành dự báo khi baseline/backtest thật chứng minh mục tiêu; nếu không đạt, nghiệm thu analytics kèm giới hạn vẫn là đầu ra hợp lệ.

## 7. Kiểm chứng, giới hạn và tài liệu tham chiếu

**Đã thực hiện:** đọc mã/tài liệu/config; quét toàn bộ CSV raw theo tháng; đếm và kiểm tra keys Bronze; tính lại coverage/year/month/độ dài trên sample bằng hàm hiện hữu; thử các trường hợp title/skill; kiểm tra thư mục Silver. Review C2C dùng chính repository để lập kế hoạch và đối chiếu báo cáo.

**Chưa thực hiện:** gọi lại API, crawl, xác minh license/điều khoản bên ngoài, chạy lại Spark/HDFS, đếm lại Parquet hay gán nhãn benchmark thủ công. Không coi lời mô tả số dòng Silver trong summary là kết quả chạy mới. Báo cáo này là review và đề xuất; chưa sửa mã hệ thống hoặc các báo cáo nghiệm thu cũ.

**Tham chiếu trong repository:**

- `PHASE_01_Data_Feasibility_Project_Definition.md`: baseline P1-01–P1-20.
- `FINAL_PLAN_BigData_IT_Job_Market_Skill_Forecasting.md`: trạng thái dữ liệu hiện tại, provenance và cổng forecast (đặc biệt mục 21).
- `docs/planning/go_no_go_report.md`, `docs/planning/phase_01_02_summary.md`: nghiệm thu cũ cần đối soát.
- `docs/planning/project_scope.md`, `docs/planning/research_questions.md`: phạm vi/RQ.
- `docs/data/historical_data_evaluation.md`, `fresh_data_evaluation.md`, `data_profile.md`: đánh giá nguồn/profiling.
- `docs/data/unified_schema.md`, `data_dictionary.md`, `schema_mapping.md`, `deduplication_rules.md`: hợp đồng dữ liệu.
- `src/collection/collect_samples.py`, `profile_samples.py`, `test_api_sources.py`: collector/profiling/API probe.
- `tests/test_phase01_feasibility.py`, `tests/test_results_phase01.json`: hàm kiểm tra và kết quả cũ.
- `configs/job_title_mapping_v0.json`, `configs/skills_v0.json`, `src/common/schema.py`: taxonomy/schema trong mã.
- `src/ingestion/historical_ingestion.py`, `src/ingestion/fresh_ingestion.py`, `src/processing/spark_etl.py`: đối chiếu Phase 02.

**Khuyến nghị nghiệm thu:** giữ GO cho phát triển prototype, cho phép analytics trong phạm vi dữ liệu đã xác minh; mở lại Phase 01 về nguồn gốc và chuỗi thời gian; giữ NO-GO cho predictive claims tới khi các cổng dữ liệu/backtest đạt yêu cầu.
