# Phân tích các chỉ số của tab "Dự báo & độ tin cậy"

Tài liệu này đọc từng con số xuất hiện trên các biểu đồ của tab **Dự báo & độ tin cậy**: nó có nghĩa là gì, tính từ đâu, và **nó nói tốt hay xấu về mô hình**. Ngoài việc chép lại số trên màn hình, tài liệu tính thêm các phân tích từ dữ liệu kiểm tra (`backtest_cell`, `label_score`, `model_score`, `leadlag`, `radar_series` trong `gold.db`) để trả lời những câu hỏi mà màn hình không trả lời: mô hình sai ở đâu, có ổn định theo thời gian không, khoảng dự báo có hiệu chuẩn tốt cho mọi kỹ năng không.

Phạm vi kiểm tra: **53 kỹ năng đủ điều kiện × 12 quý mục tiêu (2023Q4–2026Q3) = 636 quan sát** cho dự báo trước 4 quý; các horizon ngắn hơn có nhiều quan sát hơn (795 / 742 / 689 / 636 cho h = 1 / 2 / 3 / 4). Mô hình chưa từng thấy các quý này khi chọn tham số (chọn mô hình dùng dữ liệu đến 2022Q4).

> **Cách dùng:** mục 1 là bản đọc trong một phút. Các mục 3–6 đi theo thứ tự các tab. Mục 8 là các câu hỏi hội đồng có thể hỏi, kèm gợi ý trả lời trung thực.

---

## 1. Tóm tắt: tám điều cần nhớ

| # | Phát hiện | Con số | Nghĩa là gì |
| --- | --- | --- | --- |
| 1 | Nhãn hướng **tốt hơn** luôn đoán "Ổn định", có ý nghĩa thống kê | macro-F1 0,467 so với 0,264; chênh +0,2035, KTC 95% [0,147; 0,255] | Điểm mạnh nhất của đề tài |
| 2 | Nhưng **độ chính xác thô chỉ hơn 3,5 điểm %** | 68,9% so với 65,4% | Phần lớn mô hình đoán "Ổn định"; lợi thế đến từ việc bắt được một số kỹ năng tăng/giảm |
| 3 | Mô hình **bỏ sót gần hết kỹ năng tăng** | Rising: recall 11% (8/72), precision 67% (8/12) | "Đang lên" ít khi được báo, nhưng khi báo thì khá đúng |
| 4 | Lợi thế hơn đoán "Ổn định" **có ở cả 4 năm**, nhưng không đều | 2023: 0,32 vs 0,18 · 2024: 0,55 vs 0,25 · 2025: 0,35 vs 0,29 · 2026: 0,45 vs 0,27 | Không phải may mắn một năm; nhưng 2025 chỉ hơn rất ít |
| 5 | Mô hình hướng **không thắng** mô hình "giữ nguyên quý cuối" trên holdout | 0,467 so với 0,498 | Báo cáo nguyên trạng; GBM được chọn từ trước trên dữ liệu chọn mô hình |
| 6 | **Giá trị tỷ lệ** dự báo không hơn baseline; sai số 0,6–0,9 điểm % | MAE 0,62 (h=1) → 0,94 (h=4) với GBM | Tương đương sai lệch tương đối 14% → 21% so với tỷ lệ trung bình 4,4% |
| 7 | Mức **thay đổi** dự báo giải thích được rất ít thay đổi thực tế | tương quan 0,23 (GBM) so với 0,44–0,46 (mô hình đơn giản) | Nên tin nhãn hướng hơn độ lớn của mức thay đổi |
| 8 | Khoảng dự báo 80% **đúng trung bình nhưng thiếu cho kỹ năng lớn** | phủ 80,0% chung; 59% với kỹ năng ≥ 10% tỷ lệ | Dải 80% của Python, React, TypeScript… hẹp hơn mức cần |

---

## 2. Hai khung trạng thái trên cùng

### 2.1 Khung xanh "Đã kiểm chứng"
> *"nhãn hướng thay đổi sau 1 năm (macro-F1 0,47 so với 0,26 khi luôn đoán 'Ổn định'), thử trên 2023Q1..2026Q3"*

**Nhãn** được tạo từ thay đổi dự báo sau 4 quý so với trung bình 4 quý gần nhất, theo ngưỡng đặt trước ±1,0 điểm %: trên +1 là *Đang lên*, dưới −1 là *Suy giảm*, còn lại *Ổn định*.

**Macro-F1** là trung bình cộng của điểm F1 ba nhãn, nên mỗi nhãn nặng như nhau dù hiếm hay phổ biến. Lý do dùng nó thay vì độ chính xác: 65% trường hợp thực tế là "Ổn định", nên cứ đoán "Ổn định" cho mọi kỹ năng đã đúng 65%, nhưng vô dụng vì không phát hiện được kỹ năng nào đổi hướng.

