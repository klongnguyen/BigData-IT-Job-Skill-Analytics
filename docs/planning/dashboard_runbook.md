# Chạy dashboard JobScope

Dashboard Streamlit đọc 5 bảng Gold đã được xác minh từ Parquet hoặc MongoDB, không cần Spark/Java khi xem web. Có 6 chuyên mục: Tổng quan, Nhóm nghề, Kỹ năng & xu hướng, So sánh nghề, Dự báo & bằng chứng, Dữ liệu 2026. Chuyên mục cuối đọc audit Bronze tổng hợp, không trộn dữ liệu mới vào Gold.

## Cài và chạy trên Windows

Từ thư mục gốc repository (Python 3.11):

```powershell
python -m venv .venv-dashboard
./.venv-dashboard/Scripts/python.exe -m pip install -r requirements-dashboard.txt
./run_dashboard.ps1
```

Mở <http://127.0.0.1:8501>. Giữ terminal đang chạy; Ctrl+C để dừng. Nếu PowerShell không cho chạy script, dùng lệnh tương đương, không cần đổi execution policy:

```powershell
./.venv-dashboard/Scripts/python.exe -m streamlit run dashboard/app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true
```

Nếu cổng đang có ứng dụng khác, chọn `./run_dashboard.ps1 -Port 8502`. App chỉ lắng nghe trên máy này. `requirements-dashboard.txt` khóa bộ thư viện UI đã kiểm tra, tách khỏi bộ Spark của Phase 02.

### Backend MongoDB

Trên máy có MongoDB chạy ở `mongodb://127.0.0.1:27017`, publish Gold run đã khóa rồi bật backend Mongo:

```powershell
./.venv-dashboard/Scripts/python.exe -m src.serving.mongo_gold
$env:JOB_GOLD_BACKEND = 'mongo'
./run_dashboard.ps1 -Port 8502
```

Có thể đặt `JOB_MONGO_URI` và `JOB_MONGO_DB` (mặc định `jobscope`). Publisher kiểm tra Parquet, ghi và đọc lại năm collection, tạo `docs/data/mongo_serving_audit.json`. Chạy lại cùng run kiểm tra idempotent; nếu dữ liệu Mongo khác nguồn đã khóa, lệnh thất bại. Loader Mongo cần Gold audit và Mongo serving audit, xác minh hash/số dòng trước khi hiển thị; Parquet chỉ cần trên bước publish, không cần trên máy chỉ đọc Mongo. URI có mật khẩu nên đặt qua biến môi trường, không ghi vào Git.

## Artifact bắt buộc

`docs/data/phase03_analytics_audit.json` xác định `run_id` và SHA-256 của manifest. App resolve `data/gold/global/runs/<run_id>/manifest.json` từ thư mục repo hiện tại, bỏ qua đường dẫn tuyệt đối của máy cũ trong audit/manifest.

Với Parquet, phải có đúng 5 thư mục `market_stats`, `occupation_stats`, `skill_evidence_stats`, `skill_stats`, `skill_trends` của run đã khóa. Mỗi lần tải, loader kiểm tra hash manifest, metadata, hash và danh sách file output, số dòng và khóa/schema của từng bảng. Với Mongo, loader dùng thêm [serving audit](../data/mongo_serving_audit.json) và hash canonical row từng collection. Không tự chọn thư mục mới nhất và không thay bằng dữ liệu giả khi artifact thiếu hoặc sai checksum. Những Parquet này nằm ngoài Git; clone mới phải khôi phục đúng run hoặc tái tạo Gold trước khi publish Mongo.

