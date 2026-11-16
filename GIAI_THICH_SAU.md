# Giải thích chuyên sâu dự án Skill Radar

> Tài liệu này giải thích **dự án làm gì, dữ liệu từ đâu, xử lý ra sao, mô hình dự đoán thế nào và kết quả đáng tin tới mức nào**.
> Tệp liên quan: [GIAI_THICH_DU_AN.md](GIAI_THICH_DU_AN.md) (bản ngắn), [PROJECT_REPORT.md](PROJECT_REPORT.md) (số liệu đầy đủ).

---

## Phần 1. Bài toán và cách đặt vấn đề

**Đề tài:** Dự đoán xu hướng kỹ năng nghề nghiệp ngành CNTT.

Đề tài này không có sẵn dữ liệu "kỹ năng X sẽ hot năm sau". Vì vậy phải tự dựng ba thứ:

1. **Một thước đo nhu cầu** của từng kỹ năng, theo thời gian. Dự án dùng *tỷ lệ tin tuyển dụng có nhắc tới kỹ năng đó* trong mỗi quý.
2. **Một mô hình** nhìn lịch sử thước đo đó để đoán tương lai.
3. **Một cách kiểm tra trung thực** xem mô hình đoán có đúng không, hay chỉ là may mắn.

**Câu hỏi nghiên cứu bổ sung:** hoạt động cộng đồng (Stack Overflow, npm, GitHub) có tăng *trước* khi nhu cầu tuyển dụng tăng không? Nếu có, nó là "tín hiệu báo sớm" giúp dự đoán tốt hơn. Phần này được kiểm tra riêng và **chưa có bằng chứng ủng hộ**.

---

## Phần 2. Nguồn dữ liệu (ghi rõ)

### 2.1 Bảng tổng hợp

| # | Nguồn | Điểm truy cập | Dữ liệu lấy | Vai trò | Khóa API | Trạng thái |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | **Hacker News – "Ask HN: Who is hiring?"** | API Algolia HN: `https://hn.algolia.com/api/v1` (`/search_by_date`, `/items/{id}`) | 185 chuỗi hằng tháng từ 04/2011, toàn bộ bình luận. Giữ lại **93.354 tin tuyển dụng** | **Biến mục tiêu** (nhu cầu tuyển dụng) | Không cần | Xong |
| 2 | **npm** | API số lượt tải: `https://api.npmjs.org/downloads/range` | Lượt tải theo ngày → gộp theo tháng của 11 gói: `typescript`, `react`, `@angular/core`, `vue`, `jquery`, `svelte`, `next`, `graphql`, `tailwindcss`, `langchain`, `react-native`. 141 tháng (02/2015–10/2026) | Tín hiệu báo sớm | Không cần | Xong |
| 3 | **Stack Overflow** | API Stack Exchange 2.3: `https://api.stackexchange.com/2.3/questions` | Số câu hỏi theo thẻ (tag) và theo quý, từ 2011Q1. Đã có: tổng số câu hỏi, `javascript`, `python`, `typescript` (63 quý), `java` (mới 28 quý) | Tín hiệu báo sớm | Tùy chọn (`SE_API_KEY`); không khóa chỉ 300 lượt/ngày | **Chạy dở** |
| 4 | **GitHub Archive** | Dự kiến lấy mẫu theo giờ bằng Spark | — | Tín hiệu báo sớm | — | **Chưa làm** (không có dữ liệu) |

Tệp tải về từ API (bộ nhớ đệm) nằm ở `skill_radar/data/raw/` (hn, npm, stackexchange), khoảng 46 MB. Dữ liệu thô được nạp vào cơ sở dữ liệu SQLite `warehouse.db` (bảng `bronze_comment`); mọi bước sau đọc/ghi trong cơ sở dữ liệu, không còn file JSON/parquet kết quả.

### 2.2 Vì sao chọn Hacker News làm nguồn nhu cầu?

**Ưu điểm**
- Công khai, miễn phí, có API ổn định, **không cần khóa**.
- Chuỗi thời gian rất dài và đều đặn: mỗi tháng một chuỗi, từ 2011 đến nay.
- Mỗi tin do chính công ty tự đăng nên phản ánh nhu cầu thật, không phải tin lặp do bot hay môi giới.
- Dữ liệu ở dạng văn bản, cho phép tự trích xuất kỹ năng thay vì phụ thuộc nhãn có sẵn.

