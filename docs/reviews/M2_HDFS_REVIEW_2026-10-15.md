# Review M2 — HDFS Docker đối chiếu Final Plan

**Ngày review:** 15/10/2026 (Asia/Saigon)

**Quyết định:** **Cổng kỹ thuật HDFS → Spark đã đạt**; **M2 Global Data Ingestion Ready vẫn mở, chờ chốt nghiệm thu toàn mốc**. Review này không thay đổi cổng dự báo `NO_GO`.

## 1. Phạm vi và tiêu chí

[Final Plan, Phase 2](../../FINAL_PLAN_BigData_IT_Job_Market_Skill_Forecasting.md#phase-2--data-ingestion--big-data-storage) yêu cầu đường `Source → HDFS Bronze → Spark Read`, các task P2-01 đến P2-11 và chỉ đánh dấu M2 hoàn tất sau khi có bằng chứng đọc/ghi HDFS cùng thống kê đầu vào/đầu ra tái lập được. Kế hoạch cũng ghi việc thu thập định kỳ, độ ổn định nguồn và kiểm tra dữ liệu nhiều tháng chưa được xác nhận; bảng tuần 4 nêu đường HDFS → Spark → Silver. Vì thế review tách **phép thử HDFS đã qua** khỏi **mức sẵn sàng vận hành và nghiệm thu M2**.

Mã [`hdfs_smoke.py`](../../src/processing/hdfs_smoke.py) upload file Bronze vào `hdfs://`, dùng Spark đọc JSON, ghi Parquet lên HDFS và dùng Spark đọc lại để so số dòng với Bronze manifest. Parquet này là **output smoke từ Bronze**, chưa phải Silver chuẩn hóa của ETL.

## 2. Bằng chứng đã đối chiếu

| Bronze run | Phạm vi nguồn | HDFS evidence | SHA-256 Bronze manifest | Số dòng Spark đọc → Parquet đọc lại |
|---|---|---|---|---:|
| Historical `20261004T103235056713Z-0811f6613d3c` | `complete/full_input` cho toàn bộ file archive local năm 2023 | [`20261014T173656587825Z-9aee99826405`](../../data/manifests/hdfs/hdfs_smoke_20261014T173656587825Z-9aee99826405.json) | `48492bae64ab9e68a0ab93bc96814ced958a6ca7cc78af0e26e21bbd4207480a` | **785.741 → 785.741** |
| Fresh `20261004T075332383635Z-c9fddef628d7` | `partial`: Arbeitnow 650/2 trang; Remotive 16/1 trang | [`20261014T173838902471Z-542df647c8cf`](../../data/manifests/hdfs/hdfs_smoke_20261014T173838902471Z-542df647c8cf.json) | `a9f14604497ca92f9579c71ff96f4e440565ac454c2f3f87de7cc91d5cc95b51` | **666 → 666** |

Hai evidence có `status=completed`, `hdfs_uri=hdfs://namenode:8020`, `spark_version=4.2.0`, `spark_master=local[2]`, Java `17.0.20.1`, URI Bronze/Parquet riêng theo run ID. Review tính lại SHA-256 của cả hai manifest nguồn trên volume `/workspace`, đối chiếu `total_rows`, `status` và `coverage`; đều khớp. Hai manifest 1.000 dòng còn lại trong `data/manifests/hdfs/` là smoke trên input historical `partial/limited`, không dùng để thay bằng chứng full archive.

Kiểm tra độc lập ngày 15/10:

| Kiểm tra | Kết quả |
|---|---|
| Docker Compose | NameNode và DataNode đang chạy; `dfsadmin -report` thấy **1 live DataNode**, **0 missing block**, **0 corrupt block**. |
| HDFS FSCK theo hai run chính | Cả historical và fresh trả `HEALTHY`, không có block mất/hỏng. |
| Live test trong container có `PHASE02_HDFS_URI=hdfs://namenode:8020/bigdata_job_analy` | `python -m pytest -q tests/test_phase02_hdfs.py`: **2 passed, 0 skipped**. Một test bác `file://`; một test tạo round-trip HDFS thật. |
| Regression pipeline cùng container | `python -m pytest -q tests --ignore=tests/test_dashboard.py`: **27 passed, 0 skipped**, 1 cảnh báo Arrow fallback. |
| Quyết định dự báo | [Audit Phase 03](../data/phase03_analytics_audit.json) và [hồ sơ M7](M7_NO_GO_ACCEPTANCE.md) vẫn `NO_GO`; không tạo model/prediction. |

Log kiểm thử mới nằm tại `tmp/m2_hdfs_live_test_2026-10-15.log` và `tmp/m2_pipeline_regression_2026-10-15.log` trên máy local. Output đọc-only `dfsadmin -report`, FSCK cho hai run và replication của một file Bronze được lưu tại `tmp/m2_hdfs_health_2026-10-15.log`; cả bốn lệnh trả exit code 0. Không cộng 2 test HDFS lần chạy riêng vào 27 test regression vì chúng đã nằm trong suite đó.

**Giới hạn độ bền HDFS:** `dfsadmin -report` vẫn ghi block under-replicated (**110** sau các lần chạy live test ngày 15/10), dù không có block missing/corrupt. FSCK của run historical có 88 và fresh có 2 block under-replicated. Một file Bronze được kiểm tra yêu cầu replication factor **3** trong khi cluster chỉ có **1** DataNode; mặc dù `hdfs-site.xml` trên NameNode đặt mặc định 1, các file đang lưu vẫn báo yêu cầu 3. Các đường đọc/ghi đã hoạt động, nhưng chưa thể coi đây là cấu hình chịu lỗi. Cần thống nhất replication factor trên client/cluster hoặc bổ sung DataNode rồi kiểm tra lại.

## 3. Ma trận task Phase 2

| Task Final Plan | Kết quả review | Bằng chứng hoặc phần còn thiếu |
|---|---|---|
| P2-01 Hadoop / HDFS Setup | **Đạt trong lab** | Docker NameNode + 1 DataNode, URI HDFS thật; còn giới hạn replica. |
| P2-02 Spark / PySpark Setup | **Đạt** | Spark 4.2.0 `local[2]` đọc/ghi HDFS; live test đạt. |
| P2-03 Bronze / Silver / Gold Structure | **Đạt ở local** | Bronze manifest, Silver/provenance và Gold run đã có; smoke HDFS không tạo Silver/Gold. |
| P2-04 Historical Data Loader | **Đạt cho file local** | Run `complete/full_input` 785.741 dòng của archive 2023. |
| P2-05 Fresh Data Collector | **Đạt một phần** | Snapshot 666 dòng, hai nguồn `partial/scoped`; chưa chứng minh thu định kỳ hay độ ổn định. |
| P2-06 Metadata | **Đạt cho run đã chọn** | Manifest nguồn/run ID/SHA, URI, phiên bản và số dòng trong evidence. |
| P2-07 Validation | **Đạt về integrity của smoke** | SHA manifest và input/output count khớp; độ đầy nguồn qua nhiều kỳ chưa xác nhận. |
| P2-08 Bronze Storage | **Đạt** | File Bronze thực được upload dưới URI `hdfs://.../bronze`. |
| P2-09 Spark Read Test | **Đạt** | Spark đọc JSON từ HDFS, count bằng Bronze manifest. |
| P2-10 Logging | **Đạt cho smoke** | Evidence JSON có thời gian, run ID, URI, SHA, môi trường, input/output; log vận hành dài hạn chưa có. |
| P2-11 End-to-End Test | **Đạt cho HDFS smoke** | Bronze local → HDFS → Spark JSON → HDFS Parquet → Spark đọc lại; chưa chứng minh đường HDFS → ETL → Silver. |

## 4. Kết luận và điều kiện đóng M2

**HDFS technical acceptance gate: PASSED.** Bằng chứng đã mạnh hơn trạng thái “HDFS chưa chạy” trong review cũ. Tuy nhiên, **M2 vẫn OPEN/CONDITIONAL**, vì nhãn “Global Data Ingestion Ready” trong Final Plan bao gồm collector và vận hành nguồn; hiện chưa có bằng chứng job fresh định kỳ, chất lượng/độ ổn định qua nhiều tháng, và đường tích hợp HDFS → Spark ETL → Silver nêu tại kế hoạch tuần 4. Không có biên bản nhóm/giảng viên chấp thuận giới hạn này như điều kiện nghiệm thu M2.

Việc cần làm để xin chốt M2:

1. Chạy và lưu một đường **HDFS Bronze → Spark ETL → Silver/provenance** có manifest, checksum, số dòng input/valid/quarantine/dedup/output; hoặc ghi quyết định phạm vi của nhóm/giảng viên rằng smoke hiện tại đủ cho P2-11/M2.
2. Thu fresh theo lịch qua nhiều kỳ, theo dõi lỗi/độ trễ/số trang/duplicate theo nguồn và phân biệt ngày không quan sát với số tin bằng 0. Không nâng snapshot 666 dòng thành coverage toàn API.
3. Khắc phục tình trạng under-replicated hoặc ghi rõ cấu hình lab 1 DataNode được chấp nhận; kiểm tra lại `dfsadmin`/`fsck`.
4. Ghi biên bản nghiệm thu M2 kèm đúng hai run ID và evidence JSON ở mục 2. Cổng forecast vẫn `NO_GO` cho đến khi các điều kiện dữ liệu/model riêng được đáp ứng.

Docker Compose cho môi trường review nằm ngoài repository; các Bronze run lớn và log ở `tmp/` cũng là artifact local. Hai evidence JSON chính hiện ở workspace, chưa tự suy ra rằng người khác có thể tái lập chỉ từ bản clone Git.

## 5. Bổ sung Bronze 2026 sau lượt smoke

[Audit 2026](../data/2026_ingestion_audit.json) đã xác minh 19.706 ID nguồn duy nhất trong 23 run được chọn, gồm 6.739 tin USAJOBS liên bang Mỹ trong 21 khoảng ngày liên tiếp và 12.967 bản ghi snapshot Arbeitnow/Remotive. Collector/identity test **14 passed**. Các run này mới ở Bronze local; phép thử HDFS và ETL/Gold ở mục 2 vẫn dùng các run cũ. Vì vậy kết quả mới tăng bằng chứng thu thập, nhưng **không tự đóng M2** hay thay kết luận HDFS → ETL → Silver còn thiếu.