Cách tính, ví dụ với GBM (từ ma trận nhầm lẫn ở mục 4.1):

| Nhãn | Precision | Recall | F1 = 2PR/(P+R) |
| --- | --- | --- | --- |
| Suy giảm | 0,495 | 0,338 | 0,402 |
| Ổn định | 0,727 | 0,914 | 0,809 |
| Đang lên | 0,667 | 0,111 | 0,190 |
| **Macro-F1** | | | (0,402 + 0,809 + 0,190) / 3 = **0,467** |

Với "luôn đoán Ổn định": F1 của Ổn định = 0,791, hai nhãn còn lại = 0, nên macro-F1 = 0,791 / 3 = **0,264**. Đây là mốc cần vượt.

**Khoảng tin cậy 95% [0,147; 0,255]:** ước lượng bằng bootstrap *theo kỹ năng* (2.000 lần lấy mẫu lại cả kỹ năng, không lấy từng quan sát). Phải làm vậy vì 636 quan sát không độc lập: cùng một kỹ năng xuất hiện 12 lần, và các quý liền nhau chồng lấn. Khoảng nằm hẳn trên 0 → mô hình hơn mốc có ý nghĩa thống kê.

### 2.2 Khung vàng "Chưa kiểm chứng"
Hiện khi khoảng tin cậy của mô hình giá trị so với baseline "giữ nguyên quý cuối" chứa 0 (mục 5.2). Nghĩa là: con số tỷ lệ dự báo không được chứng minh là tốt hơn việc lấy tỷ lệ quý vừa rồi. Đây là cảnh báo trung thực, không phải lỗi.

---

## 3. Tab "Radar 1 năm tới"

### 3.1 Các ô đếm
Trong 53 kỹ năng đủ điều kiện: **2 Đang lên · 48 Ổn định · 3 Suy giảm**. 22 kỹ năng còn lại (như LLM, Generative AI, Next.js) không có nhãn vì tỷ lệ trung bình dưới 1% trong giai đoạn chọn mô hình.

### 3.2 Biểu đồ cột và bảng
Mỗi cột là mức thay đổi dự báo `(GBM dự báo sau 4 quý − trung bình 4 quý gần nhất) × 100`, đơn vị điểm %. Phân bố của 53 mức thay đổi: trung bình +0,02, độ lệch chuẩn 0,56, từ −1,79 đến +1,99, trung vị +0,08. Tức hầu hết kỹ năng được dự báo gần như đứng yên, và chỉ 5 kỹ năng vượt ngưỡng ±1.

| Kỹ năng | Tỷ lệ năm qua | Thay đổi theo GBM (điểm %) | Thay đổi theo `damped` (điểm %) | Nhãn |
| --- | --- | --- | --- | --- |
| Python | 25,1% | +1,99 | +1,90 | Đang lên |
| PostgreSQL | 18,4% | +1,35 | +1,42 | Đang lên |
| React | 22,7% | −1,79 | **+0,33** | Suy giảm |
| Go | 7,3% | −1,21 | −0,32 | Suy giảm |
| TypeScript | 23,8% | −1,13 | **+0,82** | Suy giảm |
| Docker | 6,2% | +0,87 | +0,87 | Ổn định (cách ngưỡng 0,13) |
| React Native | 3,1% | +0,69 | −0,07 | Ổn định |
| Redis | 3,8% | +0,68 | +0,54 | Ổn định |

### 3.3 Ba điều cần cẩn thận khi đọc radar
1. **Hai mô hình bất đồng.** Nhãn và thanh trên radar do GBM tính; cột "Dự báo 4 quý" trong bảng do `damped` tính. Dấu của hai mức thay đổi trùng nhau ở 68% kỹ năng. Đáng chú ý: React và TypeScript được gắn *Suy giảm* theo GBM trong khi `damped` dự báo *tăng*. Chỉ Python và PostgreSQL được cả hai mô hình đồng ý là tăng.
2. **Nhãn gần ngưỡng rất mong manh.** Ba kỹ năng nằm trong khoảng 0,3 điểm % quanh ngưỡng ±1: TypeScript (−1,13), Go (−1,21) và Docker (+0,87). Một thay đổi nhỏ của dữ liệu có thể đổi nhãn của chúng.
3. **Mô hình hiếm khi báo "Đang lên".** Trên holdout, GBM đoán Đang lên chỉ 1,9% số lần trong khi thực tế là 11,3%; đoán Suy giảm 15,9% so với thực tế 23,3%. Con số "2 Đang lên" hiện tại nhiều khả năng là **ước lượng thấp**: có thể có kỹ năng đang lên mà mô hình không bắt được (xem mục 4.1).

