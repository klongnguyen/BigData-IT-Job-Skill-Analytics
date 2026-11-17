# Hướng dẫn sử dụng dashboard Skill Radar

Tài liệu cho người dùng và người bảo vệ đề tài: mỗi màn hình làm gì, các nút bấm dùng ra sao, từng biểu đồ thể hiện điều gì và được tính từ trường dữ liệu nào.

Mục lục
1. [Mở dashboard và thao tác chung](#1-mở-dashboard-và-thao-tác-chung)
2. [Quy ước dữ liệu cần biết trước khi đọc biểu đồ](#2-quy-ước-dữ-liệu-cần-biết-trước-khi-đọc-biểu-đồ)
3. [Tổng quan](#3-tổng-quan)
4. [Xu hướng](#4-xu-hướng)
5. [Hồ sơ kỹ năng](#5-hồ-sơ-kỹ-năng)
6. [Hệ sinh thái](#6-hệ-sinh-thái)
7. [Skill Navigator](#7-skill-navigator)
8. [Dự báo & độ tin cậy](#8-dự-báo--độ-tin-cậy)
9. [Cách đọc kết quả cho đúng (giới hạn)](#9-cách-đọc-kết-quả-cho-đúng-giới-hạn)
10. [Phụ lục A: từ điển bảng dữ liệu](#phụ-lục-a-từ-điển-bảng-dữ-liệu)
11. [Phụ lục B: luật trích xuất từ văn bản tin](#phụ-lục-b-luật-trích-xuất-từ-văn-bản-tin)

---

## 1. Mở dashboard và thao tác chung

### Khởi động
```powershell
cd d:\Study\2026\Nam04_HK1\bigData_T.Ha\BigData_Job_Analy
python -m streamlit run skill_radar/app.py --server.port 8502
```
Mở trình duyệt tại http://127.0.0.1:8502. Dashboard chỉ cần file `skill_radar/data/gold.db`; không cần chạy lại pipeline.
Giao diện luôn nền trắng.

Liên kết trực tiếp tới một màn hình: thêm `?page=` + tên màn hình, ví dụ `http://127.0.0.1:8502/?page=Xu hướng`.

### Thanh bên trái
| Thành phần | Chức năng |
| --- | --- |
| Danh sách 6 chuyên mục | Bấm để chuyển màn hình. |
| **Đang chọn: …** và nút **Bỏ chọn** | Chỉ hiện sau khi bạn bấm vào một kỹ năng trên biểu đồ (xem mục dưới). **Bỏ chọn** xóa kỹ năng đang chọn và mọi vùng chọn trên biểu đồ. |
| Khung "Nguồn / Giai đoạn / Tin phân tích" | Nguồn dữ liệu, khoảng quý được phân tích, số tin. Lấy từ bảng `gold_fact`. |

### Thao tác trên mọi biểu đồ
| Thao tác | Kết quả |
| --- | --- |
| **Rê chuột** | Hiện chú thích (tooltip) với giá trị chính xác. |
| **Bấm vào tên trong chú giải** | Ẩn/hiện chuỗi đó. **Bấm đúp** vào tên: chỉ giữ lại chuỗi đó. |
| **Kéo chuột** trên biểu đồ | Không có tác dụng (đã khóa phóng to/kéo trục để biểu đồ không bị lệch mà không quay lại được). Muốn xem một khoảng thời gian, dùng nút 3 năm / 5 năm / Tất cả. |
| **Nút "3 năm / 5 năm / Tất cả"** (trên các biểu đồ theo quý) | Chỉ xem 3 năm hoặc 5 năm gần nhất, hoặc toàn bộ. |

### Bấm để chọn kỹ năng (giống lọc chéo của Power BI)
Một số biểu đồ cho phép **bấm vào một cột / bong bóng / chấm**:
- Biểu đồ làm mờ các điểm còn lại để làm nổi điểm bạn chọn.
- Bên dưới biểu đồ hiện khung **Chi tiết: <tên kỹ năng>** gồm 5 chỉ số, biểu đồ lịch sử + kịch bản, và nút **Mở hồ sơ đầy đủ →** để nhảy sang màn hình Hồ sơ kỹ năng.
- Kỹ năng vừa bấm trở thành **kỹ năng đang chọn**: được làm nổi trên biểu đồ xếp hạng (Tổng quan) và biểu đồ so sánh (Xu hướng); màn hình Hồ sơ kỹ năng mở sẵn kỹ năng đó.
- **Bấm đúp** vào biểu đồ để bỏ chọn trong biểu đồ đó; nút **Bỏ chọn** ở thanh bên xóa kỹ năng đang chọn và mọi vùng chọn.

Biểu đồ bấm được: *Cuộc đua xếp hạng kỹ năng* (Tổng quan), *Radar 1 năm tới* (Dự báo), *Vị thế và động lượng* (Xu hướng), *Bản đồ công nghệ* (Hệ sinh thái). Treemap ở Tổng quan có kiểu tương tác riêng: bấm một nhóm để phóng to, bấm thanh đường dẫn phía trên để quay lại.

---

## 2. Quy ước dữ liệu cần biết trước khi đọc biểu đồ

| Thuật ngữ | Ý nghĩa |
| --- | --- |
| **Tin** | Một bình luận cấp cao nhất trong chuỗi "Ask HN: Who is hiring?" của Hacker News, tức một tin tuyển dụng do công ty tự đăng. Tin dưới 50 ký tự bị loại. |
| **Kỹ năng được nhắc** | Tin có chứa từ khóa của kỹ năng đó (danh mục 75 kỹ năng trong `taxonomy.py`). "Nhắc tới" chưa chắc là "đang tuyển người biết kỹ năng đó". |
| **Tỷ lệ (share)** | `số tin nhắc kỹ năng / tổng số tin` trong khoảng thời gian đang xét. Ví dụ Python 25% = cứ 4 tin thì 1 tin nhắc Python. Dùng tỷ lệ vì tổng số tin mỗi quý thay đổi. |
| **Điểm % (điểm phần trăm)** | Hiệu của hai tỷ lệ. Từ 20% lên 23% là +3 điểm %. |
| **4 quý gần nhất** | 4 quý cuối của dữ liệu (2025Q4–2026Q3 ở bản dữ liệu hiện tại). Tỷ lệ được cộng dồn số tin rồi chia, không lấy trung bình của 4 tỷ lệ. |
| **Giai đoạn** | Từ 2015Q3 đến 2026Q3 (45 quý, 79.180 tin). Các tháng 2015 bị thiếu ở nguồn nên chuỗi chỉ liền mạch từ 2015Q3. |
| **Nhóm kỹ năng** | 8 nhóm: Ngôn ngữ, Front-end, Back-end, Dữ liệu, AI/ML, Cloud/DevOps, Mobile, Khác. Mỗi nhóm một màu cố định ở mọi biểu đồ. |
| **Kỹ năng đủ điều kiện dự báo** | 53 kỹ năng có tỷ lệ trung bình ≥ 1% trong giai đoạn chọn mô hình (đến 2022Q4). Kỹ năng còn lại (ví dụ LLM, LangChain) chỉ có thống kê lịch sử, không có dự báo. |
| **Màu** | Xanh dương: tăng / mức cao. Đỏ: giảm. Xám: ổn định / không xác định. |

Luồng dữ liệu: `API (Hacker News, npm, Stack Overflow)` → `warehouse.db` (Bronze: dữ liệu thô; Silver: tin đã làm sạch, kỹ năng, đặc trưng) → `pipeline` (dự báo, kiểm chứng, bảng phân tích) → `gold.db` → dashboard.

---

## 3. Tổng quan

**Mục đích:** nhìn toàn thị trường trong một màn hình, không cần thao tác.

### Các ô chỉ số (hàng trên cùng)
| Ô | Giá trị | Lấy từ |
| --- | --- | --- |
| Tin đã phân tích | Số tin trong giai đoạn mô hình | `gold_fact.postings` |
| Kỹ năng theo dõi | Số kỹ năng trong danh mục | số dòng bảng `skills` |
| Phổ biến nhất | Kỹ năng có tỷ lệ cao nhất trong 4 quý gần nhất, kèm tỷ lệ | `radar_history` (`posts`, `total`) |
| Tăng nhanh nhất | Kỹ năng tăng nhiều điểm % nhất so với 4 quý trước đó (chỉ xét kỹ năng có ≥ 1% số tin ở một trong hai giai đoạn, để bỏ nhiễu từ kỹ năng quá hiếm) | `radar_history` |
| Giảm mạnh nhất | Như trên, theo chiều giảm | `radar_history` |

Năm ô nằm trên một hàng. Tỷ lệ tin remote và tin nêu lương của **từng kỹ năng** xem ở mục "Chân dung tin tuyển" của trang Hồ sơ kỹ năng. Dự báo và độ tin cậy của dự báo xem ở trang **Dự báo & độ tin cậy**.

### Dự báo năm tới
Hai biểu đồ thanh ngay dưới các ô chỉ số, để thấy hướng đi của thị trường mà không cần sang trang khác.
- **Kỹ năng:** 5 kỹ năng dự báo tăng nhiều nhất và 5 kỹ năng giảm nhiều nhất sau 4 quý so với trung bình năm vừa qua (điểm %). Chỉ xét kỹ năng đủ điều kiện dự báo. Dữ liệu: `radar_series` (`delta_pp_4q`, `direction`).
- **Nhóm kỹ năng:** thay đổi dự báo của 7 nhóm (Ngôn ngữ, Front-end, Back-end, Dữ liệu, AI/ML, Cloud/DevOps, Mobile). Dữ liệu: `category_forecast`.
- Màu: xanh là tăng, đỏ là giảm, xám là ổn định. Đây là hướng đi, chưa phải con số chính xác. Chi tiết và độ chính xác xem ở trang **Dự báo & độ tin cậy**.

### Bản đồ kỹ năng năm qua (treemap)
- **Diện tích:** số tin nhắc kỹ năng trong 4 quý gần nhất (`radar_history.posts`).
- **Màu:** thay đổi tỷ lệ so với 4 quý liền trước, tính bằng điểm %. Xanh: tăng, đỏ: giảm; thang màu cắt ở mức 90% của biến động tuyệt đối để vài kỹ năng cực đoan không làm nhạt phần còn lại.
- **Chữ trong ô:** tỷ lệ 4 quý gần nhất.
- **Cấu trúc:** nhóm kỹ năng → kỹ năng. **Bấm một nhóm** để phóng to, bấm thanh đường dẫn phía trên để quay lại.

### Cơ cấu lượt nhắc kỹ năng theo nhóm
Biểu đồ vùng xếp chồng 100%. Với mỗi quý, cộng số lượt nhắc kỹ năng của từng nhóm (`radar_history.posts` gộp theo `category`) rồi chia cho tổng lượt nhắc của quý. Một tin có thể nhắc nhiều kỹ năng nên đây là **cơ cấu lượt nhắc**, không phải cơ cấu số tin. Dải mỏng lên là nhóm nào đang chiếm thêm "phần chú ý". Có nút 3 năm / 5 năm / Tất cả.

### Cuộc đua xếp hạng kỹ năng
- Với mỗi năm, tỷ lệ của từng kỹ năng (`skill_year.posts / total`) được xếp hạng (1 = nhiều nhất), từ 2016. Hai kỹ năng bằng điểm nhau được xếp liền nhau theo thứ tự có sẵn để nhãn không đè lên nhau.
- **Thanh trượt "Khoảng hạng hiển thị"**: chọn khoảng hạng của năm gần nhất, mặc định 1–12; kéo sang ví dụ 16–40 để xem các kỹ năng xếp thấp hơn. Biểu đồ dài ra theo số hạng, cuộn trang xuống để xem hết.
- Đường đi **ra ngoài khung** nghĩa là khi đó kỹ năng xếp ngoài khoảng hạng đang hiển thị.
- **Bấm vào một đường** để mở bảng chi tiết kỹ năng phía dưới (kèm nút "Mở hồ sơ đầy đủ").
- Nếu bạn đã bấm chọn một kỹ năng ở màn hình khác, đường của nó được làm đậm, các đường còn lại mờ đi.

---

## 4. Xu hướng

**Mục đích:** so sánh kỹ năng theo thời gian. Có 4 thẻ (tab) ở phía trên.

### Thẻ "So sánh kỹ năng"
| Điều khiển | Chức năng |
| --- | --- |
| **Kỹ năng** (chọn nhiều, tối đa 8) | Chọn các kỹ năng vẽ lên biểu đồ. Mặc định: React, Angular, jQuery, TypeScript, Vue. |
| **Thước đo:** *Tỷ lệ tin (%)* / *Chỉ số (đỉnh = 100)* | Chế độ chỉ số chia mỗi đường cho giá trị cao nhất của chính nó, để so sánh **hình dạng** tăng/giảm của kỹ năng lớn và nhỏ trên một trục. |
| **Làm mượt 4 quý** | Lấy trung bình trượt 4 quý để bớt nhiễu. |
| **Hiện sự kiện** | Vẽ các vạch dọc: COVID-19 (2020Q1), ChatGPT ra mắt (2022Q4), Sa thải hàng loạt ngành tech (2023Q1). Lấy từ bảng `event`. |
| Nút 3 năm / 5 năm / Tất cả | Chọn khoảng thời gian hiển thị. |

Dữ liệu: `radar_history.share` (tỷ lệ từng quý của từng kỹ năng). Kỹ năng đang chọn từ màn hình khác được làm đậm.

### Thẻ "Bản đồ nhiệt"
| Điều khiển | Chức năng |
| --- | --- |
| **Nhóm kỹ năng** | Chỉ giữ kỹ năng thuộc các nhóm được chọn. |
| **Số kỹ năng hiển thị** (10–40) | Lấy N kỹ năng có tỷ lệ cao nhất ở năm gần nhất. |

Mỗi ô là tỷ lệ % tin trong năm đó nhắc tới kỹ năng (`skill_year.posts / total`); số trong ô làm tròn đến đơn vị (hiện khi N ≤ 30). Màu xanh càng đậm tỷ lệ càng cao. Năm đầu (2015 chỉ có nửa năm) bị bỏ; năm cuối có thể chưa đủ 4 quý.

### Thẻ "Thắng – thua"
| Điều khiển | Chức năng |
| --- | --- |
| **Năm so sánh (đầu / cuối)** | Chọn hai năm cần so. |
| **Số kỹ năng thay đổi nhiều nhất** (8–30) | Hiện N kỹ năng có thay đổi tuyệt đối lớn nhất. |

Biểu đồ "quả tạ": vòng rỗng = tỷ lệ năm đầu, chấm đen = tỷ lệ năm cuối, đường nối **xanh** nếu tăng và **đỏ** nếu giảm. Chỉ xét kỹ năng có tỷ lệ ≥ 1% ở ít nhất một trong hai năm; sắp xếp theo mức thay đổi. Dữ liệu: `skill_year`.

### Thẻ "Vị thế & động lượng" (bấm được)
Mỗi bong bóng là một kỹ năng:
- **Trục ngang (thang log):** tỷ lệ 4 quý gần nhất, tức "độ phổ biến".
- **Trục dọc:** thay đổi tỷ lệ so với 4 quý liền trước (điểm %), tức "động lượng".
- **Kích thước:** số tin nhắc kỹ năng. **Màu và hình dạng:** nhóm kỹ năng.
- **Đường chấm dọc:** trung vị tỷ lệ, chia "phổ biến" và "ít phổ biến". Bốn góc: *Phổ biến & đang lên*, *Ít phổ biến nhưng đang lên*, *Phổ biến nhưng chững lại*, *Ít phổ biến & thu hẹp*.
- Chỉ vẽ kỹ năng có ≥ 20 tin trong 4 quý gần nhất; ghi tên cho 6 kỹ năng phổ biến nhất, 5 kỹ năng tăng mạnh nhất, 5 kỹ năng giảm mạnh nhất.
- **Bấm một bong bóng** để xem khung chi tiết bên dưới.

Đây là số liệu đã xảy ra, không phải dự báo. Dữ liệu: `radar_history`.

---

## 5. Hồ sơ kỹ năng

**Mục đích:** xem mọi thứ về một kỹ năng. **Chọn kỹ năng** bằng hộp chọn ở trên cùng (sắp xếp theo độ phổ biến; mặc định Python hoặc kỹ năng bạn vừa bấm ở màn hình khác).

### Năm ô chỉ số
| Ô | Ý nghĩa | Lấy từ |
| --- | --- | --- |
| Tỷ lệ 4 quý gần nhất | % tin nhắc kỹ năng | `radar_series.share_last_year` |
| Hạng trong 75 kỹ năng | Thứ hạng theo tỷ lệ 4 quý gần nhất | `radar_history` |
| Đỉnh lịch sử | Tỷ lệ quý cao nhất và quý đạt đỉnh | `radar_series.peak_share`, `peak_period` |
| Hướng 1 năm tới | Đang lên / Ổn định / Suy giảm và mức thay đổi dự báo (điểm %). Dấu "—" nếu chưa đủ bằng chứng | `radar_series.direction`, `delta_pp_4q` |
| Lương trung vị | Trung vị mức lương USD/năm công bố trong 8 quý gần nhất, kèm chênh so với chung. Hiện khi có ≥ 20 tin nêu lương USD | `skill_salary` (`scope = recent`) |

Dòng chữ "Thuộc cụm công nghệ" lấy từ `skill_cluster`.

### Lịch sử và kịch bản 4 quý tới
- **Cột nhạt:** tỷ lệ từng quý. **Đường đậm:** trung bình trượt 4 quý (`radar_history.share`).
- **Đường nét đứt + dải xám:** kịch bản 4 quý tới và khoảng dự báo 80% (`radar_paths.forecast`, `lo`, `hi`). Chỉ có cho kỹ năng đủ điều kiện. Đây là **kịch bản**, chưa vượt baseline "giữ nguyên quý cuối" (xem mục 9).
- Vạch dọc: các sự kiện. Có nút 3 năm / 5 năm / Tất cả.

### Chân dung tin tuyển so với thị trường
Thanh xanh = tỷ lệ tin **của kỹ năng này** có thuộc tính; thanh xám = tỷ lệ **toàn bộ tin**, cùng 2 năm gần nhất. Các thuộc tính: làm từ xa, hybrid, nêu mức lương, có equity/cổ phần, vị trí senior trở lên, junior/thực tập, hỗ trợ visa. Dữ liệu: `skill_attr_year` (kỹ năng) và `market_quarter` (toàn bộ).

### Hay đi kèm với
Với kỹ năng A đang chọn, mỗi thanh là kỹ năng B và **xác suất có B khi tin nhắc A**: `số tin nhắc cả A và B / số tin nhắc A`. Tooltip có thêm **lift** (xem [mục 6](#6-hệ-sinh-thái)) và số tin. Dữ liệu: `skill_pair_window` (12 quý gần nhất).

### Vì sao kỹ năng này tăng/giảm? (đang tạm tắt)
> **Đang tạm ẩn khỏi giao diện.** Mã nguồn vẫn còn (`ui/pages/why.py`, `drivers.py`); đặt `SHOW_WHY = True` trong `ui/pages/profile.py` để bật lại. Phần mô tả dưới đây áp dụng khi bật.

Mục này trả lời "thay đổi **đến từ đâu**". Nó là phân tích **mô tả** từ chính các tin tuyển dụng; dữ liệu không chứng minh được nguyên nhân. Phía trên cùng là nút chọn **So sánh 4 quý gần nhất với: 1 / 3 / 5 năm trước** (kỳ so sánh là 4 quý kết thúc cách đây 4, 12 hoặc 20 quý). Một khung **Tóm tắt** tự sinh các câu sau, rồi 5 thẻ minh họa chi tiết.

**Khung Tóm tắt** (hàm `summarize` trong `skill_radar/drivers.py`):
| Câu | Nội dung | Cách tính |
| --- | --- | --- |
| Thay đổi | Tỷ lệ kỳ trước → kỳ này và hiệu (điểm %) | `posts / total` của kỹ năng trong hai kỳ (bảng `radar_history`) |
| Do chính kỹ năng / do cơ cấu tin | Phần thay đổi diễn ra trong các tin tương đương, hay do loại tin thay đổi | Phân tách "shift-share" (thẻ 2). Kết luận "do chính kỹ năng" khi trung bình phần "trong tin tương đương" của 3 cách chia tin ≥ 70% tổng thay đổi; "do cơ cấu tin" khi ≤ 30%; còn lại "một phần" |
| Độ rộng | Số nhà tuyển dụng khác nhau và phần của 5 nhà đăng nhiều nhất | Thẻ 3 |
| Bước ngoặt | Quý xu hướng đổi hướng, độ dốc trước/sau, sự kiện gần đó | Thẻ 1 |
| Biến động cùng/ngược chiều | Ba kỹ năng gần nhất theo từng chiều | Thẻ 4 |
| Dự báo dựa vào gì | Đà 8 quý và mức nền mà mô hình đọc | Thẻ 5 |
Nếu kỹ năng có dưới 30 tin trong một trong hai kỳ, câu "Số tin ít" thay cho câu độ rộng để cảnh báo kết luận dễ nhiễu.

**Thẻ 1, "Bước ngoặt".** Khớp một đường thẳng gấp khúc liên tục (hai độ dốc) vào chuỗi tỷ lệ từng quý, thử mọi điểm gấp có ít nhất 6 quý mỗi bên và chọn điểm có sai số nhỏ nhất. Chỉ báo cáo "có bước ngoặt" khi đường gấp khúc loại bỏ thêm **≥ 20%** sai số so với một đường thẳng **và** đổi độ dốc **≥ 0,3 điểm %/năm**. Đường đen là đường khớp, vạch đỏ là bước ngoặt, vạch xám là các sự kiện (COVID-19, ChatGPT, sa thải hàng loạt) để đối chiếu; trùng thời điểm **không** chứng minh nguyên nhân. Dữ liệu: `radar_history.share`, `event`.

**Thẻ 2, "Cơ cấu tin hay chính kỹ năng?".** Biểu đồ thác nước tách thay đổi tỷ lệ thành hai phần cộng lại đúng bằng tổng thay đổi. Chọn cách **chia tin theo**: Hình thức làm việc (nhắc remote hay không), Cấp bậc (senior hay không), Khu vực (Bắc Mỹ, Châu Âu, Châu Á – TBD, không nêu). Với mỗi nhóm tin `s`: `w` = tỷ trọng nhóm trong tổng số tin, `p` = tỷ lệ tin của nhóm nhắc kỹ năng; tỷ lệ chung = Σ `w × p`.
- **Kỹ năng được nhắc khác đi (trong tin tương đương)** = Σ trung bình(`w`) × (`p` nay − `p` trước).
- **Loại tin thay đổi (cơ cấu)** = Σ (`w` nay − `w` trước) × trung bình(`p`).
Ví dụ: nếu tin remote tăng từ 20% lên 60% và tin remote nhắc kỹ năng nhiều hơn tin khác, tỷ lệ chung tăng dù trong từng loại tin kỹ năng không được nhắc nhiều hơn: phần đó thuộc "cơ cấu". Hộp "Chi tiết từng nhóm tin" cho thấy `w`, `p` và đóng góp của từng nhóm. Dữ liệu: `posting` (`is_remote`, `is_senior`, `region`, `quarter`) và `posting_skill`.

**Thẻ 3, "Độ rộng nhà tuyển dụng".** Bốn ô: số tin nhắc kỹ năng, số nhà tuyển dụng khác nhau, số tin trên mỗi nhà tuyển dụng, phần của 5 nhà đăng nhiều nhất; số lớn là kỳ này, chú thích nhỏ là kỳ trước. Số nhà tuyển dụng tăng cùng nhịp số tin = chấp nhận rộng; vài nhà tuyển dụng đăng liên tục chiếm phần lớn = tăng trưởng mong manh hơn. Nhà tuyển dụng được đếm theo `posting.author_id`, một số nguyên ẩn danh (không có tên người đăng).

**Thẻ 4, "Đồng biến / ngược chiều".** Thanh xanh = kỹ năng có thay đổi theo năm cùng chiều, thanh đỏ = ngược chiều. Cách tính: với mọi kỹ năng, lấy thay đổi tỷ lệ so với 4 quý trước tại mỗi quý, rồi tính **hệ số tương quan** với thay đổi của kỹ năng đang xem trên toàn giai đoạn; hiển thị 5 kỹ năng cao nhất và 5 thấp nhất, chỉ xét kỹ năng có tỷ lệ trung bình ≥ 0,5%. Tooltip có thêm lift (mức đi cùng tin). Gợi ý: cùng chiều có thể là bổ trợ (React với TypeScript), ngược chiều có thể là thay thế (jQuery với React/Vue). Đây là tương quan: hai kỹ năng có thể cùng chịu một yếu tố thứ ba, và các thay đổi chồng thời gian nên tự tương quan mạnh, nên không dùng để kết luận nguyên nhân.

**Thẻ 5, "Mô hình dự báo dựa vào gì?".** Liệt kê các số mô hình hướng (Gradient Boosting) thực sự đọc cho kỹ năng này: mức nền (trung bình 4 quý gần nhất), độ dốc 8 quý, độ lệch của 3 quý gần nhất so với mức nền; ngoài ra mô hình còn dùng tổng số tin của quý và nhóm kỹ năng. Nghĩa là dự báo là **quán tính** (đang lên thì tiếp tục lên chậm dần), **không** học các nguyên nhân ở bốn thẻ trên. Vì vậy chỉ nhãn hướng được kiểm chứng, và dashboard không hứa hẹn giải thích nguyên nhân.

---

## 6. Hệ sinh thái

**Mục đích:** kỹ năng nào hay xuất hiện cùng nhau, và chúng tạo thành những "stack" nào. Tính trên **12 quý gần nhất** (2023Q4–2026Q3), 11.536 tin.

### Khái niệm
- **Đồng xuất hiện:** số tin nhắc cả hai kỹ năng.
- **Lift:** `P(A và B) / (P(A) × P(B))`. Lift 1 = đi cùng ở mức ngẫu nhiên; lift 3 = đi cùng nhiều gấp 3 lần mức ngẫu nhiên. Cho biết hai kỹ năng **thật sự gắn với nhau**, khác với việc cả hai đều phổ biến.
- **PPMI:** log của lift, đặt về 0 nếu âm hoặc nếu cặp có dưới 5 tin. Mỗi kỹ năng thành một vectơ PPMI; độ giống nhau của hai kỹ năng = cosine của hai vectơ.
- **Cụm:** phân cụm Ward trên khoảng cách `1 − cosine`; số cụm k chọn theo silhouette cao nhất trong các k mà mỗi cụm có 5 đến 35% số kỹ năng (6 cụm ở bản hiện tại). Chỉ phân cụm kỹ năng có ≥ 30 tin trong cửa sổ (68/75 kỹ năng).

### Thẻ "Bản đồ công nghệ" (bấm được)
- Mỗi chấm là một kỹ năng. **Hai chấm càng gần nhau thì càng hay xuất hiện cùng nhau.** Vị trí tính bằng t-SNE trên khoảng cách nói trên (cố định hạt giống, nên hình luôn như nhau); chỉ khoảng cách tương đối có ý nghĩa, không phải tọa độ tuyệt đối.
- **Màu và hình dạng:** cụm. Tên cụm trong chú giải là 3 kỹ năng nhiều tin nhất của cụm. **Kích thước:** số tin nhắc kỹ năng.
- **Đường nối:** cặp có lift ≥ 2 và ≥ 25 tin (tối đa 120 đường có lift cao nhất).
- Dòng "Lưu ý silhouette": độ tách cụm khá yếu (~0,15), các cụm chồng lấn; coi cụm là gợi ý.
- Hộp mở rộng "Thành phần từng cụm" liệt kê kỹ năng của mỗi cụm.
- **Bấm một chấm** để xem khung chi tiết và biểu đồ "bạn đồng hành".

### Thẻ "Bạn đồng hành của một kỹ năng"
**Chọn một kỹ năng** → 15 kỹ năng đi kèm nhiều nhất (xác suất có điều kiện như mục 5). Màu theo nhóm kỹ năng.

### Thẻ "Ma trận lift"
| Điều khiển | Chức năng |
| --- | --- |
| **Số kỹ năng trong ma trận** (12–40) | Lấy N kỹ năng nhiều tin nhất, xếp theo cụm. |

Mỗi ô là **log₂(lift)** của một cặp kỹ năng. **Xanh:** đi cùng nhiều hơn ngẫu nhiên; **đỏ:** đi cùng ít hơn ngẫu nhiên; **trắng/trống:** cặp ít hơn 5 tin nên không đủ dữ liệu. Các khối xanh dọc đường chéo chính chính là các cụm.

---

## 7. Skill Navigator

**Mục đích:** cho biết kỹ năng bạn đang có phù hợp bao nhiêu tin tuyển dụng và nên học gì tiếp.

### Quy tắc "phù hợp"
Một tin **phù hợp** khi bạn biết **ít nhất X% số kỹ năng được nêu trong tin đó** (X do bạn chọn, mặc định 50%). Ví dụ tin nêu Python, SQL, Docker, AWS: ở ngưỡng 50% bạn cần biết ít nhất 2 trong 4. Chỉ tin nhắc ít nhất một kỹ năng trong danh mục được tính (khoảng 60 nghìn tin).

### Điều khiển
| Điều khiển | Chức năng |
| --- | --- |
| **Hồ sơ mẫu** | Điền sẵn bộ kỹ năng: Web front-end, Back-end Python, Dữ liệu & ML, Mobile iOS, DevOps; hoặc "Tự chọn". |
| **Kỹ năng của bạn** | Thêm/bớt kỹ năng đã biết. |
| **Giai đoạn tin** | 8 quý gần nhất / 16 quý gần nhất / toàn bộ từ 2015Q3. |
| **Cần biết ít nhất … kỹ năng nêu trong tin** (20%–100%) | Ngưỡng X ở trên. Càng cao càng khắt khe. |
| **Chỉ tin làm từ xa** | Giữ các tin có nhắc remote (`posting.is_remote`). |
| **Chỉ tin nêu lương** | Giữ các tin có công bố lương (`posting.has_salary`). |

### Kết quả
- **Độ phủ thị trường:** số tin phù hợp / số tin đang xét. **Số tin phù hợp** và **Kỹ năng đã chọn** kèm theo.
- **Nên học gì tiếp theo?** Với mỗi kỹ năng chưa có, đếm số tin sẽ **trở thành phù hợp** nếu bạn học thêm đúng kỹ năng đó; thanh hiển thị phần tăng độ phủ (điểm %). Màu theo nhóm.
- **Lộ trình học tham lam:** lặp 6 bước: mỗi bước chọn kỹ năng làm tăng độ phủ nhiều nhất rồi cộng vào bộ kỹ năng. Đường bậc thang cho thấy độ phủ sau mỗi bước. "Tham lam" nghĩa là chọn tốt nhất từng bước, không đảm bảo tối ưu toàn cục.
- **Bộ kỹ năng này có "ăn khách" hơn theo thời gian?** Độ phủ của đúng bộ kỹ năng đang chọn theo từng quý (trung bình trượt 4 quý), tính trên toàn bộ tin; không phụ thuộc bộ lọc giai đoạn.

Dữ liệu: `posting` (`pid`, `quarter`, `is_remote`, `has_salary`) và `posting_skill` (`pid`, `skill`).

---

## 8. Dự báo & độ tin cậy

**Mục đích:** xem dự báo và biết nó đáng tin tới mức nào. Có 5 tab: Radar 1 năm tới, Theo nhóm kỹ năng, Độ chính xác của hướng, Độ chính xác của số liệu, Tín hiệu cộng đồng.

Tóm tắt độ tin cậy:
- **Hướng** thay đổi sau 1 năm (Đang lên, Ổn định, Suy giảm) tốt hơn đoán bừa. Macro-F1 0,47 so với 0,26 khi luôn đoán Ổn định, chấm trên 2023Q1 đến 2026Q3 chưa từng dùng để chọn mô hình.
- **Con số tỷ lệ** dự báo chưa vượt cách giữ nguyên quý cuối, nên coi là **kịch bản**.


### Thẻ "Radar 1 năm tới" (bấm được)
| Điều khiển | Chức năng |
| --- | --- |
| **Nhóm kỹ năng** | Lọc theo nhóm. |
| **Bấm một cột** | Hiện khung chi tiết kỹ năng. |
| Hộp mở rộng **Bảng đầy đủ** và nút **Tải CSV** | Xem và tải bảng dự báo của các kỹ năng đang lọc. |

- Ba ô: số kỹ năng **Đang lên / Ổn định / Suy giảm** trong các kỹ năng đủ điều kiện.
- Biểu đồ: 16 kỹ năng thay đổi dự báo nhiều nhất. Giá trị = (tỷ lệ mô hình hướng dự báo sau 4 quý − tỷ lệ trung bình 4 quý gần nhất) × 100, tức điểm %. Đường chấm ±1 là ngưỡng đặt trước: vượt +1 là *Đang lên*, dưới −1 là *Suy giảm*, còn lại *Ổn định*. Dữ liệu: `radar_series.delta_pp_4q`, `direction`.
- Bảng: tỷ lệ năm qua, dự báo 4 quý, thay đổi, hướng, đỉnh lịch sử, quý đỉnh.
- Lưu ý: nhãn lấy từ mô hình hướng (GBM), con số dự báo lấy từ mô hình giá trị (damped), hai mô hình khác nhau nên đôi khi nhãn và con số lệch chiều.

### Thẻ "Theo nhóm kỹ năng"
Dự báo cho cả nhóm (Ngôn ngữ, Cloud/DevOps, AI/ML…) thay vì từng kỹ năng. Một nhóm gộp nhiều kỹ năng nên chuỗi lớn và mượt hơn.
- **Chuỗi:** tỷ lệ tin có nhắc **ít nhất một** kỹ năng của nhóm (một tin chỉ tính một lần). Dữ liệu: `category_history`.
- **Bảy biểu đồ nhỏ:** đường liền là 4 năm gần nhất, nét đứt là dự báo 4 quý tới, vùng xám là khoảng 80% (`category_path`).
- **Bảng:** tỷ lệ năm qua, dự báo 4 quý, thay đổi và hướng (`category_forecast`). Ngưỡng hướng là ±2,0 điểm % vì tỷ lệ của nhóm lớn hơn nhiều so với từng kỹ năng.
- Cách làm giống dự báo theo kỹ năng: chọn tham số và mô hình bằng dữ liệu đến 2022Q4, rồi chấm một lần trên giai đoạn kiểm tra. Chỉ dùng mô hình cổ điển (giữ nguyên quý cuối, trung bình 4 quý, làm mượt mũ, xu hướng giảm dần) vì chỉ có 7 chuỗi, không đủ để huấn luyện mô hình học máy chung.
- **Kết quả:** nhãn hướng theo nhóm tốt hơn đoán bừa (macro-F1 0,43 so với 0,16, khoảng tin cậy 95% của chênh lệch là 0,13 đến 0,39). Giá trị dự báo vẫn chưa hơn "giữ nguyên quý cuối" (sai số 2,28 so với 2,65 của mô hình đang dùng), nên coi là kịch bản.
- Lưu ý: chỉ có 7 nhóm và 12 thời điểm dự báo, các quý liền nhau lại giống nhau, nên kết quả ít chắc chắn hơn kết quả theo kỹ năng.

### Thẻ "Độ chính xác của hướng"
- **Ma trận nhầm lẫn:** hàng = hướng thực tế, cột = hướng mô hình đoán, dự báo trước 4 quý trên giai đoạn kiểm tra. Mỗi hàng chia 100% (số trong ngoặc là số trường hợp). Ô đậm dọc đường chéo = đoán đúng. Dữ liệu: `backtest_cell` (`pred`, `actual`, `base4`, lọc `h = 4`), nhãn tính bằng ngưỡng ±`band_pp` (1,0 điểm %).
- **Mô hình nào đoán đúng hướng?** macro-F1 của từng mô hình (cao hơn là tốt hơn); cột xanh là mô hình dùng cho dashboard; đường đỏ là điểm chuẩn "luôn đoán Ổn định". Dữ liệu: `label_score`.
- Dòng dưới: chênh macro-F1 so với đoán "luôn Ổn định" và khoảng tin cậy 95% (bootstrap theo kỹ năng). Khoảng không chứa 0 nghĩa là mô hình thật sự tốt hơn đoán bừa. Dữ liệu: `run_info` (`dv_gain`, `dv_gain_lo`, `dv_gain_hi`).
- Ghi chú trung thực: mô hình "giữ nguyên quý cuối" còn nhỉnh hơn một chút ở ngưỡng 0,5 và 1,0; mô hình hướng được chọn từ trước trên dữ liệu chọn mô hình nên vẫn báo cáo nguyên trạng.

### Thẻ "Độ chính xác của số liệu"
- **Có mô hình nào đánh bại "giữ nguyên quý cuối"?** Mỗi chấm là chênh sai số tuyệt đối trung bình (điểm %) của một mô hình so với baseline, kèm khoảng tin cậy 95%. Âm = tốt hơn. **Xanh:** tốt hơn rõ ràng (khoảng nằm hẳn dưới 0); **đỏ:** tệ hơn rõ ràng; **xám:** chưa phân biệt được. Dữ liệu: `model_score` (`diff_pp`, `ci_lo`, `ci_hi`).
- **Sai số tăng theo thời gian dự báo:** sai số tuyệt đối trung bình theo số quý dự báo trước (1–4) của 5 mô hình chính. Dữ liệu: `model_horizon_error`.
- **Dự đoán so với thực tế:** chọn **Mô hình** và **Dự báo trước**. Mỗi chấm là một cặp (kỹ năng, quý) chưa từng thấy; càng gần đường chéo càng đúng. Hiện sai số trung bình và số điểm. Dữ liệu: `backtest_cell`.
- Dòng cuối: khoảng dự báo 80% phủ đúng ~80% giá trị thực trên giai đoạn kiểm tra, nên độ rộng khoảng là hợp lý (`run_info.interval_coverage_80`).

### Thẻ "Tín hiệu cộng đồng"
Câu hỏi: hoạt động cộng đồng (npm, Stack Overflow, GitHub) có đi **trước** nhu cầu tuyển dụng không?
- **Dòng đầu:** thêm tín hiệu vào mô hình thì sai số đổi bao nhiêu (`model_score.signal_diff_pp` và khoảng tin cậy). Khoảng chứa 0 = chưa thấy cải thiện.
- **Lượt tải npm: có đi trước nhu cầu không?** Mỗi điểm là tương quan trung bình, qua các kỹ năng, giữa mức tăng của tín hiệu cách đây k quý và mức tăng của nhu cầu hiện tại; thanh dọc là khoảng tin cậy 95%. Khoảng chứa 0 ở mọi độ trễ = không có bằng chứng đi trước. Dữ liệu: `leadlag`.
- **Từng kỹ năng:** bản đồ nhiệt tương quan theo kỹ năng và độ trễ (`leadlag_skill`). Xanh: cùng chiều, đỏ: ngược chiều.
- **Tuyển dụng và lượt tải npm:** chọn một kỹ năng; hai đường cùng chuẩn hóa về đỉnh = 100 để chung một trục (`signal_quarter.npm_dl`, `radar_history.share`).
- Stack Overflow mới có ít kỹ năng và GitHub chưa thu thập nên chưa đủ để kết luận; đây là "chưa đủ dữ liệu", không phải "chắc chắn không có".

Cuối trang, hộp **Dữ liệu và giới hạn** tóm tắt nguồn và các hạn chế.

---

## 9. Cách đọc kết quả cho đúng (giới hạn)

1. **Nguồn dữ liệu lệch:** Hacker News thiên về startup, công ty công nghệ, thị trường Mỹ và làm việc từ xa. Không đại diện toàn ngành CNTT và không đại diện Việt Nam (15 tin trên 79.180, dưới 0,1%).
2. **"Nhắc tới" không bằng "đang tuyển":** một tin nhắc "Python, Ruby, WASM" như các ngôn ngữ sản phẩm hỗ trợ vẫn bị tính cả ba.
3. **Chỉ nhãn hướng dự báo mới được kiểm chứng.** Con số tỷ lệ dự báo là kịch bản. Mọi chỉ số remote/lương/cấp bậc (ở Hồ sơ kỹ năng), cụm công nghệ, Skill Navigator là **thống kê mô tả** từ luật từ khóa, **chưa đối chiếu với nhãn thủ công**. Riêng nhận diện kỹ năng đã được kiểm tra nhanh trên 60 tin (chính xác 99,3%, phủ 97,3%, do Claude chấm), xem mục 4.5 của `PROJECT_REPORT.md`.
4. **Cụm công nghệ yếu:** silhouette khoảng 0,15, các cụm chồng lấn.
5. **Lương công bố** (ở Hồ sơ kỹ năng) chỉ từ tin có nêu lương (thiên về công ty Mỹ), nên không phải mức lương thị trường.
6. **Số tin mỗi quý giảm theo thời gian** (khoảng 2.200 tin/quý năm 2015–2022, thấp hơn nhiều gần đây), nên quý gần nhất nhiễu hơn, nhất là với kỹ năng hiếm.
7. **Giải thích tăng/giảm chỉ là mô tả:** mục "Vì sao" cho biết thay đổi đến từ đâu (kỹ năng hay cơ cấu tin, rộng hay hẹp, đi cùng kỹ năng nào) chứ không chứng minh nguyên nhân (công nghệ mới, sa thải, xu hướng thị trường…); các nguyên nhân đó không có trong dữ liệu.
8. **Kỹ năng mới nổi** (LLM, RAG, LangChain) chưa đủ điều kiện dự báo, chỉ có lịch sử.

---

## Phụ lục A: từ điển bảng dữ liệu

Tất cả nằm trong `skill_radar/data/gold.db` (dashboard đọc ở chế độ chỉ đọc). Dữ liệu thô và đã làm sạch nằm trong `warehouse.db`.

| Bảng | Mỗi dòng là | Cột chính | Dùng ở |
| --- | --- | --- | --- |
| `skills` | một kỹ năng | `skill`, `label`, `category`, `npm_package`, `se_tag` | mọi nơi (tên, nhóm) |
| `radar_history` | (kỹ năng, quý) | `skill`, `period`, `share`, `posts`, `total` | Tổng quan, Xu hướng, Hồ sơ |
| `radar_series` | một kỹ năng | `share_last_year`, `share_last_quarter`, `forecast_4q`, `delta_pp_4q`, `direction`, `evidence`, `eligible`, `peak_share`, `peak_period`, `posts_last_year` | Hồ sơ, Radar |
| `radar_paths` | (kỹ năng, quý tương lai) | `h`, `forecast`, `lo`, `hi` | Hồ sơ (dải dự báo) |
| `skill_year` | (năm, kỹ năng) | `posts`, `total` | Tổng quan, Xu hướng |
| `market_quarter` | một quý | `n_posts`, `remote`, `onsite`, `hybrid`, `salary`, `usd_salary`, `equity`, `visa`, `senior`, `junior`, `intern`, `fulltime`, `parttime`, `contract`, `salary_median_k` | Hồ sơ kỹ năng |
| `skill_attr_year` | (năm, kỹ năng) | `posts`, `remote`, `hybrid`, `salary`, `usd_salary`, `equity`, `senior`, `junior`, `visa` | Hồ sơ kỹ năng |
| `skill_salary` | (phạm vi, kỹ năng) | `scope` (`all`/`recent`), `n`, `q1`, `median`, `q3`; dòng `__all__` là chung | Hồ sơ kỹ năng |
| `location_year` | (năm, khu vực, thành phố) | `posts` | không còn trang nào hiển thị (vẫn có trong `gold.db`) |
| `employer` | một công ty (≥ 8 tin) | `company`, `posts`, `active_months`, `first_month`, `last_month` | không còn trang nào hiển thị (vẫn có trong `gold.db`) |
| `skill_pair_window` | cặp kỹ năng trong 12 quý gần nhất | `a`, `b`, `n`, `n_a`, `n_b`, `lift`, `window_postings` | Hệ sinh thái, Hồ sơ |
| `skill_pair_year` | (năm, cặp kỹ năng) | `a`, `b`, `n` | dự phòng cho phân tích theo năm |
| `skill_cluster` | một kỹ năng | `cluster`, `cluster_name`, `x`, `y`, `mentions` | Hệ sinh thái |
| `posting` | một tin (không có văn bản) | `pid`, `quarter`, `year`, `is_remote`, `is_onsite`, `is_hybrid`, `has_salary`, `salary_usd_k`, `has_equity`, `has_visa`, `is_senior`, `is_junior`, `is_intern`, `is_fulltime`, `is_parttime`, `is_contract`, `city`, `region`, `n_skills`, `author_id` (mã nhà tuyển dụng ẩn danh) | Skill Navigator, Hồ sơ kỹ năng (mục "Vì sao") |
| `posting_skill` | (tin, kỹ năng) | `pid`, `skill` | Skill Navigator, Hồ sơ kỹ năng (mục "Vì sao") |
| `event` | một sự kiện | `period`, `label` | các biểu đồ theo quý |
| `signal_quarter` | (quý, kỹ năng) | `npm_dl`, `se_share`, `gh_share` | Tín hiệu cộng đồng |
| `backtest_cell` | một dự đoán kiểm tra | `model`, `skill`, `origin_period`, `target_period`, `h`, `pred`, `actual`, `base4` | Dự báo & độ tin cậy |
| `category_history`, `category_forecast`, `category_path` | chuỗi, dự báo 4 quý và dải 80% của từng nhóm kỹ năng | `category`, `period`, `share`, `forecast`, `lo`, `hi`, `delta_pp_4q`, `direction` | Tổng quan, Dự báo (Theo nhóm kỹ năng) |
| `category_score`, `category_label`, `category_info` | điểm chấm mô hình theo nhóm và thông số chạy | `mae_pp`, `macro_f1`, `rate_model`, `direction_model` | Dự báo (Theo nhóm kỹ năng) |
| `run_info` | một thông số (khóa–giá trị) | ngày chạy, giao thức, mô hình được chọn, kiểm chứng nhãn hướng, độ phủ khoảng 80% | Dự báo & độ tin cậy |
| `model_score`, `model_horizon_error`, `label_score`, `selection_score`, `interval_quantile` | kết quả chấm điểm mô hình | `mae_pp`, `diff_pp`, `ci_lo`, `ci_hi`, `macro_f1`… | Dự báo & độ tin cậy |
| `leadlag_signal`, `leadlag`, `leadlag_skill` | kết quả phân tích "đi trước" | `signal`, `lag`, `mean_corr`, `ci_lo`, `ci_hi`, `corr` | Tín hiệu cộng đồng |
| `gold_fact` | một sự kiện chạy (khóa–giá trị) | số tin, số tác giả, tỷ lệ tác giả đăng lặp, kết quả phân cụm | Thanh bên, Hệ sinh thái |

---

## Phụ lục B: luật trích xuất từ văn bản tin

Mã nguồn: `skill_radar/taxonomy.py` (kỹ năng) và `skill_radar/process/features.py` (đặc trưng). Mọi luật không phân biệt hoa/thường trừ khi ghi chú.

| Trường | Luật |
| --- | --- |
| **Kỹ năng** | Danh mục 75 kỹ năng, mỗi kỹ năng có nhiều cách viết. Từ nhập nhằng xử lý riêng: "Go" chỉ tính khi viết hoa và không đứng trước to/for/with…; "Java" không khớp trong "JavaScript"; "React" không khớp "React Native"; "Swift", "iOS", "RAG" phân biệt hoa/thường. |
| `is_remote` | Có từ "remote" và không bị phủ định (no remote, not remote, "Remote: No"…). |
| `is_onsite` | Có "onsite", "on-site", "in-office" hoặc "office-based". |
| `is_hybrid` | Có "hybrid". |
| `has_salary` | Có con số lương: `$120k`, `$100-150k`, `$120,000`, `£60k`, `€80k`, `80k-100k`… (con số tiền gọi vốn như `$20,000,000` không tính). |
| `salary_usd_k` | Trung điểm (nghìn USD/năm) của con số lương USD **đầu tiên** trong tin; chỉ nhận giá trị từ 30 đến 700. Lương tiền tệ khác vẫn tính `has_salary` nhưng không có `salary_usd_k`. |
| `has_equity` | Có "equity", "stock option", "ESOP" hoặc "RSU". |
| `has_visa` | Có "visa" hoặc "sponsor/sponsorship". |
| `is_senior` | Có senior, sr, principal, architect, tech/team lead, engineering manager, head of, director, "staff engineer/developer/…", "lead engineer/developer/…". |
| `is_junior` | Có junior, jr, entry-level, new grad, recent graduate, early-career, apprentice. |
| `is_intern` | Có intern, internship hoặc co-op. |
| `is_fulltime`, `is_parttime` | Có "full-time" / "part-time". |
| `is_contract` | Có contract, contractor, contracting hoặc freelance (không tính "smart contract"). |
| `city`, `region` | Tìm trong **250 ký tự đầu** của tin: 35 thành phố (San Francisco, New York, London, Berlin, Singapore, Việt Nam…); không có thành phố thì tìm tên quốc gia/khu vực. Khu vực: Bắc Mỹ, Châu Âu, Châu Á – Thái Bình Dương, hoặc không rõ. |
| `company` | Trường đầu của tin có từ 2 dấu `|` trở lên, bỏ phần trong ngoặc và đường dẫn; loại nếu dài hơn 40 ký tự, hơn 5 từ hoặc chứa từ chỉ chức danh/hình thức làm việc (engineer, remote, hiring…). |

Các luật này đếm **từ khóa**: chúng không hiểu ngữ cảnh. Muốn đổi luật, sửa `features.py` rồi chạy `python -m skill_radar.process.hn_postings --features-only` và `python -m skill_radar.pipeline`.
