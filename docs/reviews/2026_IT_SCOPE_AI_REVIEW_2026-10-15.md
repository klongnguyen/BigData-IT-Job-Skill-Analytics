# Rà soát AI-assisted phạm vi IT — mẫu Bronze 2026

**Ngày:** 15/10/2026 · **Task:** `c2c_2026_to_dashboard`, iteration 2

**Đầu vào:** [mẫu 175 tin](../data/2026_it_scope_sample.csv), [manifest mẫu](../data/2026_it_scope_sample.manifest.json)

**Phương pháp:** AI-assisted semantic title review; `reviewer_type=AI`. Các cột có tên `manual_label` và `review_reason` được giữ vì schema mẫu ban đầu, **không phải nhãn do người đánh giá tạo**. Đây là kiểm tra phạm vi theo tiêu đề, không phải human ground truth hoặc phép đo precision/recall/F1.

## Kết quả

| Nguồn | Số mẫu | IT (`1`) | Ngoài IT (`0`) | Chưa xác định |
|---|---:|---:|---:|---:|
| Arbeitnow · GLOBAL | 80 | 52 | 22 | 6 |
| Remotive · GLOBAL | 15 | 10 | 5 | 0 |
| USAJOBS 2210 · US_FEDERAL | 80 | 80 | 0 | 0 |
| **Tổng** | **175** | **142** | **27** | **6** |

| Nguồn | Đã map: giữ nguyên nhãn | Đã map: sửa nhãn nhưng vẫn IT | Đã map: loại ngoài IT | `Other IT` → IT | `Other IT` → ngoài IT | `Other IT` → chưa xác định |
|---|---:|---:|---:|---:|---:|---:|
| Arbeitnow | 36 | 3 | 1 | 13 | 21 | 6 |
| Remotive | 7 | 0 | 0 | 3 | 5 | 0 |
| USAJOBS 2210 | 33 | 7 | 0 | 40 | 0 | 0 |
| **Tổng** | **76** | **10** | **1** | **56** | **26** | **6** |

Các số trên là **đếm đồng thuận/chuyển nhãn trong một mẫu spot-check chọn tất định**, không ngoại suy thành tỷ lệ sai của toàn bộ Bronze. SHA-256 của CSV sau gán nhãn: `365de636595ce0057a7f056580bb073955731d83470e6cb4d6fb8893d2308caa` (khóa trong manifest). Script [label_2026_it_scope_sample.py](../../scripts/label_2026_it_scope_sample.py) lưu từng quyết định riêng và từ chối chạy trên mẫu có SHA khác hoặc đã có nhãn.

## Dạng taxonomy v0.1 bỏ sót hoặc map rộng

- **Alias nghề bị bỏ sót:** `Full-Stack Entwickler`, `Softwareentwickler`, `Front-end Developer`, `Shopify Developer`, `Full-Stack Rails Engineer`, `RF Machine Learning Engineer`. Những title này có đủ bằng chứng để đưa vào một trong tám nhóm.
- **IT rõ nhưng nằm ngoài tám nhóm:** AI Solutions, kiến trúc Digital Platforms, triển khai phần mềm/EDI, IT Support/POS, Service Desk, QA, Offensive Security, Cybersecurity. Không ép chúng thành Data/Software/DevOps chỉ để tăng coverage.
- **Map quá rộng:** `IT Systems Engineer`, `Infrastructure Engineer`, `Network Systems Engineer`, `Information Security Infrastructure Engineer` không đồng nghĩa DevOps; `Research Scientist / Engineer – Reinforcement Learning Infrastructure` phù hợp ML Engineer hơn Data Scientist. `Weiterbildung: Data Science...` là khóa đào tạo, không phải tin tuyển dụng IT.
- **Ngoài IT xuất hiện trong nguồn chung:** marketing, sales, nhân sự, kế toán, bác sĩ, điện/cơ khí, mỹ thuật game, nội dung và hành chính. Tên công ty công nghệ không tự biến các nghề này thành nghề IT.
- **Title chưa đủ thông tin (6 Arbeitnow):** Product Manager; Initiativbewerbung; Project Manager Real World Data; Technical Support Specialist; Delivery Management Professional Services; AI Data Specialist - French. Cần JD hoặc người đánh giá bổ sung; không tự cho vào Silver IT.

USAJOBS được giữ toàn bộ theo bộ lọc nguồn `PositionSeries=2210`, kể cả tiêu đề chung hoặc `Other IT`. Việc này chỉ xác lập phạm vi **IT liên bang Mỹ**, không chứng minh nghề cụ thể thuộc một trong tám nhóm. Giữ `market=US_FEDERAL`, thời gian và mẫu số riêng; không cộng với `GLOBAL`.

## Đề xuất policy trước Silver production

1. **Arbeitnow/Remotive:** dùng quy tắc title có giải thích và cập nhật alias đa ngôn ngữ cho các nghề rõ ràng. `Other IT` phải qua phân loại riêng: rõ IT thì giữ (`IT ngoài 8 nhóm` nếu ngoài taxonomy), rõ ngoài IT thì `scope_excluded`, mơ hồ thì `scope_unresolved`/chờ JD. Không đưa record hợp lệ ngoài scope vào quarantine. Không dùng nhãn của 175 mẫu như bộ nhãn áp tự động cho mọi record.
2. **USAJOBS:** chỉ nhận đúng `PositionSeries=2210`; giữ `US_FEDERAL` và `Other IT` nếu title chưa đủ chứng cứ map. Không trộn với `GLOBAL` hoặc dùng cùng denominator.
3. **Gate chất lượng:** sửa false positive khóa học và các alias map quá rộng; kiểm thêm mẫu ở toàn bộ tập Bronze trước khi chọn rule production. Mẫu AI-assisted hỗ trợ thiết kế scope, nhưng đánh giá độ chính xác M4 vẫn cần nhãn độc lập của người đánh giá nếu muốn công bố metric.
4. **Lineage và audit:** áp rule trên 23 run đã pin, giữ `input_run_id`, manifest SHA, mỗi observation và các nhánh `scope_excluded`/`scope_unresolved`. Chỉ sau khi số đếm Silver và phân rã nguồn × thị trường × nghề × tháng đạt mới tạo Gold mới.

Iteration này **chưa chạy Silver/Gold production**, chưa chuyển dashboard và không đổi forecast gate `NO_GO`. Bronze và các run Silver/Gold cũ được giữ nguyên.