**Cách nói khi trình bày:** "Radar cho biết mô hình thấy gì từ đà gần đây, không phải lời tiên tri. Python và PostgreSQL là hai kỹ năng cả hai mô hình cùng cho là đi lên."

---

## 4. Tab "Kiểm chứng nhãn hướng"

### 4.1 Ma trận nhầm lẫn (GBM, dự báo trước 4 quý, 636 quan sát)

| | Đoán Suy giảm | Đoán Ổn định | Đoán Đang lên | Tổng thực tế |
| --- | --- | --- | --- | --- |
| **Thực tế Suy giảm** | 50 (34%) | 97 (66%) | 1 (1%) | 148 |
| **Thực tế Ổn định** | 33 (8%) | 380 (91%) | 3 (1%) | 416 |
| **Thực tế Đang lên** | 18 (25%) | 46 (64%) | 8 (11%) | 72 |

Các ô trên màn hình là phần trăm theo hàng (như trong ngoặc) cùng số trường hợp. Cách đọc:
- **Đường chéo = đoán đúng:** 50 + 380 + 8 = 438/636 = **68,9%**.
- **Phần lớn lỗi là đoán "Ổn định" cho kỹ năng thực ra đổi hướng** (97 + 46 = 143 trong số 220 kỹ năng thực sự tăng hoặc giảm). Mô hình thận trọng: thà bỏ sót còn hơn báo nhầm.
- **Nhầm ngược chiều rất hiếm:** đoán Suy giảm khi thực tế Đang lên chỉ 18 lần, đoán Đang lên khi thực tế Suy giảm chỉ 1 lần. Khi mô hình báo một hướng, hướng đó hiếm khi sai bét.
- **Báo nhầm hướng ít:** báo Đang lên 12 lần, đúng 8 (precision 67%); báo Suy giảm 101 lần, đúng 50 (precision 50%).

| | Số lần mô hình đoán | Đoán đúng | Bỏ sót (recall) |
| --- | --- | --- | --- |
| Suy giảm | 101 | 50 | 66% bị bỏ sót |
| Đang lên | 12 | 8 | **89% bị bỏ sót** |

**Ý nghĩa thực tế:** mô hình phù hợp để *cảnh báo sớm một số kỹ năng suy giảm* hơn là *tìm ra kỹ năng sắp bùng nổ*. Điều này đáng nói thẳng nếu đề tài nhấn mạnh việc "dự đoán kỹ năng tương lai".

### 4.2 So sánh macro-F1 các mô hình (biểu đồ cột)

| Mô hình | Ngưỡng ±0,5 | **±1,0** | ±2,0 | Độ chính xác thô (±1,0) |
| --- | --- | --- | --- | --- |
| Luôn "Ổn định" (mốc) | 0,195 | **0,264** | 0,310 | 65,4% |
| `naive_last` | 0,506 | 0,498 | 0,417 | 69,8% |
| `ses` | 0,484 | 0,462 | 0,354 | 69,8% |
| `damped` | 0,392 | 0,368 | 0,365 | 67,5% |
| `ridge` | 0,477 | 0,477 | 0,422 | — |
| **`gbm` (dùng trên dashboard)** | 0,468 | **0,467** | 0,392 | 68,9% |
| `ridge+signals` | 0,466 | 0,465 | 0,438 | — |
| `gbm+signals` | 0,465 | 0,442 | 0,418 | — |

Nhận xét:
- **Mọi mô hình trong bảng đều vượt mốc "luôn Ổn định" ở cả ba ngưỡng** (`mean4` không có trong bảng vì nó luôn dự báo "Ổn định", nên trùng với mốc). Đây là kết quả vững: nó không phụ thuộc việc chọn đúng ngưỡng ±1.
- **Ngưỡng càng cao, lợi thế càng nhỏ.** Ở ±2,0, GBM hơn mốc chỉ +0,08 (0,392 so với 0,310), vì số trường hợp thay đổi mạnh quá ít (chỉ 84/636 quan sát).
- **`naive_last` nhỉnh hơn GBM** ở cả ba ngưỡng (0,498 so với 0,467 ở ±1). Nghĩa là trên holdout, một quy tắc chỉ nhìn quý cuối cùng còn bắt hướng tốt hơn một chút. GBM được chọn vì nó đứng đầu trên *dữ liệu chọn mô hình* (0,596 so với 0,458 của `naive_last`); đây là quy trình đặt trước, và báo cáo giữ nguyên thay vì đổi mô hình sau khi thấy kết quả.
- **GBM tụt từ 0,596 (chọn) xuống 0,467 (holdout)**, trong khi `naive_last` tăng từ 0,458 lên 0,498. Giai đoạn 2023–2026 khác giai đoạn trước (năm 2023–2024 nhiều kỹ năng giảm, năm 2025–2026 nhiều kỹ năng tăng, xem mục 4.3), nên mô hình học từ quá khứ gặp khó. Đây là bằng chứng cho thấy kết quả "chọn" lạc quan hơn thực tế.

