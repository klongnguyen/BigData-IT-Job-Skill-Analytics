# Đề cương 10 slide báo cáo BigData Job Analy

**Thông điệp chính:** đường Bronze → Silver → Gold → dashboard 2026 đã chạy và được audit; kết quả là mô tả mẫu thu thập, dự báo giữ `NO_GO`. Bản PPTX `BigData_Job_Analy_Final_2026-10-15_v2.pptx` hiện còn số liệu cũ, cần cập nhật theo outline này trước khi trình chiếu.

| Slide | Tiêu đề | Nội dung/visual cần đưa lên |
| ---: | --- | --- |
| 1 | Bài toán | Câu hỏi về nghề và kỹ năng IT trong tin tuyển dụng đã thu; phạm vi mẫu, không suy rộng toàn thị trường. |
| 2 | Kiến trúc | Sơ đồ Bronze + manifest → Spark Silver/provenance → Gold → JobScope; HDFS lab là đường tích hợp có audit. |
| 3 | Nguồn dữ liệu | Archive 2023 riêng; Arbeitnow/Remotive `GLOBAL` snapshot 2026; USAJOBS 2210 `US_FEDERAL` Jan–Oct. |
| 4 | Bronze 2026 | 23 run pin; 21.435 raw → 19.706 ID duy nhất; 1.729 duplicate; manifest/SHA. |
| 5 | Silver và lineage | 8.370 analytical = 8.370 provenance; 548 excluded; 10.788 unresolved; 0 quarantine; run và SHA. |
| 6 | Taxonomy và scope | Taxonomy v0.2, policy v1, `Other IT` in-scope; mẫu 175 AI-assisted chỉ để soát policy, chưa có ground truth độc lập. |
| 7 | Gold analytics | Năm bảng 13/66/66/401/401; tổng ba bảng đếm tin 8.370; market-safe denominator và gap tháng thiếu. |
| 8 | Dashboard | Demo Dataset → Market → Source → Month → Occupation; pipeline 2026, biểu đồ và chứng cứ nguồn; USAJOBS chưa có kỹ năng chuẩn hóa. |
| 9 | Cổng dự báo | `NO_GO`: không đủ chuỗi nghề/nguồn và đánh giá ngoài mẫu; không model/prediction/metric. |
| 10 | Kết luận và phần còn lại | ~90% deliverables; Gold 2026 + dashboard đã audit; cập nhật slide, kiểm tra demo trên máy báo cáo, đánh giá độc lập, nghiệm thu. |

Ghi chú cho người thuyết trình: dùng [demo script](DEMO_SCRIPT.md), [Gold audit](../data/2026_gold_run_audit.json) và [báo cáo cuối](FINAL_REPORT_2026-10-15.md) làm nguồn số. Không cộng `GLOBAL` với `US_FEDERAL` để tính tỷ lệ chung; không gọi unresolved là non-IT; không gắn nhãn “human ground truth” cho review bằng AI.
