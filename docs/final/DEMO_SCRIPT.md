# Kịch bản demo JobScope · 2026

## Chuẩn bị trên máy trình bày

1. Kiểm tra đúng Gold 2026 run `20261015T144634600577Z-8d531796a5f6` và Gold 2023 run `20261004T110131548191Z-e38fa7303cf4` trên máy local. Các Parquet lớn không nằm trong Git. So SHA của [Gold audit 2026](../data/2026_gold_run_audit.json) với [catalog](../data/dashboard_gold_catalog.json); không chọn run mới nhất tùy ý.
2. Chạy từ thư mục gốc dự án:

   ```powershell
   .\.venv-dashboard\Scripts\python.exe -m streamlit run dashboard/app.py --server.port 8501
   ```

3. Mở <http://127.0.0.1:8501>, xác nhận trang tổng quan tải được. Nếu báo thiếu Gold, khôi phục **đúng** run đã pin theo [runbook](../planning/dashboard_runbook.md).

## Trình bày trong 6–8 phút

1. **Bài toán và kiến trúc:** Bronze bất biến → Spark Silver + provenance → Gold mô tả → JobScope. Chỉ mô tả tin trong mẫu thu.
2. **Dữ liệu 2026:** mở trang “Dữ liệu 2026”; chỉ 21.435 raw → 19.706 unique → 8.370 Silver → 5 Gold. Nói rõ 548 excluded và 10.788 unresolved được lưu riêng.
3. **Thị trường:** chọn Dataset “Scoped 2026”, Market `GLOBAL`, Source Arbeitnow 2026; cho thấy 1.621 tin tháng 10. Chuyển Remotive 2026 để thấy 8 tin tháng 9 và 2 tin tháng 10. Chuyển Market `US_FEDERAL`, Source USAJOBS 2210 · US Federal để thấy 6.739 tin tháng 1–10; không cộng tỷ lệ hai market.
4. **Analytics:** mở “Nhóm nghề”; giải thích `Other IT` được giữ khi policy xác nhận in-scope. Mở “Kỹ năng & xu hướng” với Arbeitnow hoặc Remotive; chỉ mẫu số theo đúng market, source, occupation và khoảng trống của tháng thiếu. Với USAJOBS, nêu hiện không có bằng chứng kỹ năng chuẩn hóa, nên trang này không tạo tỷ lệ.
5. **Gold cũ:** chọn Dataset “Legacy / archive 2023”, chỉ dữ liệu vẫn mở được. Không so sánh trực tiếp số tin 2023 và 2026 như cùng khung lấy mẫu.
6. **Dự báo:** mở “Dự báo & bằng chứng”; chỉ `NO_GO` và các check. Không trình bày model, nhãn dự báo hoặc metric giả.
7. **Kết luận:** chỉ [Gold audit](../reviews/2026_GOLD_RUN_AUDIT_2026-10-15.md), [báo cáo cuối](FINAL_REPORT_2026-10-15.md) và [việc còn lại](REPORT_READY_STATUS_2026-10-15.md).

## Câu trả lời ngắn cho phản biện

- **Vì sao 10.788 tin không vào Gold?** Title Arbeitnow chưa đủ bằng chứng để kết luận IT hay ngoài IT; giữ `scope_unresolved` có lineage, không đưa vào mẫu số.
- **USAJOBS đại diện nước Mỹ?** Không. Chỉ PositionSeries 2210 của tuyển dụng liên bang.
- **Có dự báo?** Không. Gate `NO_GO`; chuỗi theo cùng nghề và nguồn chưa đạt ngưỡng, thiếu đánh giá ngoài mẫu.
- **Nhãn scope là ground truth?** Không. Mẫu 175 dòng là AI-assisted title review; cần đánh giá độc lập nếu muốn báo metric taxonomy.

## Kiểm tra cuối trước trình bày

Chạy `python -m pytest -q tests/test_dashboard.py` trong `.venv-dashboard`, kiểm tra các trang không có exception và HTTP local trả 200. Không đổi audit/run ID để làm đẹp demo. Bản PPTX cũ chưa có Gold 2026; chỉnh theo [đề cương 10 slide](PRESENTATION_OUTLINE_2026-10-15.md).