### 4.3 Có ổn định theo thời gian không?

macro-F1 của dự báo trước 4 quý, nhóm theo năm của quý mục tiêu:

| Năm mục tiêu | Số quan sát | GBM | `naive_last` | Luôn "Ổn định" | Tỷ lệ thực tế Đang lên / Suy giảm |
| --- | --- | --- | --- | --- | --- |
| 2023 (chỉ Q4) | 53 | 0,322 | 0,289 | 0,183 | 2% / 60% |
| 2024 | 212 | 0,546 | 0,564 | 0,247 | 2% / 39% |
| 2025 | 212 | 0,353 | 0,442 | 0,288 | 15% / 9% |
| 2026 (tới Q3) | 159 | 0,454 | 0,425 | 0,273 | 22% / 9% |

- GBM **hơn mốc ở cả 4 năm** → kết quả gộp không do một năm may mắn kéo lên.
- Nhưng điểm số dao động từ 0,32 đến 0,55 và **2025 chỉ hơn mốc 0,06**. Con số 0,467 là trung bình của một thế giới thay đổi: năm 2023–2024 thị trường chủ yếu *suy giảm* (60% và 39% kỹ năng giảm), còn 2025–2026 chuyển sang *tăng* (15% và 22% kỹ năng tăng). Mô hình đoán Đang lên rất ít nên chịu thiệt ở hai năm sau.
- Mỗi năm chỉ có 2–4 quý mục tiêu và các quý này chồng lấn nhau, nên không nên đọc từng con số theo năm quá chi tiết; ý chính là xu hướng chung.

### 4.4 Theo nhóm kỹ năng (GBM, h=4)

| Nhóm | Số quan sát | Độ chính xác | Luôn đoán Ổn định đúng |
| --- | --- | --- | --- |
| AI/ML | 48 | 85,4% | 81,3% |
| Dữ liệu | 84 | 72,6% | 69,0% |
| Cloud/DevOps | 132 | 68,9% | 68,2% |
| Back-end | 60 | 68,3% | 63,3% |
| Ngôn ngữ | 204 | 67,6% | 60,8% |
| Front-end | 60 | 66,7% | 63,3% |
| Mobile | 36 | **50,0%** | 58,3% |

Mô hình hơn mốc ở hầu hết nhóm nhưng **kém mốc ở nhóm Mobile** (50% so với 58%). Mỗi nhóm chỉ vài chục quan sát từ vài kỹ năng, nên đây là gợi ý chứ không phải kết luận.

---

## 5. Tab "Kiểm chứng giá trị dự báo"

### 5.1 Sai số theo mô hình và horizon (MAE, điểm %, trên holdout)

| Mô hình | h = 1 | h = 2 | h = 3 | h = 4 | Thiên lệch ở h = 4 |
| --- | --- | --- | --- | --- | --- |
| `naive_last` (baseline) | 0,669 | 0,741 | 0,817 | 0,899 | +0,13 |
| `ses` | 0,635 | 0,716 | 0,796 | 0,889 | +0,15 |
| `damped` (mô hình giá trị) | 0,668 | 0,762 | 0,853 | 0,950 | +0,04 |
| `gbm` | 0,623 | 0,713 | 0,834 | 0,940 | −0,17 |

"Thiên lệch" là trung bình (dự báo − thực tế): dương là dự báo cao hơn thực tế, âm là thấp hơn. GBM **dự báo thấp hơn thực tế** (−0,17 điểm % ở h = 4), phù hợp với việc 2025–2026 nhiều kỹ năng tăng hơn mô hình nghĩ.

### 5.2 Biểu đồ "Có mô hình nào đánh bại giữ nguyên quý cuối?"
Chênh MAE so với `naive_last` (âm = tốt hơn), khoảng tin cậy 95% bootstrap theo 53 kỹ năng:

