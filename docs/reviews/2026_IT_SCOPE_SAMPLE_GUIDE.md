# Kiểm mẫu phạm vi nghề IT 2026 — đã rà soát bằng AI

**Cập nhật 15/10/2026:** 175 dòng đã được gán nhãn theo policy AI-assisted. Xem [báo cáo kết quả](2026_IT_SCOPE_AI_REVIEW_2026-10-15.md). Các tên cột `manual_label`/`review_reason` là schema cũ, không có nghĩa đây là nhãn của người đánh giá.

## Mẫu cần review

- File: [`../data/2026_it_scope_sample.csv`](../data/2026_it_scope_sample.csv)
- Manifest mẫu: [`../data/2026_it_scope_sample.manifest.json`](../data/2026_it_scope_sample.manifest.json)
- 175 tin: Arbeitnow 40 tiêu đề khớp taxonomy + 40 `Other IT`; Remotive toàn bộ 15; USAJOBS 40 khớp + 40 `Other IT`.
- Mẫu được chọn tất định theo SHA-256 của `(source, source_record_id)` sau khử trùng ID. Ưu tiên observation từ run `complete` khi cùng ID xuất hiện ở run `partial` và `complete`.
- `manual_label`, `in_scope_it`, `review_reason` hiện chứa kết quả rà soát AI. Manifest ghi `reviewer_type=AI`; không coi đây là ground truth độc lập.

## Cách kiểm tra lại

Khi kiểm tra lại một dòng, đọc tiêu đề, nguồn, địa điểm và liên kết gốc nếu có. Đối chiếu:

1. `manual_label`: một trong 8 nhóm nghề của dự án, `IT ngoài 8 nhóm`, `ngoài IT`, hoặc `chưa đủ thông tin`.
2. `in_scope_it`: `1` nếu thực sự thuộc IT, `0` nếu ngoài IT; để trống nếu chưa đủ thông tin.
3. `review_reason`: một lý do ngắn, nhất là với tiêu đề mơ hồ, taxonomy sai hoặc tin `Other IT` thực sự thuộc IT.

Một tin thuộc IT nhưng ngoài 8 nhóm cần được ghi rõ, không tự ép vào một nhóm gần nhất. Với USAJOBS, `PositionSeries=2210` là bằng chứng phạm vi của nguồn; nhãn nghề cụ thể vẫn cần chứng cứ từ tin.

Đây là kiểm mẫu phục vụ quyết định rule. Khi chưa có nhãn độc lập và quy trình đánh giá M4 đầy đủ, không gọi tỷ lệ đồng thuận trong mẫu là precision, recall hoặc F1. Kết quả đã chỉ ra cả false positive và IT bị bỏ sót; cần sửa taxonomy/rule trước khi chạy Silver production.

Iteration 2 chỉ hoàn tất kiểm mẫu. Chưa tạo Silver/Gold production hay chuyển dashboard sang Gold mới. Forecast gate tiếp tục `NO_GO`.