**Nhược điểm (cần nói rõ khi bảo vệ)**
- Chỉ phản ánh cộng đồng Hacker News: thiên về startup, công nghệ, thị trường Mỹ và làm việc từ xa. **Không đại diện cho thị trường Việt Nam hay toàn bộ ngành CNTT.**
- Không phải khảo sát có kiểm soát nên không biết số tin có đại diện cho nhu cầu thực không.
- Số tin mỗi quý đã giảm (khoảng 2.200 tin vào 2015–2022, còn 722 ở 2026Q3), nên kỹ năng hiếm dao động mạnh.

### 2.3 Cách thu thập từng nguồn

**Hacker News (`ingest/hn.py`)**
1. Gọi `search_by_date` với `tags=story,author_whoishiring`, `hitsPerPage=1000`, phân trang.
2. Lọc các bài có tiêu đề khớp `^ask hn: who is hiring?`, sắp theo thời gian.
3. Với mỗi bài, gọi `items/{id}` một lần: API trả cả cây bình luận.
4. Lưu nguyên văn dạng nén: `raw/hn/{id}.json.gz` + `threads.json`.
5. Lỗi 429/5xx thì chờ tăng dần rồi thử lại tối đa 5 lần; nghỉ 0,4 giây giữa các yêu cầu; đã có tệp thì bỏ qua (cache).

**npm (`ingest/npm.py`)**
- API chỉ cho khoảng thời gian tối đa khoảng 18 tháng mỗi lần, nên chia thành cửa sổ 500 ngày rồi nối lại.
- Cộng lượt tải theo tháng và **chỉ giữ tháng đủ ngày** (bỏ tháng đầu dở dang và tháng hiện tại) để tránh số liệu bị thiếu giả tạo.
- Mỗi gói lưu riêng, lỗi giữa chừng chạy lại sẽ tiếp tục.

**Stack Overflow (`ingest/stackexchange.py`)**
- Mỗi lần gọi trả về `total` số câu hỏi của một (thẻ, khoảng thời gian), nên không cần tải nội dung câu hỏi.
- Thứ tự "xong thẻ này mới sang thẻ khác" để thẻ nào xong là dùng được ngay; kết quả ghi nối vào CSV nên chạy lại tiếp tục chỗ dừng.
- Chưa xong vì hạn mức 300 lượt/ngày: cần 68 thẻ × 63 quý.

---

## Phần 3. Xử lý dữ liệu: từ văn bản lộn xộn tới con số

Dùng mô hình **Bronze → Silver → Gold**:

| Tầng | Ý nghĩa | Ở đây |
| --- | --- | --- |
| Bronze | Dữ liệu thô, giữ nguyên | `warehouse.db`: `bronze_thread`, `bronze_comment` (HTML gốc) |
| Silver | Đã làm sạch, mỗi dòng một đối tượng | `warehouse.db`: `postings` (mỗi dòng một tin), `posting_skills` (cặp tin–kỹ năng), `posting_features` (remote, lương, cấp bậc, địa điểm, công ty) |
| Gold | Đã tổng hợp để phân tích | `gold.db`: dự báo, kết quả backtest, lead-lag và các bảng cho dashboard (nhỏ, đưa lên git) |

Giữ Bronze nguyên vẹn nghĩa là nếu sau này phát hiện lỗi luật xử lý, chỉ cần sửa và chạy lại, không phải tải lại.

### 3.1 Ví dụ thật, đi qua từng bước

Một tin thật trong chuỗi tháng 6/2025 (bình luận id `44164731`).

**Bronze (dữ liệu thô, là HTML):**
```
elide.dev | Multiple Roles | REMOTE OR OFFICE (US) | Full-time &amp; Part-time | Kotlin + Rust<p>Elide, a new runtime built in Kotlin, and which runs JavaScript&#x2F;TypeScript, Kotlin, Python, WASM, and soon Ruby.<p><a href="https:&#x2F;&#x2F;elide.dev" ...>...
```