| Mô hình | Chênh | KTC 95% | Kết luận |
| --- | --- | --- | --- |
| `ses` | −0,023 | [−0,031; −0,015] | **Tốt hơn** (nhưng chỉ ≈ 0,02 điểm %) |
| `gbm` | −0,007 | [−0,041; 0,028] | Không phân biệt được |
| `gbm+signals` | −0,009 | [−0,044; 0,028] | Không phân biệt được |
| `damped` | +0,025 | [−0,006; 0,059] | Không phân biệt được |
| `ridge` | +0,036 | [0,004; 0,071] | Tệ hơn |
| `ridge+signals` | +0,034 | [0,002; 0,069] | Tệ hơn |
| `mean4` | +0,067 | [0,034; 0,109] | Tệ hơn |

Mô hình sản xuất cho giá trị là `damped` (được chọn vì sai số thấp nhất trên dữ liệu chọn mô hình). Nó **không** khác baseline có ý nghĩa, nên khung vàng "Chưa kiểm chứng" là đúng. `ses` thắng baseline nhưng mức hơn quá nhỏ về mặt thực tế (≈ 0,02 điểm % trên sai số ≈ 0,77).

### 5.3 Sai số có lớn không? Đặt trong ngữ cảnh
Tỷ lệ trung bình của một kỹ năng trong holdout là **4,4%**. Với h = 4, MAE ≈ 0,94 điểm % nghĩa là sai lệch tương đối **≈ 21%**; với h = 1 là ≈ 14%. Tỷ lệ dự báo nằm trong ±1 điểm % của thực tế ở **82% trường hợp (h=1) và 72% (h=4)**, nằm trong ±0,5 điểm % ở 57% và 45%. Sai số tăng ≈ 51% từ 1 lên 4 quý, gần song song ở mọi mô hình (biểu đồ "Sai số tăng theo thời gian dự báo"): dự báo xa vốn khó hơn, không phải lỗi riêng của mô hình nào.

### 5.4 Mức thay đổi dự báo giải thích được bao nhiêu thay đổi thực tế?
Đây là phép kiểm tra không có trên màn hình. Với dự báo trước 4 quý, so *thay đổi dự báo* (dự báo − trung bình 4 quý) với *thay đổi thực tế*:

| Mô hình | Tương quan | R² của thay đổi | Hệ số hồi quy |
| --- | --- | --- | --- |
| `gbm` | 0,234 | −0,035 | 0,46 |
| `damped` | 0,218 | 0,037 | 0,69 |
| `ses` | 0,457 | 0,194 | 1,19 |
| `naive_last` | 0,436 | 0,179 | 0,88 |

- Thay đổi thực tế có độ lệch chuẩn 1,48 điểm % và 35% trường hợp thay đổi hơn 1 điểm %.
- **GBM có tương quan thấp (0,23) và R² âm:** nếu coi mức thay đổi GBM dự báo là con số, nó tệ hơn việc dự báo "không đổi". `ses` và `naive_last` có tương quan gấp đôi (≈ 0,44–0,46), vì quán tính gần đây là tín hiệu thật.
- **Hệ quả cho cách trình bày:** *hướng* (ngưỡng ±1) của GBM có giá trị như đã chứng minh ở mục 4, nhưng *độ lớn* của mức thay đổi trên radar chỉ nên đọc như thứ tự tương đối, không phải số chính xác. Nên tránh câu "Python sẽ tăng 2 điểm %"; nên nói "Python được dự báo thuộc nhóm đang lên".

### 5.5 Mô hình sai ở đâu? (biểu đồ "Dự đoán so với thực tế")
Tám sai số lớn nhất của GBM ở h = 4 đều ≥ 5,8 điểm %, và 7/8 là **dự báo thấp hơn thực tế**:

| Kỹ năng | Quý mục tiêu | Dự báo | Thực tế | Trung bình 4 quý trước đó |
| --- | --- | --- | --- | --- |
| TypeScript | 2025Q3 | 16,7% | 25,5% | 17,8% |
| PostgreSQL | 2026Q1 | 12,4% | 19,8% | 12,7% |
| React | 2026Q1 | 17,8% | 24,9% | 20,1% |
| TypeScript | 2026Q1 | 19,0% | 25,9% | 19,5% |
| Python | 2025Q2 | 18,3% | 25,0% | 21,0% |

Đây là các bước tăng đột ngột của những kỹ năng lớn trong 2025–2026, mà mô hình dự báo gần như phẳng. Nguyên nhân chưa được xác minh; có thể do số tin mỗi quý giảm còn 700–1.100 (tỷ lệ dao động mạnh hơn) hoặc do thay đổi cơ cấu tin, và dữ liệu hiện có không đủ để phân biệt.

