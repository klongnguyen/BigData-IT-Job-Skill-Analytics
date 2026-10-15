# Nội dung trình bày dự án (10 slide) — BigData Job Analy

Tài liệu này là bản nội dung chi tiết bám sát [đề cương 10 slide](PRESENTATION_OUTLINE_2026-10-15.md). Mọi số liệu được khóa theo hồ sơ audit ngày 15/10/2026.

---

## Slide 1: Đặt vấn đề và Mục tiêu Đồ án
* **Tên đồ án:** BigData IT Job & Skill Analytics (`JobScope`).
* **Câu hỏi nghiên cứu:** Trong các nguồn tin tuyển dụng đã thu thập, cơ cấu nhóm nghề và kỹ năng IT phân bổ ra sao theo thời gian? Tỷ lệ yêu cầu các kỹ năng chính là bao nhiêu?
* **Phạm vi trả lời:** Phân tích mô tả trên tập mẫu thu thập thực tế; **không** suy diễn khống thành quy mô toàn bộ thị trường lao động.

## Slide 2: Kiến trúc Hệ thống Dữ liệu Lớn
* **Quy trình luồng dữ liệu:**
  $$\text{Bronze (Raw Ingestion)} \longrightarrow \text{Spark ETL (Clean/Dedup/Scope)} \longrightarrow \text{Silver + Provenance} \longrightarrow \text{Gold (Mô tả)} \longrightarrow \text{JobScope Dashboard}$$
* **Hạ tầng phân tán:**
  * HDFS Storage: Lưu trữ dữ liệu thô Bronze, kiểm chứng trên Docker cluster thực nghiệm.
  * Apache Spark: Xử lý dữ liệu lớn, làm sạch, tách scope và chuẩn hóa theo taxonomy.
  * Serving Layer: Hỗ trợ Parquet tốc độ cao cho Gold 2026 và MongoDB cho Gold Archive 2023.

## Slide 3: Nguồn dữ liệu & Tính chất mẫu thu thập
* **Dữ liệu lịch sử (Archive 2023):** Giữ nguyên vẹn làm mốc đối chiếu trong namespace riêng.
* **Dữ liệu năm 2026 (Snapshot Ingestion):**
  * `GLOBAL`: Snapshot từ Arbeitnow (1.621 tin - tháng 10) và Remotive (10 tin - tháng 9 & 10).
  * `US_FEDERAL`: Dữ liệu việc làm chính phủ liên bang Hoa Kỳ từ USAJOBS (PositionSeries 2210 - tháng 1 đến 10/2026).
* **Nguyên tắc toàn vẹn:** Phân tách rõ ràng giữa `GLOBAL` và `US_FEDERAL`, không gộp chung mẫu số nhằm tránh sai lệch khung chọn mẫu.

## Slide 4: Tầng Bronze 2026 — Tiếp nhận và Lưu trữ thô
* **Kết quả kiểm toán Bronze:**
  * 23 runs được ghim cố định qua [2026_silver_input_selection.json](../data/2026_silver_input_selection.json).
  * Tổng **21.435** bản ghi thô; trích xuất **19.706** ID nguồn duy nhất; loại bỏ **1.729** bản ghi trùng lặp.
* **Tính bất biến (Immutability):** Dữ liệu thô nguyên vẹn, đối soát bằng mã băm SHA-256 trong tệp audit.

## Slide 5: Tầng Silver 2026 — Làm sạch, Khử trùng lặp và Phân định Scope
* **Kết quả phân loại (Run `10d0710787d2402186356858d3331e50`):**
  * **8.370** tin IT in-scope (`Silver analytical`) đi kèm **8.370** bản ghi truy xuất nguồn gốc (`provenance 1:1`).
  * **548** tin ngoài ngành IT (`excluded`) được lưu trữ riêng.
  * **10.788** tin chưa đủ bằng chứng định danh (`unresolved`) được cách ly để theo dõi lineage.
  * **0** bản ghi lỗi định dạng (`quarantine`).
* Không suy diễn các tin `unresolved` là non-IT; loại bỏ khỏi mẫu số phân tích để bảo đảm tính chuẩn xác.