**Bước làm sạch:** bỏ thẻ `<p>`, `<a>`; giải mã `&amp;` → `&`, `&#x2F;` → `/`; gộp khoảng trắng.

**Silver (văn bản sạch):**
```
elide.dev | Multiple Roles | REMOTE OR OFFICE (US) | Full-time & Part-time | Kotlin + Rust Elide, a new runtime built in Kotlin, and which runs JavaScript/TypeScript, Kotlin, Python, WASM, and soon Ruby. ...
```

**Nhận diện kỹ năng:** hệ thống tìm thấy 7 kỹ năng:
`javascript, kotlin, python, ruby, rust, typescript, webassembly`
→ sinh 7 dòng trong `hn_posting_skills`.

**Nhận xét trung thực:** tin này thật ra tuyển **Kotlin và Rust**, nhưng Python, Ruby, WASM chỉ được nhắc như ngôn ngữ mà sản phẩm hỗ trợ. Phương pháp đếm "có nhắc tới" vẫn tính chúng. Đây là một **hạn chế đã biết** (xem Phần 7). Khi gộp hàng chục nghìn tin, sai lệch kiểu này ảnh hưởng ít tới *xu hướng* hơn là tới *mức tuyệt đối*, nhưng chưa được đo.

### 3.2 Các quy tắc lọc và vì sao cần
1. **Chỉ bình luận cấp cao nhất là tin tuyển dụng.** Trả lời (hỏi đáp, bàn luận) bị loại vì không phải tin tuyển dụng.
2. **Bỏ tin rỗng hoặc dưới 50 ký tự.** 2 tin rỗng/đã xóa và 208 tin quá ngắn bị bỏ; mọi tin bị bỏ đều được đếm và ghi vào `hn_report.json`.
3. **Kỳ thời gian lấy theo tháng ghi trong tiêu đề bài**, vì bài thường được đăng sớm 1–2 ngày (nếu dùng ngày tạo, tin tháng 7 có thể bị tính vào tháng 6).
4. **Khử trùng theo id bình luận** khi một tháng có hai chuỗi (0 trường hợp trùng).
5. **Bỏ tháng đang diễn ra** (chưa đủ dữ liệu) và các quý có dưới 2 tháng dữ liệu, để tỷ lệ không bị lệch.
6. **Chỉ dùng chuỗi liên tục từ 2015Q3.** Một số tháng của năm 2015 bị thiếu; code sẽ báo lỗi nếu chuỗi có khoảng trống.

### 3.3 Nhận diện kỹ năng bằng danh mục luật (`taxonomy.py`)

Không dùng mô hình ngôn ngữ mà dùng **danh mục 75 kỹ năng**, mỗi kỹ năng có các cách viết:

| Nhóm | Số kỹ năng | Ví dụ |
| --- | --- | --- |
| Ngôn ngữ | 20 | Python, Java, Go, Rust, SQL |
| Front-end | 9 | React, Vue, Next.js, GraphQL |
| Back-end | 8 | Django, Node.js, Laravel |
| Dữ liệu | 12 | PostgreSQL, Kafka, Spark |
| AI/ML | 10 | Machine Learning, PyTorch, LLM |
| Cloud/DevOps | 11 | AWS, Docker, Kubernetes |
| Mobile | 4 | Android, iOS, Flutter |
| Khác | 1 | Blockchain |

Từ nhập nhằng được xử lý riêng:
- **"Go"**: chỉ tính khi viết hoa đúng "Go", không đứng trước các từ như *to, for, with, team, market*… (tránh "go to market").
- **"Java"** không khớp bên trong "JavaScript"; **"React"** không khớp "React Native" (là kỹ năng riêng).
- **"Swift", "iOS", "RAG"**: phân biệt hoa/thường vì chữ thường là từ tiếng Anh bình thường.
- Quy tắc ký tự biên: không khớp nếu dính chữ, dấu chấm, `#`, `+` ngay trước/sau (ví dụ `c++` và `c#` được xử lý đúng).

Kết quả: 71.571 trên 93.354 tin (khoảng 76,7%) nhắc tới ít nhất một kỹ năng trong danh mục; trung bình khoảng 4 kỹ năng mỗi tin.