**Sai số tăng theo cỡ kỹ năng:** MAE tuyệt đối tương quan 0,90 với tỷ lệ trung bình của kỹ năng. Kỹ năng ≥ 10% có MAE trung vị ≈ 2,9 điểm %, kỹ năng < 3% chỉ ≈ 0,4 điểm %. Tuy nhiên tính theo *tỷ lệ tương đối*, kỹ năng nhỏ lại sai nhiều hơn (trung vị ≈ 36%) so với kỹ năng lớn (≈ 17%). Điều này giải thích vì sao các kỹ năng nhỏ bị loại khỏi diện dự báo (cần ≥ 1% tỷ lệ).

### 5.6 Khoảng dự báo 80% (dòng cuối của tab)
Độ phủ thực tế trên holdout là **79,98%**, và khớp mục tiêu ở từng horizon:

| Horizon | Độ phủ | Nửa độ rộng trung bình (điểm %) |
| --- | --- | --- |
| 1 quý | 80,0% | ±0,99 |
| 2 quý | 80,1% | ±1,12 |
| 3 quý | 80,0% | ±1,29 |
| 4 quý | 80,0% | ±1,36 |

Nhưng **độ phủ trung bình che một khuyết điểm theo cỡ kỹ năng:**

| Tỷ lệ của kỹ năng | Độ phủ thực tế (mục tiêu 80%) |
| --- | --- |
| < 3% | 85,4% (khoảng quá rộng) |
| 3–10% | 79,5% (đúng) |
| **≥ 10%** | **59,3% (khoảng quá hẹp)** |

Khoảng được co giãn theo √(p(1−p)), nhưng sai số thực của kỹ năng lớn còn tăng nhanh hơn thế. Hậu quả: dải xám trên biểu đồ của Python, React, TypeScript, AWS… **hẹp hơn mức nên có**; chỉ khoảng 6/10 giá trị thực rơi vào đó chứ không phải 8/10. Câu "khoảng 80% được hiệu chuẩn tốt" đúng với toàn bộ nhưng không đúng với những kỹ năng phổ biến nhất. Nếu có thời gian, cách sửa là tính phân vị sai số riêng theo nhóm cỡ kỹ năng.

---

## 6. Tab "Tín hiệu cộng đồng"

### 6.1 Thêm tín hiệu có giảm sai số không?
Chênh MAE khi thêm tín hiệu vào cùng loại mô hình (âm = tốt hơn):

| So sánh | 53 kỹ năng | 10 kỹ năng có tín hiệu |
| --- | --- | --- |
| `gbm+signals` − `gbm` | −0,0017 [−0,0059; 0,0033] | +0,0018 [−0,0157; 0,0274] |
| `ridge+signals` − `ridge` | −0,0020 [−0,0074; 0,0044] | +0,0185 [−0,0064; 0,0449] |

Mọi khoảng chứa 0, và các mức chênh chỉ cỡ 0,002 điểm % (cao nhất 0,0185) so với sai số ≈ 0,77 nên về mặt thực tế gần bằng 0. **Chưa có bằng chứng tín hiệu giúp dự báo.** Chú ý ở nhóm 10 kỹ năng có tín hiệu, `ridge+signals` còn có xu hướng *tệ hơn* (+0,019), nhưng khoảng cũng chứa 0.

### 6.2 Dẫn trước – trễ (biểu đồ npm và bản đồ nhiệt)
Tương quan trung bình giữa tăng trưởng lượt tải npm cách đây k quý và thay đổi nhu cầu hiện tại, trên 11 kỹ năng:

| Độ trễ k | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Tương quan TB | 0,071 | 0,046 | 0,078 | 0,111 | 0,079 | 0,106 | 0,110 |
| KTC 95% chứa 0? | có | có | có | có | có | có | có |
| p placebo | 0,36 | 0,64 | 0,36 | 0,17 | 0,31 | 0,16 | 0,16 |

- Tương quan dương nhỏ ở mọi độ trễ nhưng **khoảng tin cậy rộng (≈ ±0,25–0,27) và đều chứa 0**; placebo p > 0,15. Không có dấu hiệu npm đi trước nhu cầu. Tương quan ở k = 0 (cùng thời điểm) cũng chỉ 0,07, nên ngay cả quan hệ cùng lúc cũng yếu.
- **Sức mạnh thống kê thấp:** chỉ 11 kỹ năng, nên khoảng rộng. Kết quả đúng nhất là "không phát hiện được hiệu ứng với 11 kỹ năng", không phải "chắc chắn không có hiệu ứng".
- **Stack Overflow** (3 kỹ năng) có tương quan âm ở độ trễ dài (khoảng −0,1 đến −0,13), nhưng quá ít kỹ năng để kết luận (hai độ trễ có placebo p = 0 nhưng mẫu 3). Sự suy giảm câu hỏi Stack Overflow phản ánh xu hướng chung của nền tảng hơn là nhu cầu tuyển dụng. Dashboard hiển thị Stack Overflow là "mới có 3 kỹ năng, chưa đủ để kết luận" nên khớp phân tích này.
- **GitHub:** chưa có dữ liệu.