## Slide 6: Chuẩn hóa Nghề nghiệp & Kỹ năng (Taxonomy & Policy)
* Áp dụng Taxonomy v0.2 và Chính sách định danh IT Scope Policy v1.
* Quy tắc gán nhóm nghề chặt chẽ: Chỉ phân loại vào 8 nhóm IT trọng điểm khi tiêu đề và mô tả có từ khóa đối soát rõ ràng; nhóm `Other IT` chỉ giữ lại khi thỏa mãn điều kiện tuyển dụng công nghệ (đặc thù USAJOBS series 2210).
* Bộ mẫu kiểm nghiệm 175 dòng được hỗ trợ rà soát bằng AI (`AI-assisted`), ghi nhận minh bạch hạn chế chưa phải tập ground-truth độc lập từ con người.

## Slide 7: Tầng Gold 2026 — Các bảng phân tích mô tả
* **Cấu trúc 5 bảng phân tích (Run `20261015T144634600577Z-8d531796a5f6`):**
  * `market_stats` (13 dòng), `occupation_stats` (66 dòng), `skill_evidence_stats` (66 dòng), `skill_stats` (401 dòng), `skill_trends` (401 dòng).
* **Kiểm toán số liệu thống nhất:** Tổng `job_count` ở các bảng nghiệp vụ khớp chính xác **8.370**.
* **Độ chính xác thống kê:** Tháng không có dữ liệu được ghi nhận là khoảng trống (gap), không tự ý điền giá trị 0; mẫu số tính tỷ lệ kỹ năng luôn gắn liền với tổng số tin của từng nhóm nghề tương ứng.

## Slide 8: Ứng dụng Trực quan hóa JobScope Dashboard
* **Tính năng giao diện Streamlit (6 trang chuyên biệt):**
  * Hỗ trợ bộ lọc phân cấp an toàn: `Dataset → Market → Source → Month → Occupation`.
  * Trang khảo sát luồng dữ liệu Bronze → Silver → Gold trực quan.
  * Khám phá phân bổ kỹ năng, nhóm nghề, tương quan nhu cầu tuyển dụng.
* **Xử lý thiếu bằng chứng:** Với nguồn USAJOBS chưa có trích xuất kỹ năng chuẩn hóa, hệ thống hiển thị trạng thái thiếu chứng cứ minh bạch, tuyệt đối không tạo tỷ lệ giả.

## Slide 9: Mô hình Dự báo Máy học (Spark MLlib) & Kiểm soát Cổng Dữ liệu
* **Mô hình Dự báo Xu hướng Kỹ năng (Spark MLlib / RF Pipeline):**
  * Huấn luyện mô hình Random Forest trên 785.741 tin tuyển dụng của chuỗi 12 tháng liên tục năm 2023.
  * Trích xuất các đặc trưng chuỗi thời gian: Lags ($t, t-1, t-2, t-3$), trung bình trượt 3 tháng, độ dốc xu hướng (rolling slope) và động lượng (momentum).
  * Đánh giá kiểm thử Rolling-Origin (T9–T11/2023): Đạt **Độ chính xác (Accuracy): 64,0%**, **Macro F1-Score: 0,623** cho bài toán phân loại 3 lớp: `Growing` (Tăng trưởng), `Stable` (Ổn định), `Declining` (Suy giảm).
  * Dự báo kỳ kế tiếp (T1/2024) cho 349 cặp nghề–kỹ năng hiển thị trực tiếp trên Dashboard.
* **Kiểm soát Cổng Dữ liệu 2026 (Quality Gate Audit):**
  * Với dữ liệu 2026, do bị gián đoạn 32 tháng (2024–2025 không có dữ liệu) và nguồn mới chỉ là snapshot ngắn hạn, hệ thống kích hoạt quyết định **`NO_GO`** để bảo đảm tính trung thực khoa học, không tạo số liệu dự báo giả.

## Slide 10: Tổng kết Đồ án & Đóng góp
* **Kết quả đạt được:**
  * Xây dựng thành công kiến trúc Big Data hoàn chỉnh, kiểm thử tự động đạt 100% (Spark container & Dashboard).
  * Quy trình xử lý dữ liệu minh bạch, có kiểm toán SHA-256, phân định ranh giới thị trường nghiêm ngặt.
  * Dashboard phục vụ phân tích trực quan trực tiếp từ Big Data Storage.
* **Hướng phát triển:** Thiết lập cơ chế tự động thu thập định kỳ dài hạn để tích lũy chuỗi thời gian liên tục phục vụ cho bài toán dự báo trong tương lai.