### 3.4 Biến thành thước đo nhu cầu

```
tỷ lệ(kỹ năng, quý) = số tin trong quý nhắc kỹ năng / tổng số tin trong quý
```

Dùng **tỷ lệ** thay vì số tuyệt đối vì tổng số tin mỗi quý thay đổi, và ta muốn biết *thị phần chú ý* của kỹ năng. Ví dụ Python ở năm gần nhất có tỷ lệ khoảng 25,1%, nghĩa là cứ 4 tin thì khoảng 1 tin nhắc Python.

Sau bước này ta có bảng **75 kỹ năng × 45 quý** (2015Q3 → 2026Q3), cùng các cột tín hiệu (`se_share`, `npm_dl`, `gh_share`); chỗ nào thiếu thì để trống, **không điền bù**.

---

## Phần 4. Mô hình dự đoán

Nguyên tắc: **bắt đầu từ cách đơn giản nhất, rồi xem mô hình phức tạp có hơn không.** Nếu không hơn thì không có lý do dùng.

| Mô hình | Ý tưởng một câu |
| --- | --- |
| Giữ nguyên quý cuối (`naive_last`) | Quý sau bằng quý này |
| Trung bình 4 quý (`mean4`) | Lấy trung bình cả năm, loại bớt dao động |
| Làm mượt mũ (`ses`) | Trung bình có trọng số, quý mới nặng hơn |
| Xu hướng giảm dần (`damped`) | Kéo đường thẳng qua 8 quý gần nhất, nhưng đà tăng/giảm yếu dần |
| Ridge / Gradient Boosting | Máy học học chung từ tất cả kỹ năng |
| Ridge/GBM **+ tín hiệu** | Như trên, thêm tốc độ tăng của npm, Stack Overflow |

Đặc trưng của máy học: độ lệch ba quý gần nhất so với mức nền, độ dốc 8 quý, mức nền, số tin của quý, nhóm kỹ năng; với bản "+ tín hiệu" thêm tốc độ tăng của tín hiệu.

Hai việc dự đoán, hai mô hình riêng:
- **Dự đoán giá trị** (tỷ lệ bao nhiêu %): chọn `damped`.
- **Dự đoán hướng** (Đang lên / Ổn định / Suy giảm): chọn `gbm`.

Nhãn hướng định nghĩa: so tỷ lệ dự báo sau 4 quý với trung bình 4 quý gần nhất. Lệch hơn **+1,0 điểm %** là Đang lên, thấp hơn **−1,0 điểm %** là Suy giảm, còn lại là Ổn định.

---

## Phần 5. Cách kiểm tra trung thực

Đây là phần giúp kết quả đáng tin.

1. **Cắt thời gian cứng.** Dữ liệu đến hết 2022 dùng để chọn mô hình và tham số. Giai đoạn **2023–2026 chỉ chấm điểm một lần**, mô hình chưa từng thấy.
2. **Mô hình không được nhìn thấy tương lai.** Với mỗi thời điểm dự đoán, chỉ đưa vào các quý đã xảy ra. Có bài test tự động kiểm tra điều này.
3. **Quy tắc đặt trước.** Giao thức (ngưỡng, horizon, kỹ năng đủ điều kiện ≥ 1%) cố định trước khi xem kết quả.
4. **So sánh với baseline đơn giản** và dùng **bootstrap theo kỹ năng** để có khoảng tin cậy 95%. Nếu khoảng tin cậy chứa 0 thì coi như *không khác biệt*, không được tuyên bố hơn.
5. **Placebo cho phân tích báo sớm.** Ghép nhu cầu của kỹ năng này với tín hiệu của kỹ năng khác để xem "ngẫu nhiên" cho ra tương quan cỡ nào.

Chỉ 53 trong 75 kỹ năng đủ điều kiện (tỷ lệ trung bình ≥ 1% giai đoạn 2015–2022). Kỹ năng quá hiếm có tỷ lệ dao động quá ồn nên không dự đoán đáng tin.

---

## Phần 6. Kết quả