---

## 7. Hộp "Dữ liệu và giới hạn" (cuối trang)

Các giới hạn trong hộp đều ảnh hưởng tới cách đọc các chỉ số ở trên:
- **Một nguồn (Hacker News):** các dự báo là về *tỷ lệ tin trên Hacker News*, không phải thị trường việc làm nói chung. Một kỹ năng đang giảm trên HN có thể không giảm ở nơi khác.
- **Đếm từ khóa:** "có nhắc tới" chưa chắc là "đang tuyển". Sai sót nhận diện làm nhiễu cả nhãn thực tế lẫn dự báo.
- **Công ty đăng lặp lại:** vài công ty lớn có thể kéo tỷ lệ một kỹ năng (≈ 56% số tin đến từ tác giả đăng ≥ 5 lần).
- **Số tin mỗi quý giảm** (từ 2.315 còn 722–1.104): tỷ lệ mỗi quý nhiễu hơn, làm sai số dự báo khó giảm xuống dù mô hình tốt hơn.
- **Quy trình đặt trước:** chọn mô hình đến 2022Q4, chấm một lần trên 2023Q1–2026Q3. Đây là điểm mạnh về phương pháp: kết quả holdout không bị "chỉnh cho đẹp".

---

## 8. Câu hỏi hội đồng có thể hỏi

**1. "Mô hình của em chính xác bao nhiêu phần trăm?"**
Độ chính xác thô của nhãn hướng là 68,9%, nhưng đoán "Ổn định" cho mọi kỹ năng cũng đã đúng 65,4%. Vì vậy chúng em dùng macro-F1 (0,467 so với 0,264), chỉ số buộc mô hình phải bắt được cả kỹ năng tăng và giảm. Mức chênh +0,20 có ý nghĩa thống kê (KTC 95% [0,15; 0,25]).

**2. "Sao mô hình không dự đoán chính xác con số tỷ lệ?"**
Giữ nguyên quý cuối đã là baseline rất khó thắng với chuỗi này: tỷ lệ một kỹ năng thay đổi chậm, trong khi số tin mỗi quý ít nên có nhiễu lớn. Mô hình giá trị không thắng baseline có ý nghĩa thống kê, nên chúng em ghi "Chưa kiểm chứng" và dùng con số như kịch bản; chỉ nhãn hướng được kiểm chứng.

**3. "Mô hình hướng có thắng mô hình đơn giản nhất không?"**
Không hoàn toàn. Trên holdout, "giữ nguyên quý cuối" đạt 0,498 nhỉnh hơn GBM 0,467. GBM được chọn từ trước vì đứng đầu ở dữ liệu chọn mô hình (0,596 so với 0,458); chúng em không đổi mô hình sau khi nhìn thấy holdout để tránh chọn theo kết quả tốt nhất. Kết quả này cũng cho thấy kết quả giai đoạn chọn lạc quan hơn thực tế.

**4. "Mô hình có tìm ra kỹ năng sắp bùng nổ không?"**
Hạn chế lớn nhất của chúng em. Mô hình chỉ bắt được 11% kỹ năng thực sự tăng (8/72), nhưng khi nó báo "Đang lên" thì đúng 67% (8/12). Nó phù hợp để cảnh báo kỹ năng suy giảm (bắt được 34%, đúng 50% khi báo) hơn là phát hiện kỹ năng bùng nổ. Kỹ năng mới nổi như LLM bị loại vì chưa đủ lịch sử.

**5. "Kết quả có ổn định theo thời gian không?"**
GBM hơn mốc "luôn Ổn định" ở cả 4 năm của holdout, nhưng điểm dao động (0,32–0,55) và năm 2025 chỉ hơn 0,06. Thị trường đổi chế độ: năm 2023–2024 nhiều kỹ năng giảm, năm 2025–2026 nhiều kỹ năng tăng.

**6. "Tại sao React và TypeScript bị gắn 'Suy giảm' mà mô hình giá trị lại dự báo tăng?"**
Hai mô hình khác nhau và chúng em để lộ sự bất đồng đó. Nhãn do mô hình hướng (GBM) cho, còn con số do `damped` cho; chỉ Python và PostgreSQL được cả hai đồng ý là tăng. Hơn nữa, trên holdout, chính hai kỹ năng này nằm trong số các lần mô hình dự báo thấp nhất, nên nhãn "Suy giảm" cho chúng cần được đọc thận trọng.

