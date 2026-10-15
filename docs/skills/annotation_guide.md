# Hướng dẫn gán nhãn độc lập cho mẫu M4

Mẫu local `tmp/m4_annotation_sample.csv` gồm 95 tin từ audit Bronze 2026, lấy ngẫu nhiên có seed 42 theo nguồn × title khớp/chưa khớp. File chứa JD từ API nên giữ local, không commit hoặc chia sẻ công khai khi chưa kiểm tra điều khoản nguồn. Các cột `predicted_*` là output taxonomy v0.1; người gán nhãn cần **ẩn các cột này khi đọc** để giảm thiên lệch.

## Cột cần điền

| Cột | Quy tắc |
|---|---|
| `is_it` | `1` nếu tin tuyển vị trí CNTT trong phạm vi nghiên cứu; `0` nếu ngoài phạm vi. Không suy ra chỉ từ `Other IT`. |
| `gold_occupation` | Nếu `is_it=1`, chọn đúng một trong 8 nhóm ở `configs/job_title_mapping_v0.json` hoặc `Other IT` nếu là IT nhưng ngoài tám nhóm. Nếu `is_it=0`, dùng `Out of scope`. |
| `gold_skills` | Danh sách canonical skill ID trong `configs/skills_v0.json`, ngăn bằng `;`, chỉ khi JD thực sự nhắc đến kỹ năng. Để trống khi JD không có hoặc không đủ bằng chứng; không suy từ title. |
| `annotator` | Mã/người gán nhãn; để trống nghĩa là chưa hoàn thành và không tính vào metric. |
| `annotation_notes` | Ghi trường hợp mơ hồ, JD thiếu, ngữ cảnh phủ định hoặc từ viết tắt. |

USAJOBS Historic trong mẫu không có JD gốc đáng tin cậy; có thể gán nhãn phạm vi/nghề từ title và thông tin nguồn, nhưng **không** dùng các hàng không có description để đo skill extraction. Gán nhãn hai lượt độc lập bằng hai bản sao CSV, so bất đồng và tạo một bản phân xử. Không sửa `source`, ID, title, description hoặc `predicted_*` của mẫu.

Sau phân xử:

```powershell
python -m src.skills.label_eval evaluate --labels tmp/m4_annotation_sample.csv --output tmp/m4_evaluation.json
```

Report tách `title_coverage`, accuracy/macro-F1 nghề (chỉ trong phạm vi IT), precision/recall/F1 skill micro trên JD có description, số tin ngoài phạm vi và cỡ mẫu từng nguồn. Nếu một nguồn hoặc nhãn không có đủ ví dụ, ghi `null`/cỡ mẫu thay vì suy diễn độ chính xác. Chỉ đề xuất sửa taxonomy sau khi xem lỗi từng nguồn; đổi version cấu hình và tái tạo ETL/Gold bằng run mới.