### 6.1 Dự đoán hướng: có giá trị (đã kiểm chứng)
- Mô hình `gbm`: macro-F1 = **0,466**.
- Luôn đoán "Ổn định": macro-F1 = **0,264**.
- Chênh lệch **+0,203**, khoảng tin cậy 95% là **[0,146; 0,254]**, không chứa 0, nên mô hình hướng thật sự tốt hơn đoán bừa.
- Lưu ý trung thực: ở ngưỡng 0,5 và 1,0, cách "giữ nguyên quý cuối" còn nhỉnh hơn một chút (0,498 so với 0,466 ở ngưỡng 1,0) trên giai đoạn kiểm tra. Mô hình `gbm` được chọn từ trước trên giai đoạn chọn mô hình nên báo cáo nguyên trạng.

### 6.2 Dự đoán giá trị: chưa hơn baseline
Sai số trung bình (điểm %) trên 2023–2026:
- Giữ nguyên quý cuối: **0,775**
- `damped` (mô hình được chọn): 0,800 (chênh +0,025, khoảng [−0,006; 0,059], không khác biệt)
- Chỉ `ses` thắng baseline có ý nghĩa (0,751), nhưng chỉ nhỉnh 0,02 điểm %.

Nghĩa là: với chuỗi này, **cách đơn giản "giữ nguyên" rất khó đánh bại**. Vì vậy dashboard ghi rõ "chưa kiểm chứng" cho con số dự báo, coi là kịch bản chứ không phải lời hứa.

### 6.3 Độ chính xác của khoảng dự báo
Khoảng dự báo 80% phủ đúng **79,98%** các giá trị thực trên giai đoạn kiểm tra, tức khoảng không quá hẹp hay quá rộng.

### 6.4 Tín hiệu cộng đồng: không giúp
- Thêm tín hiệu vào mô hình: sai số thay đổi chỉ khoảng ±0,002 điểm %, khoảng tin cậy luôn chứa 0.
- Phân tích "đi trước bao nhiêu quý" (0 đến 6 quý): npm không có tương quan đáng kể ở bất kỳ độ trễ nào. Stack Overflow có tương quan âm nhẹ nhưng chỉ dựa trên 3 kỹ năng, không đủ để kết luận.

**Kết luận cho câu hỏi nghiên cứu:** với dữ liệu hiện có, **chưa có bằng chứng** rằng hoạt động cộng đồng đi trước nhu cầu tuyển dụng. Đây là kết quả âm tính, và cần nói rõ là *"chưa đủ dữ liệu để khẳng định"* chứ không phải *"chắc chắn không có"* (do mới có 3 kỹ năng Stack Overflow và chưa có GitHub).

### 6.5 Bức tranh thị trường (dự báo hướng sau 1 năm)
Trong 53 kỹ năng đủ điều kiện:

| Nhãn | Số lượng | Kỹ năng |
| --- | --- | --- |
| Đang lên | 2 | Python (25,1% → 27,0%), PostgreSQL (18,4% → 19,8%) |
| Suy giảm | 3 | TypeScript (23,8% → 24,6%), React (22,7% → 23,0%), Go (7,3% → 7,0%) |
| Ổn định | 48 | AWS, Machine Learning, Kubernetes, Rust, Docker… |

Ghi chú: nhãn dựa trên mô hình hướng (`gbm`), còn con số tỷ lệ dự báo dựa trên mô hình giá trị (`damped`). Hai mô hình khác nhau nên đôi khi nhãn và con số không cùng chiều (ví dụ TypeScript có tỷ lệ dự báo cao hơn năm qua nhưng nhãn là Suy giảm). Đây là điểm cần giải thích khi trình bày.

---

## Phần 7. Hạn chế