**7. "Khoảng dự báo 80% có đáng tin không?"**
Phủ đúng 80,0% ở mọi horizon, nhưng với kỹ năng lớn (≥ 10% tỷ lệ) chỉ phủ 59%. Với Python hay React, nên đọc dải này như dải khoảng 60% chứ không phải 80%.

**8. "Giả thuyết cộng đồng đi trước tuyển dụng có đúng không?"**
Chưa có bằng chứng: thêm tín hiệu không giảm sai số, và tương quan dẫn trước của npm có khoảng tin cậy chứa 0 ở mọi độ trễ. Nhưng chỉ có 11 kỹ năng npm, 3 kỹ năng Stack Overflow và chưa có GitHub, nên kết luận chính xác là "chưa đủ dữ liệu để phát hiện", không phải "không có".

**9. "Dữ liệu Hacker News có đại diện cho Việt Nam không?"**
Không. Chỉ 15 trên 79.180 tin nêu Việt Nam là địa điểm. Kết quả dự báo là về nhu cầu công nghệ trên Hacker News, thiên về các công ty Mỹ.

---

## 9. Nếu còn thời gian, điều gì đáng làm nhất?

Xếp theo tác động lên chất lượng kết luận:

1. **Hiệu chuẩn khoảng dự báo theo cỡ kỹ năng** (mục 5.6): sửa được khuyết điểm 59% → ≈ 80% cho kỹ năng lớn, chỉ cần tính phân vị riêng cho từng nhóm cỡ. Chi phí thấp.
2. **Đưa dự báo lên trang đầu và nói rõ "hướng", không phải "con số"** (mục 5.4): tránh người xem hiểu sai độ lớn.
3. **Hoàn tất Stack Overflow và thêm GitHub** để câu hỏi nghiên cứu về tín hiệu cộng đồng có sức mạnh thống kê đủ để kết luận cả hai chiều.
4. **Dự báo cho kỹ năng mới nổi** (LLM, Generative AI): hiện bị loại; có thể dự báo theo nhóm (ví dụ nhóm AI/ML) để vượt hạn chế thiếu lịch sử.

---

## Phụ lục: nguồn và cách tính

| Chỉ số | Nguồn trong `gold.db` | Cách tính |
| --- | --- | --- |
| macro-F1, mốc, độ nhạy ngưỡng | `label_score`, `run_info` | F1 từng nhãn rồi lấy trung bình; mốc là luôn đoán "Ổn định" |
| Ma trận nhầm lẫn, precision/recall, độ chính xác, theo năm, theo nhóm | `backtest_cell` (mô hình `gbm`, `h = 4`) | nhãn thực tế = nhãn của `(thực tế − base4) × 100` với ngưỡng ±1; nhãn đoán tương tự từ `pred` |
| MAE, thiên lệch, tỷ lệ trong ±0,5 / ±1 | `backtest_cell` | `(pred − actual) × 100`; MAE là trung bình trị tuyệt đối |
| So với baseline (KTC) | `model_score` | bootstrap cặp theo kỹ năng, 2.000 lần, hạt giống 42 |
| Tương quan thay đổi dự báo – thực tế | `backtest_cell` (`h = 4`) | tương quan Pearson của `(pred − base4)` và `(actual − base4)`; R² = 1 − SSE/SST của thay đổi thực tế |
| Độ phủ khoảng 80% | `backtest_cell` (`damped`), `interval_quantile` | nửa độ rộng = phân vị × √(p(1−p)), p = `base4` (kẹp 0,01–0,99); phủ nếu `actual` nằm trong `pred ± nửa độ rộng` |
| Dẫn trước – trễ, hiệu ứng tín hiệu | `leadlag`, `leadlag_signal`, `model_score` | xem báo cáo, mục 7.2 và 7.5 |
| Radar hiện tại | `radar_series`, `radar_paths` | `delta_pp_4q = (GBM dự báo sau 4 quý − trung bình 4 quý gần nhất) × 100`; `forecast_4q` do `damped` dự báo |

`backtest_cell` chỉ lưu 4 mô hình chính (`naive_last`, `ses`, `damped`, `gbm`) trên 53 kỹ năng đủ điều kiện, các quý mục tiêu 2023Q1–2026Q3. Các số của `ridge`, `mean4` và các mô hình có tín hiệu lấy từ `label_score` và `model_score`. Các phân tích ở mục 3–6 mà màn hình không hiển thị (theo năm, theo nhóm, độ phủ theo cỡ, tương quan thay đổi, sai số lớn nhất) được tính trực tiếp từ `backtest_cell` và `radar_series`; chúng là phân tích bổ sung, chưa nằm trong pipeline hay dashboard.