Cách tạo lại Gold từ ETL manifest/checksum: xem [báo cáo Phase 03, Lệnh chạy lại](../reviews/PHASE_03_ANALYTICS_REPORT.md#lệnh-chạy-lại). Chạy pipeline trong môi trường Spark riêng, chỉ chuyển audit/Gold đã publish thành công sang dashboard. Tùy chọn `JOB_ANALYTICS_AUDIT` cho phép chọn audit khác; run vẫn phải nằm trong cấu trúc Gold của workspace.

## Demo gợi ý

1. Tổng quan → Archive 2023 → 785.639 tin, 629.764 tin có kỹ năng, 12 tháng quan sát.
2. Kỹ năng & xu hướng → Data Engineer → SQL → 131.898 / 200.880 = 65,66%.
3. Đổi sang Arbeitnow → Software Engineer → Python → 28 / 47 = 59,57%; đọc cảnh báo snapshot partial.
4. Bỏ chọn tất cả tháng hoặc nghề → thông báo không có quan sát. Chọn lại để tiếp tục.
5. Dự báo & bằng chứng → NO_GO / Insufficient evidence và các kiểm tra gate, 32 tháng thiếu trong toàn run.
6. Dữ liệu 2026 → 19.706 ID Bronze theo nguồn/tháng; giải thích 91,7% title chưa khớp và US_FEDERAL riêng.

## Contract số liệu

- Mỗi lần chỉ chọn một nguồn. Kỹ năng chọn riêng một `skills_origin`; taxonomy được khóa theo manifest.
- Tỷ lệ nhiều tháng = tổng tử số / tổng mẫu số. Mẫu số nghề đọc từ `occupation_stats`, kể cả job thiếu skill; không cộng mẫu số lặp trên mỗi skill hoặc lấy trung bình các tỷ lệ tháng.
- `share_in_source` dùng tổng số tin của nguồn/tháng; `share_in_selected_scope` dùng tổng tin của các nghề được chọn.
- Coverage kỹ năng không phải accuracy. Country/experience chưa có phân bố đã kiểm định. Không cộng distinct companies theo tháng thành distinct companies cả kỳ.
- Điểm 0 có thật trong Gold giữ 0. Tháng thiếu hoặc bỏ chọn là NaN, line chart `connectgaps=False`. Delta chỉ hiển thị nếu Gold đánh dấu hai tháng quan sát liên tiếp; tháng trước có thể nằm ngoài lựa chọn hiện tại.
- Quyết định forecast lấy từ run đã khóa; đổi filter không tự xét lại gate. Chưa có pipeline phục vụ forecast ngay cả khi một run tương lai ghi GO.
- Trang forecast hiển thị kiểm tra gate cho toàn run; ngày xử lý Gold khác với tháng cuối của nguồn. Đây là dữ liệu snapshot, không phải feed đang cập nhật trực tiếp.

## Kiểm thử

```powershell
./.venv-dashboard/Scripts/python.exe -m pip install pytest==9.1.1
./.venv-dashboard/Scripts/python.exe -m pytest tests/test_dashboard.py tests/test_mongo_gold.py -q
git diff --check
```

Tests tạo Parquet fixture riêng, không phụ thuộc dữ liệu lớn local: sửa checksum/mất file/thừa file/sai row count/schema/key/gate bị từ chối, tỷ lệ có trọng số, phân tách nguồn/evidence, zero khác missing, và Streamlit AppTest cho 6 trang/filter/empty state. Test Mongo kiểm tra thứ tự row/digest canonical; lần chạy live ngày 15/10/2026 đã publish và đọc lại năm bảng Gold trong MongoDB local. Các test pipeline Phase 01–03 chạy bằng môi trường Spark hiện có theo `requirements-phase02.txt` (Windows: TEMP/TMP trỏ thư mục ngắn có thể ghi).

## Giới hạn nghiệm thu

Đây là demo descriptive local với Parquet và MongoDB serving. Đường HDFS→Spark ETL→Silver đã chạy một run fresh, nhưng M2 còn thu thập nhiều kỳ và nghiệm thu cấu hình lab. Kiểm định taxonomy độc lập, xác minh nguồn/license, nghiệm thu M8/M9 và M10 vẫn còn mở. Không phát hành forecast hoặc metric model.