1. **Một nguồn nhu cầu duy nhất, thiên lệch.** Hacker News ≠ thị trường lao động. Muốn nói về Việt Nam cần thêm nguồn như tin tuyển dụng ở Việt Nam.
2. **Đếm "có nhắc tới" ≠ "đang tuyển kỹ năng đó".** Như ví dụ Elide ở Phần 3.1. Chưa đo độ chính xác của phương pháp này so với người gán nhãn.
3. **Tín hiệu báo sớm còn mỏng**: Stack Overflow mới 3 kỹ năng dùng được, GitHub chưa có.
4. **Kỹ năng mới nổi** (LLM, GenAI, RAG, LangChain) chưa đạt ngưỡng 1% ở giai đoạn 2015–2022 nên bị xếp "Chưa đủ bằng chứng", dù đây có thể là nhóm đáng quan tâm nhất hiện nay. Đây là hệ quả của quy tắc đặt trước.
5. **Dự đoán con số chưa hơn baseline**, chỉ dự đoán hướng được kiểm chứng.
6. **Số tin giảm theo thời gian** nên số liệu quý gần đây nhiễu hơn.

## Phần 8. Hướng cải thiện (nếu có thêm thời gian)
- Đặt khóa `SE_API_KEY` để hoàn tất Stack Overflow cho 68 thẻ, và thêm GitHub Archive: tăng sức mạnh thống kê cho câu hỏi "có đi trước không".
- Thêm nguồn tuyển dụng thứ hai (ưu tiên nguồn Việt Nam) để kiểm tra kết quả có còn đúng không.
- Gán nhãn thủ công khoảng vài trăm tin để đo độ chính xác của bộ nhận diện kỹ năng.
- Phân biệt "kỹ năng yêu cầu" với "kỹ năng chỉ được nhắc" (ví dụ chỉ tính phần đầu tin, nơi thường ghi vị trí tuyển).

## Phần 9. Cách chạy
```powershell
pip install -r requirements.txt
python -m skill_radar.ingest.hn            # tải dữ liệu Hacker News (có cache)
python -m skill_radar.ingest.npm
python -m skill_radar.ingest.stackexchange # đặt SE_API_KEY để chạy đủ trong 1 ngày
python -m skill_radar.process.hn_postings  # nạp Bronze, làm sạch + nhận diện kỹ năng + đặc trưng -> warehouse.db
python -m skill_radar.process.signals      # nạp npm / Stack Overflow vào warehouse.db
python -m skill_radar.pipeline             # kiểm tra, dự đoán, bảng phân tích -> gold.db
python -m streamlit run skill_radar/app.py --server.port 8502   # dashboard
python -m pytest -q tests
```

## Phần 10. Các phân tích bổ sung (từ 2026-11-16)
Chi tiết kế hoạch và trạng thái: [KE_HOACH_CAI_TIEN.md](KE_HOACH_CAI_TIEN.md). Dashboard có 6 trang; các chỉ số dưới đây là **thống kê mô tả** từ regex, không thuộc quy trình kiểm chứng ở Phần 5.

- **Đặc trưng tin** (`process/features.py`): làm từ xa / onsite / hybrid, có nêu lương (kèm lương USD/năm trung điểm cho khoảng 5,2 nghìn tin), equity, visa, cấp bậc, loại hợp đồng, thành phố/khu vực (250 ký tự đầu), công ty (trường đầu của tin dạng `Công ty | Địa điểm | ...`).
- **Quan sát chính:** remote tăng từ ~19% (2015) lên 83% (2022) rồi giảm còn ~54% (2026); tỷ lệ tin nêu lương từ 2% lên 26%; tin nhắc cấp senior từ 34% lên 57%; Việt Nam gần như không xuất hiện (~0,1%), nên kết quả không nói được gì về thị trường Việt Nam.
- **Hệ sinh thái** (`ecosystem.py`): đếm đồng xuất hiện, PPMI, khoảng cách cosine, phân cụm Ward (6 cụm: AI/ML; Web; Backend–Cloud; Mobile–Hệ thống; hệ Microsoft; C++/Java/Linux), bố cục t-SNE. Silhouette 0,15: cụm chồng lấn.
- **Skill Navigator** (`navigator.py`): một tin "phù hợp" khi người dùng biết ≥ X% số kỹ năng nêu trong tin; gợi ý kỹ năng học tiếp theo bằng thuật toán tham lam.
- **Điểm yếu còn lại:** chưa có nhãn thủ công để đo độ chính xác của regex (kỹ năng và đặc trưng); tín hiệu cộng đồng vẫn thiếu Stack Overflow đầy đủ và GitHub.
