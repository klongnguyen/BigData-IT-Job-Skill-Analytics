# Skill Radar — Báo cáo toàn bộ dự án

> Phân tích thị trường tuyển dụng CNTT và dự báo nhu cầu kỹ năng từ dữ liệu lớn.
> Mọi số liệu dưới đây lấy trực tiếp từ hai cơ sở dữ liệu SQLite `skill_radar/data/warehouse.db` và `skill_radar/data/gold.db` (kết quả pipeline tạo lúc 2026-11-16 11:39 UTC) và từ mã nguồn trong `skill_radar/`. Mô tả giao diện khớp với dashboard hiện tại; hướng dẫn thao tác từng màn hình nằm ở [HUONG_DAN_SU_DUNG.md](HUONG_DAN_SU_DUNG.md).

---

## 1. Tổng quan

**Câu hỏi nghiên cứu:** hoạt động cộng đồng lập trình viên (Stack Overflow, npm, GitHub) có *đi trước* nhu cầu tuyển dụng một kỹ năng không, và có giúp *dự báo* nhu cầu đó không?

**Biến mục tiêu (nhu cầu):** tỷ lệ tin tuyển dụng nhắc tới một kỹ năng, theo quý
`share = số tin có nhắc kỹ năng / tổng số tin trong quý`.

**Nguồn nhu cầu:** các chuỗi hằng tháng "Ask HN: Who is hiring?" trên Hacker News (185 chuỗi, 93.354 tin; 79.180 tin trong khoảng mô hình hóa 2015Q3–2026Q3).

**Sản phẩm:** một kho dữ liệu SQLite theo mô hình Bronze → Silver → Gold, một pipeline phân tích và dự báo có kiểm chứng, và một dashboard Streamlit 7 màn hình (nền trắng, biểu đồ tương tác) để người dùng khám phá xu hướng kỹ năng và kiểm tra độ tin cậy của dự báo.

**Kết luận ngắn (chi tiết ở mục 7):**
- Dự báo **hướng** thay đổi sau 4 quý (Đang lên / Ổn định / Suy giảm) **vượt** baseline "luôn Ổn định" (macro-F1 0,4672 so với 0,2636, khoảng tin cậy 95% của mức chênh [0,147; 0,255]) và đã được kiểm chứng trên holdout 2023–2026.
- Dự báo **giá trị tỷ lệ** **không vượt** baseline đơn giản "giữ nguyên quý cuối", nên chỉ coi là kịch bản.
- **Tín hiệu cộng đồng không làm dự báo tốt hơn**: thêm tín hiệu không giảm sai số có ý nghĩa thống kê, và quan hệ dẫn trước – trễ không có bằng chứng (npm) hoặc chưa đủ dữ liệu (Stack Overflow, GitHub).
- Phân tích mô tả cho thấy thị trường thay đổi mạnh: tin nhắc làm từ xa tăng từ 19% (2015) lên đỉnh 85% (2022Q1) rồi còn 54% (4 quý gần nhất); tin nêu mức lương tăng từ 1,4% (2015) lên 24% (4 quý gần nhất).

---

## 2. Cấu trúc dự án và kiến trúc dữ liệu

```
BigData_Job_Analy/
├── README.md                  # trỏ sang skill_radar/README.md
├── PROJECT_REPORT.md          # tệp này
├── HUONG_DAN_SU_DUNG.md       # hướng dẫn từng màn hình, từng biểu đồ, từng trường dữ liệu
├── KE_HOACH_CAI_TIEN.md       # kế hoạch cải tiến và trạng thái từng giai đoạn
├── GIAI_THICH_DU_AN.md, GIAI_THICH_SAU.md   # giải thích dự án
├── requirements.txt           # numpy, scipy, scikit-learn, pandas, requests, streamlit, plotly, pytest
├── tests/
│   ├── test_skill_radar.py    # kiểm thử nhận diện, mô hình, backtest
│   └── test_features_db.py    # kiểm thử đặc trưng, SQLite, hệ sinh thái, navigator, giao diện
└── skill_radar/
    ├── taxonomy.py            # danh mục 75 kỹ năng + luật nhận diện
    ├── ingest/                # thu thập (hn.py, npm.py, stackexchange.py)
    ├── process/
    │   ├── hn_postings.py     # Bronze -> Silver (tin, kỹ năng, đặc trưng, nhu cầu)
    │   ├── features.py        # trích xuất remote, lương, cấp bậc, địa điểm, công ty...
    │   └── signals.py         # nạp tín hiệu npm, Stack Overflow vào kho
    ├── db.py, store.py        # truy cập SQLite; ghi/đọc kết quả dạng bảng
    ├── panel.py               # ghép nhu cầu + tín hiệu thành bảng quý
    ├── models.py, backtest.py, leadlag.py   # mô hình, backtest, dẫn trước – trễ
    ├── pipeline.py            # chạy toàn bộ và ghi gold.db
    ├── analytics.py           # các bảng phân tích cho dashboard
    ├── ecosystem.py, navigator.py, insights.py, drivers.py   # phân cụm, lộ trình học, tóm tắt, giải thích tăng/giảm
    ├── app.py                 # dashboard Streamlit (điểm vào)
    ├── ui/                    # giao diện: theme.py, interact.py, data.py và 7 trang trong ui/pages/
    └── data/
        ├── raw/               # bộ nhớ đệm phản hồi API (≈46 MB, không đưa lên git)
        ├── warehouse.db       # Bronze + Silver (≈303 MB, không đưa lên git)
        └── gold.db            # kết quả cuối cho dashboard (≈17 MB, đưa lên git)
```

Dữ liệu lưu trong **cơ sở dữ liệu SQLite**, không còn tệp JSON hay parquet làm đầu ra. Kiến trúc **Bronze → Silver → Gold**:

| Tầng | Nơi lưu | Bảng chính |
| --- | --- | --- |
| Bronze | `warehouse.db` | `bronze_thread` (185 chuỗi), `bronze_comment` (93.564 bình luận, HTML gốc, chưa sửa) |
| Silver | `warehouse.db` | `postings` (93.354 tin đã làm sạch), `posting_skills` (285.733 cặp tin–kỹ năng), `posting_features` (93.354 dòng đặc trưng), `demand_month` (13.875), `demand_quarter` (4.725), `etl_report`, `signal_npm_month` (1.551), `signal_se_quarter` (280) |
| Gold (dự báo) | `gold.db` | `radar_series` (75), `radar_paths` (300), `radar_history` (3.375), `backtest_cell` (11.448) và các bảng kết quả: `run_info`, `selection_score`, `model_score`, `model_horizon_error`, `label_score`, `interval_quantile`, `leadlag`, `leadlag_signal`, `leadlag_skill` |
| Gold (phân tích) | `gold.db` | `posting` (79.180, không có văn bản; tác giả chỉ còn mã ẩn danh), `posting_skill` (246.865), `market_quarter` (45), `skill_year` (900), `skill_attr_year` (844), `skill_salary` (147), `skill_pair_window` (1.334), `skill_pair_year` (20.171), `skill_cluster` (75), `location_year` (455), `employer` (1.975), `signal_quarter` (659), `event`, `gold_fact` |

Dashboard chỉ đọc `gold.db` ở chế độ chỉ đọc; chạy dashboard không cần `warehouse.db` hay mạng. `gold.db` không chứa nội dung văn bản tin và không có tên tác giả. Lý do chọn SQLite thay vì một máy chủ cơ sở dữ liệu: dữ liệu là bảng quan hệ cỡ vài trăm MB, một người dùng, cần chạy lại trên máy khác chỉ bằng cách chép một tệp; SQLite đáp ứng đủ mà không cần cài đặt dịch vụ.

---

## 3. Thu thập dữ liệu (`ingest/`)

### 3.1 Nhu cầu — Hacker News "Who is hiring?" (`ingest/hn.py`) — **hoàn tất**
- **API:** Algolia HN (`hn.algolia.com/api/v1`), không cần khóa.
- **Cách làm:** (1) `search_by_date` với tag `story,author_whoishiring`, phân trang 1000 kết quả, lọc tiêu đề khớp `^ask hn: who is hiring?`; (2) mỗi chuỗi gọi `items/{id}` một lần để lấy cả cây bình luận.
- **Bền bỉ:** thử lại tối đa 5 lần với back-off lũy thừa khi gặp 429/5xx; nghỉ 0,4 s giữa các yêu cầu; User-Agent định danh là client học thuật.
- **Cache:** mỗi chuỗi lưu `data/raw/hn/{id}.json.gz` và danh sách `threads.json`; chạy lại không tải lần hai. Sau đó nạp vào `bronze_thread`, `bronze_comment`.
- **Quy mô:** **185 chuỗi** (từ 04/2011 đến 11/2026), 93.564 bình luận.

### 3.2 Tín hiệu — npm (`ingest/npm.py`) — **hoàn tất**
- **API:** `api.npmjs.org/downloads/range` (giới hạn ~18 tháng/lần nên chia cửa sổ 500 ngày).
- **Phạm vi:** 11 gói tương ứng 11 kỹ năng: `typescript`, `react`, `@angular/core`, `vue`, `jquery`, `svelte`, `next`, `graphql`, `tailwindcss`, `langchain`, `react-native`.
- **Xử lý:** cộng lượt tải theo tháng, **chỉ giữ tháng đủ ngày** (bỏ tháng đầu dở dang và tháng hiện tại). Mỗi gói lưu riêng để tiếp tục được khi lỗi. Mỗi gói có 141 tháng (2015-02 → 2026-10); 1.551 dòng trong `signal_npm_month`.

### 3.3 Tín hiệu — Stack Overflow (`ingest/stackexchange.py`) — **chạy dở**
- **API:** Stack Exchange 2.3 `/questions` với `filter=total`, đếm câu hỏi theo (tag, quý) từ 2011Q1.
- **Hạn mức:** 300 lượt/ngày nếu không có khóa; đặt biến môi trường `SE_API_KEY` để có 10.000 lượt/ngày (khóa chỉ đọc từ môi trường, không ghi ra đĩa). Chạy tiếp nối được.
- **Hiện có (280 dòng trong `signal_se_quarter`):** tổng câu hỏi (`__all__`), `javascript`, `python`, `typescript` (đủ 63 quý) và `java` (mới 28 quý, chưa đủ để dùng).
- **Hệ quả:** chỉ **3 kỹ năng** (Python, JavaScript, TypeScript) có tín hiệu Stack Overflow dùng được.

### 3.4 Tín hiệu — GitHub Archive — **chưa làm**
`panel.py` đã có hàm `gh_signal()` nhưng chưa có dữ liệu nên số kỹ năng có tín hiệu `gh_share` = 0.

| Nguồn | Vai trò | Trạng thái | Kỹ năng có tín hiệu |
| --- | --- | --- | --- |
| Hacker News | Mục tiêu (nhu cầu) | Xong | 75 (tất cả) |
| npm | Tín hiệu | Xong | 11 |
| Stack Overflow | Tín hiệu | Dở dang | 4 (3 dùng được trong lead-lag) |
| GitHub Archive | Tín hiệu | Chưa làm | 0 |

---

## 4. Xử lý dữ liệu

### 4.1 Danh mục kỹ năng (`taxonomy.py`)
- **75 kỹ năng**, 8 nhóm: ngôn ngữ, front-end, back-end, dữ liệu, AI/ML, cloud/DevOps, mobile, khác.
- Mỗi kỹ năng có `aliases` (cách viết trong văn bản), `category`, và ánh xạ tín hiệu (`se_tag`, `npm`, `gh`).
- **Cú pháp alias:** chuỗi thường → khớp token nguyên, không phân biệt hoa/thường; `re:` → regex không phân biệt hoa/thường; `cs:` → regex **phân biệt hoa/thường** cho các từ trùng tiếng Anh thường ("Go", "Swift", "iOS", "RAG").
- Ví dụ xử lý nhập nhằng: "Go" chỉ tính khi viết hoa và không đi sau/trước các từ như *to, for, with, team, market…*; "React" không tính khi là "React Native" (kỹ năng riêng); "Java" không bị lẫn với "JavaScript".

### 4.2 Bronze → Silver (`process/hn_postings.py`)
Quy tắc ảnh hưởng đến thống kê:
1. Chỉ **bình luận cấp cao nhất** là tin tuyển dụng (trả lời là thảo luận, bị loại).
2. Kỳ lấy theo **tháng ghi trong tiêu đề chuỗi** (`(November 2026)`), không theo ngày tạo. Nếu không đọc được tiêu đề thì dùng ngày tạo.
3. Tháng có hai chuỗi được gộp và khử trùng theo `comment_id`.
4. Làm sạch HTML: bỏ thẻ **trước**, giải mã entity **sau**, chuẩn hóa khoảng trắng.
5. Bỏ tin dưới **50 ký tự**; mọi tin bị loại đều được đếm và báo cáo.
6. Gắn kỹ năng bằng các mẫu regex đã biên dịch.

**Báo cáo xử lý (`etl_report`):**

| Chỉ số | Giá trị |
| --- | --- |
| Số chuỗi | 185 |
| Số tháng | 185 (04/2011 → 11/2026) |
| Số quý | 63 |
| Bình luận Bronze | 93.564 |
| **Tin tuyển dụng giữ lại** | **93.354** |
| Bị loại: rỗng/đã xóa | 2 |
| Bị loại: quá ngắn (<50 ký tự) | 208 |
| Bị loại: trùng id | 0 |
| Tin nhắc ≥ 1 kỹ năng | 71.571 (≈76,7%) |
| Cặp (tin, kỹ năng) | 285.733 |

### 4.3 Đặc trưng mô tả của tin (`process/features.py`)
Từ văn bản mỗi tin, các luật regex tạo thêm các cột lưu ở `posting_features` (chi tiết luật ở phụ lục B của hướng dẫn sử dụng):

| Nhóm | Trường | Ghi chú |
| --- | --- | --- |
| Hình thức làm việc | `is_remote`, `is_onsite`, `is_hybrid` | một tin có thể thuộc nhiều hình thức |
| Lương và quyền lợi | `has_salary`, `salary_usd_k`, `has_equity`, `has_visa` | mức lương USD/năm, trung điểm của khoảng, giữ 30–700 nghìn USD |
| Cấp bậc, hợp đồng | `is_senior`, `is_junior`, `is_intern`, `is_fulltime`, `is_parttime`, `is_contract` | không tính "smart contract" |
| Địa điểm | `city`, `region` | tìm trong 250 ký tự đầu của tin |
| Công ty | `company` | trường đầu của tin dạng "Công ty \| Địa điểm \| …"; đọc được ≈ 85% tin |

Các đặc trưng này là **đếm từ khóa**, chưa được đối chiếu với nhãn gán tay (xem mục 12).

### 4.4 Bảng nhu cầu và bảng quý để mô hình hóa
`demand_panel()` tính cho mỗi (kỳ, kỹ năng): `posts_with_skill`, `total_posts`, `n_months`, `share`, lưới đầy đủ 75 kỹ năng × mọi kỳ (không xuất hiện = 0).

`panel.py` đọc từ SQLite và:
- Loại **tháng đang diễn ra** và quý có **< 2 tháng** dữ liệu (`MIN_MONTHS = 2`).
- Ghép tín hiệu bằng `left join`, thiếu vẫn là `NaN`, **không điền bù**: `se_share` = câu hỏi của tag / tổng câu hỏi trong quý; `npm_dl` = tổng lượt tải của quý (chỉ quý đủ 3 tháng); `gh_share` chưa có.
- **Chuỗi mô hình:** từ **2015Q3** (các tháng 2015 trước đó bị thiếu ở nguồn) tới **2026Q3** = **45 quý liên tục**, không khoảng trống (`to_panel` báo lỗi nếu có). Tổng **79.180 tin**; trong đó 60.681 tin nhắc ít nhất một kỹ năng, từ 26.435 tác giả (ẩn danh).
- Số tin mỗi quý giảm từ 2.315 (2015Q3) xuống 722 (2026Q3), nên tỷ lệ của kỹ năng hiếm dao động mạnh.

---

## 5. Mô hình dự báo (`models.py`)

Mọi mô hình cùng giao diện `predict(view, horizons)`; `view` chỉ chứa các quý **nhìn thấy được tại thời điểm dự báo**, nên mô hình không thể đọc tương lai (có test riêng).

| Mô hình | Mô tả |
| --- | --- |
| `naive_last` | Giữ nguyên giá trị quý cuối |
| `mean4` | Trung bình 4 quý gần nhất (một năm, loại mùa vụ) |
| `ses` | Làm mượt mũ đơn giản, hệ số α |
| `damped` | Xu hướng OLS 8 quý cuối, động lượng giảm dần theo hệ số φ |
| `ridge`, `gbm` | Mô hình gộp mọi kỹ năng; chỉ dùng lịch sử tuyển dụng |
| `ridge+signals`, `gbm+signals` | Như trên nhưng thêm tăng trưởng tín hiệu cộng đồng |

Chi tiết mô hình gộp: đặc trưng gồm độ lệch 3 quý cuối so với trung bình 4 quý, độ dốc 8 quý, mức nền, log tổng số tin, one-hot nhóm kỹ năng; với `+signals` thêm log-tăng-trưởng của từng tín hiệu (kẹp ±3) và cờ "có tín hiệu". Mục tiêu là *thay đổi so với mức nền*. Ridge: chuẩn hóa + α=10. GBM: 150 cây, độ sâu 2, learning rate 0,05, subsample 0,8, seed 42. Chỉ dự báo tới 4 quý, cần ≥ 8 quý lịch sử.

---

## 6. Quy trình đánh giá (đặt trước khi chấm điểm)

Giao thức cố định trong `backtest.py` trước khi chấm bất kỳ mô hình nào:

- **Chuỗi:** 2015Q3–2026Q3 (45 quý); horizon 1–4 quý.
- **Cửa sổ chọn mô hình:** các mốc dự báo có mục tiêu ≤ **2022Q4**. Tham số (α, φ) và mô hình sản xuất chỉ được chọn ở đây.
- **Holdout:** mục tiêu **2023Q1 → 2026Q3**, chấm **một lần**.
- **Kỹ năng đủ điều kiện:** tỷ lệ trung bình ≥ **1%** trong cửa sổ chọn (quyết định không dùng holdout) → **53 / 75 kỹ năng**.
- **Nhãn hướng:** Rising / Stable / Fading theo thay đổi 4 quý so với trung bình năm cuối, ngưỡng **±1,0 điểm %** (độ nhạy 0,5 và 2,0).
- **Độ đo:** MAE (điểm %), macro-F1 của nhãn; so sánh cặp (cùng ô origin×horizon cho mọi mô hình) bằng **bootstrap cặp theo kỹ năng** (2.000 lần, seed 42), khoảng tin cậy 95%.
- **Dự báo khoảng:** khoảng 80% theo phân vị sai số chuẩn hóa `|dự báo−thực|/√(p(1−p))`, tính riêng từng horizon.

**Tham số chọn trên cửa sổ chọn** (bảng `selection_score`):

| Tham số | Lưới và MAE (điểm %) | Chọn |
| --- | --- | --- |
| α của SES | 0,2→1,0468 · 0,4→0,7906 · 0,6→0,7339 · **0,8→0,7253** | **0,8** |
| φ của damped | **0,25→0,7202** · 0,5→0,7225 · 0,75→0,7457 · 0,9→0,7835 | **0,25** |

**Chọn mô hình sản xuất (chỉ trong số mô hình không dùng tín hiệu, trên cửa sổ chọn):**

| Mô hình | MAE chọn (điểm %) | Macro-F1 nhãn |
| --- | --- | --- |
| naive_last | 0,7407 | 0,4581 |
| mean4 | 0,8077 | 0,2670 |
| ses | 0,7253 | 0,4090 |
| **damped** | **0,7202** (mô hình giá trị) | 0,4213 |
| ridge | 0,8280 | 0,5560 |
| **gbm** | 0,7649 | **0,5962** (mô hình hướng) |

---

## 7. Kết quả

### 7.1 Holdout 2023Q1–2026Q3 — sai số giá trị (53 kỹ năng)

Baseline tốt nhất: `naive_last`. Chênh lệch dương = tệ hơn baseline.

| Mô hình | MAE (điểm %) | h=1 | h=2 | h=3 | h=4 | Chênh vs baseline [KTC 95%] |
| --- | --- | --- | --- | --- | --- | --- |
| naive_last | **0,7746** | 0,669 | 0,741 | 0,817 | 0,899 | — |
| mean4 | 0,8421 | 0,691 | 0,801 | 0,906 | 1,010 | +0,067 [0,034; 0,109] tệ hơn |
| **ses** | **0,7514** | 0,635 | 0,716 | 0,796 | 0,889 | −0,023 [−0,031; −0,015] **tốt hơn** |
| damped | 0,7995 | 0,668 | 0,762 | 0,853 | 0,950 | +0,025 [−0,006; 0,059] không khác biệt |
| ridge | 0,8109 | 0,637 | 0,743 | 0,883 | 1,030 | +0,036 [0,004; 0,071] tệ hơn |
| gbm | 0,7675 | 0,623 | 0,713 | 0,834 | 0,940 | −0,007 [−0,041; 0,028] không khác biệt |
| ridge+signals | 0,8089 | 0,637 | 0,738 | 0,880 | 1,030 | +0,034 [0,002; 0,069] tệ hơn |
| gbm+signals | 0,7657 | 0,622 | 0,710 | 0,833 | 0,938 | −0,009 [−0,044; 0,028] không khác biệt |

**Diễn giải:** mô hình sản xuất cho giá trị là `damped` (chọn trên cửa sổ chọn) **không vượt** `naive_last` trên holdout (khoảng tin cậy chứa 0). Chỉ `ses` thắng baseline có ý nghĩa, nhưng chênh lệch chỉ ≈ 0,02 điểm %. Giữ nguyên quý cuối là baseline rất khó thắng với chuỗi này. Vì vậy dashboard ghi *"Chưa kiểm chứng"* cho giá trị dự báo và coi đó là kịch bản.

### 7.2 Tín hiệu cộng đồng có giúp dự báo không? (hiệu ứng cùng lớp mô hình)

| So sánh | Toàn bộ 53 kỹ năng | 10 kỹ năng có tín hiệu |
| --- | --- | --- |
| ridge+signals − ridge | −0,002 điểm % [−0,007; 0,004] | +0,019 [−0,006; 0,045] |
| gbm+signals − gbm | −0,002 điểm % [−0,006; 0,003] | +0,002 [−0,016; 0,027] |

Mọi khoảng tin cậy chứa 0 → **không có bằng chứng** rằng Stack Overflow/npm cải thiện dự báo. Trên 10 kỹ năng có tín hiệu, sai số của mọi mô hình cao hơn hẳn (MAE `naive_last` = 1,167 điểm %) vì đây là các kỹ năng lớn, biến động mạnh.

### 7.3 Dự báo hướng (nhãn 4 quý, 636 quan sát holdout)

Macro-F1 theo ngưỡng (phân bố nhãn quan sát ở ngưỡng 1,0: Fading 148 · Stable 416 · Rising 72):

| Mô hình | ±0,5 | **±1,0** | ±2,0 |
| --- | --- | --- | --- |
| Luôn "Stable" | 0,1945 | 0,2636 | 0,3098 |
| naive_last | 0,5057 | 0,4977 | 0,4171 |
| ses | 0,4837 | 0,4620 | 0,3535 |
| damped | 0,3920 | 0,3683 | 0,3653 |
| ridge | 0,4765 | 0,4766 | 0,4216 |
| **gbm** (mô hình hướng) | 0,4679 | **0,4672** | 0,3918 |
| ridge+signals | 0,4659 | 0,4648 | 0,4383 |
| gbm+signals | 0,4645 | 0,4420 | 0,4182 |

**Kiểm chứng mô hình hướng (`gbm`, bootstrap cụm theo kỹ năng):** macro-F1 = **0,4672** so với **0,2636** của "luôn Stable"; **mức tăng +0,2035, KTC 95% [0,1467; 0,2549] → `validated = true`**. Lưu ý: ở ngưỡng 0,5 và 1,0, `naive_last` còn nhỉnh hơn `gbm` trên holdout; mô hình hướng được chọn *trước* trên cửa sổ chọn nên báo cáo nguyên trạng, không chọn lại.

Một ghi chú về khả năng tái lập: kết quả GBM thay đổi nhẹ giữa hai lần chạy ở hai môi trường phần mềm khác nhau (macro-F1 0,4662 so với 0,4672; MAE 0,7679 so với 0,7675). Nhãn quan sát không đổi và kết quả ổn định khi chạy lại trong cùng một môi trường; mọi số liệu trong báo cáo này là của lần chạy hiện tại.

### 7.4 Khoảng dự báo
Phân vị 80% của sai số chuẩn hóa theo horizon: h1 = 0,0531 · h2 = 0,0602 · h3 = 0,0689 · h4 = 0,0727. **Độ phủ thực tế trên holdout: 79,98%** (mục tiêu 80%) — khoảng được hiệu chuẩn tốt.

### 7.5 Phân tích dẫn trước – trễ (`leadlag.py`)
Với mỗi kỹ năng: x = log-tăng-trưởng 1 năm của tín hiệu, y = thay đổi 1 năm của tỷ lệ nhu cầu; tính tương quan `corr(x[t−k], y[t])` với k = 0..6 quý (k>0: tín hiệu *dẫn trước*). Suy luận **theo kỹ năng** (không theo thời gian vì thay đổi năm bị chồng lấn): bootstrap khoảng tin cậy trên các kỹ năng, và **placebo** ghép nhu cầu của kỹ năng này với tín hiệu của kỹ năng khác.

**Stack Overflow** (3 kỹ năng: python, javascript, typescript):

| Độ trễ k (quý) | Tương quan TB | KTC 95% | p placebo |
| --- | --- | --- | --- |
| 0 | −0,007 | [−0,013; 0,003] | 1,000 |
| 1 | −0,037 | [−0,126; 0,023] | 1,000 |
| 2 | −0,094 | [−0,226; −0,027] | 0,229 |
| 3 | −0,127 | [−0,268; −0,049] | 0,183 |
| 4 | −0,129 | [−0,227; −0,061] | 0,186 |
| 5 | −0,115 | [−0,147; −0,062] | 0,000 |
| 6 | −0,122 | [−0,255; 0,028] | 0,000 |

**npm** (11 kỹ năng):

| Độ trễ k (quý) | Tương quan TB | KTC 95% | p placebo |
| --- | --- | --- | --- |
| 0 | 0,071 | [−0,174; 0,336] | 0,360 |
| 1 | 0,046 | [−0,222; 0,330] | 0,640 |
| 2 | 0,078 | [−0,190; 0,342] | 0,358 |
| 3 | 0,111 | [−0,155; 0,361] | 0,170 |
| 4 | 0,079 | [−0,172; 0,344] | 0,312 |
| 5 | 0,106 | [−0,165; 0,360] | 0,158 |
| 6 | 0,110 | [−0,135; 0,365] | 0,156 |

**GitHub:** không có dữ liệu (`leadlag_signal`: "too few skills with this signal").

**Diễn giải:** với npm mọi khoảng tin cậy chứa 0 và placebo p > 0,15 → không có tín hiệu dẫn trước. Với Stack Overflow, tương quan **âm** nhẹ ở độ trễ dài, nhưng chỉ dựa trên 3 kỹ năng (không đủ để kết luận; 2 độ trễ có placebo p = 0 song mẫu quá nhỏ), và sự giảm của câu hỏi Stack Overflow phản ánh xu hướng chung của nền tảng hơn là nhu cầu tuyển dụng. Kết luận trung thực: **chưa có bằng chứng cho giả thuyết nghiên cứu**.

### 7.6 Đầu ra radar: nhãn cho 53 kỹ năng đủ điều kiện
Phân bố nhãn (`radar_series`): **Stable 48 · Fading 3 · Rising 2**; 22 kỹ năng còn lại "Chưa đủ bằng chứng".

Các kỹ năng nhiều tin nhất năm qua. Hai cột dự báo đến từ **hai mô hình khác nhau**: "Dự báo 4 quý" là tỷ lệ do mô hình giá trị `damped` dự báo; "Thay đổi" (điểm %) và nhãn do mô hình hướng `gbm` dự báo (`delta = (gbm dự báo sau 4 quý − trung bình 4 quý gần nhất) × 100`, nhãn theo ngưỡng ±1,0). Vì vậy hai cột đôi khi lệch nhau chút ít hoặc ngược chiều:

| Kỹ năng | Nhóm | Tỷ lệ năm qua | Dự báo 4 quý | Thay đổi | Nhãn |
| --- | --- | --- | --- | --- | --- |
| Python | ngôn ngữ | 25,1% | 27,0% | +1,99 | **Rising** |
| TypeScript | ngôn ngữ | 23,8% | 24,6% | −1,13 | **Fading** |
| React | front-end | 22,7% | 23,0% | −1,79 | **Fading** |
| PostgreSQL | dữ liệu | 18,4% | 19,9% | +1,35 | **Rising** |
| AWS | cloud | 15,6% | 15,8% | −0,29 | Stable |
| Machine Learning | AI | 14,9% | 14,9% | −0,67 | Stable |
| LLM | AI | 13,4% | (15,0%) | (+3,24) | Chưa đủ bằng chứng |
| Kubernetes | cloud | 9,3% | 9,7% | +0,09 | Stable |
| Rust | ngôn ngữ | 8,4% | 9,3% | +0,53 | Stable |
| Go | ngôn ngữ | 7,3% | 7,0% | −1,21 | **Fading** |
| Node.js | back-end | 7,0% | 7,7% | +0,23 | Stable |
| Docker | cloud | 6,2% | 7,1% | +0,87 | Stable |
| Terraform | cloud | 5,8% | 6,1% | −0,15 | Stable |

Quan sát: Python, PostgreSQL đang lên; TypeScript, React, Go đang suy giảm; phần còn lại ổn định. Kỹ năng AI mới nổi (LLM, Generative AI, LangChain, RAG) và Next.js chưa đạt ngưỡng 1% trong cửa sổ chọn (2015–2022) nên bị xếp "Chưa đủ bằng chứng" thay vì được gán nhãn; giá trị trong ngoặc ở dòng LLM chỉ để tham khảo, không được kiểm chứng. Đây là hệ quả của quy tắc đặt trước, cần lưu ý khi diễn giải.

Dự báo sản xuất cho các quý **2026Q4, 2027Q1, 2027Q2, 2027Q3** (4 quý × 75 kỹ năng = 300 dòng trong `radar_paths`) kèm khoảng 80%.

---

## 8. Phân tích mô tả thị trường

Ngoài dự báo, pipeline tạo các bảng phân tích để người dùng hiểu thị trường. Phần này là **thống kê mô tả** từ luật regex, không thuộc quy trình kiểm chứng ở mục 6.

### 8.1 Làm từ xa, lương, cấp bậc (`market_quarter`, `skill_attr_year`, `skill_salary`)

| Năm | Số tin | Remote | Onsite | Hybrid | Nêu lương | Equity | Senior |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2015 | 3.991 | 19,0% | 56,6% | 0,6% | 1,4% | 7,3% | 33,4% |
| 2019 | 8.434 | 31,6% | 72,8% | 0,9% | 5,8% | 7,9% | 48,7% |
| 2021 | 10.272 | 80,5% | 27,7% | 3,4% | 4,4% | 7,1% | 55,7% |
| 2022 | 7.576 | 83,2% | 22,7% | 9,4% | 7,1% | 9,4% | 55,0% |
| 2024 | 3.892 | 60,3% | 30,4% | 19,8% | 15,6% | 13,2% | 51,6% |
| 2026 (tới Q3) | 2.641 | 53,7% | 34,7% | 20,2% | 25,3% | 22,3% | 57,9% |

- Tỷ lệ tin nhắc remote đạt đỉnh **85,4% ở 2022Q1**, sau đó giảm dần; hybrid tăng từ <1% lên ≈ 20%. Một tin có thể nhắc nhiều hình thức nên các cột không cộng thành 100%.
- Tỷ lệ tin nêu mức lương tăng từ 1,4% (2015) lên **24,3%** trong 4 quý gần nhất. Trong tin nêu lương USD/năm, **trung vị 145 nghìn USD** (4.941 tin, toàn bộ giai đoạn) và **180 nghìn USD** ở 8 quý gần nhất (1.403 tin). Nhóm tin nêu lương thay đổi theo thời gian và thiên về công ty Mỹ, nên đây **không phải mức lương thị trường**.
- Tỷ lệ tin nhắc senior tăng từ 33% lên ≈ 58%; tỷ lệ tin nhắc junior/thực tập thấp (khoảng 4% và 3%).

### 8.2 Hệ sinh thái kỹ năng (`ecosystem.py`, `skill_pair_window`, `skill_cluster`)
Tính trên **12 quý gần nhất** (2023Q4–2026Q3, 11.536 tin):
- **Lift** `P(A và B) / (P(A)·P(B))` đo hai kỹ năng thật sự đi cùng nhau. Các cặp lift cao nhất đều là cặp quen thuộc: pandas–scikit-learn (86), PHP–Laravel (74), Swift–Objective-C (73), TensorFlow–PyTorch (48). Các cặp có ít tin (ví dụ pandas–scikit-learn chỉ 9 tin) nên lift cao đi cùng độ không chắc chắn lớn; dashboard chỉ nối các cặp có ≥ 25 tin.
- **Phân cụm:** PPMI (log của lift, chặn 0) → khoảng cách `1 − cosine` → phân cụm Ward; số cụm chọn theo silhouette trong các k mà mỗi cụm có 5–35% số kỹ năng; bố cục bản đồ bằng t-SNE. Kết quả: **6 cụm** cho 68 kỹ năng có đủ dữ liệu (7 kỹ năng "ít dữ liệu"), silhouette **0,149**.

| Cụm (tên trên dashboard, số kỹ năng) | Kỹ năng trong cụm (rút gọn) |
| --- | --- |
| Machine Learning · LLM · Generative AI (10) | pandas, Deep Learning, TensorFlow, PyTorch, scikit-learn, LangChain, RAG |
| React · TypeScript · PostgreSQL (15) | JavaScript, Ruby, PHP, Vue, Next.js, GraphQL, Node.js, Ruby on Rails, MySQL |
| Python · AWS · Kubernetes (22) | Go, Scala, Django, FastAPI, MongoDB, Redis, Kafka, Airflow, Snowflake, GCP |
| Rust · iOS · React Native (8) | Swift, Kotlin, Elixir, Android, Flutter |
| SQL · Azure · C# (6) | Angular, .NET, Serverless |
| C++ · Java · Linux (7) | WebAssembly, Computer Vision, Jenkins, Blockchain |

Silhouette 0,149 là thấp: các cụm gợi ý nhóm công nghệ chứ **không phải ranh giới rõ ràng**.

### 8.3 Skill Navigator (`navigator.py`)
Người dùng chọn bộ kỹ năng đang có; một tin **phù hợp** khi người dùng biết ≥ X% số kỹ năng được nêu trong tin (mặc định 50%, chỉ tính tin nhắc ≥ 1 kỹ năng trong danh mục). Hệ thống tính **độ phủ thị trường**, xếp hạng **kỹ năng nên học tiếp** theo số tin trở thành phù hợp, và đề xuất lộ trình 6 bước **tham lam** (mỗi bước chọn kỹ năng tăng độ phủ nhiều nhất; không bảo đảm tối ưu toàn cục). Đây là phép đếm trên tin quá khứ, không phải dự đoán cơ hội việc làm.

### 8.4 Phân tích "vì sao kỹ năng tăng/giảm" (`drivers.py`) — đã cài đặt, đang tạm ẩn khỏi giao diện
Mô-đun này giải thích **thay đổi đến từ đâu**, không khẳng định nguyên nhân: điểm gãy xu hướng (đường gấp khúc hai độ dốc), tách thay đổi thành phần "chính kỹ năng được nhắc nhiều hơn" và phần "cơ cấu tin thay đổi" (shift-share, hai phần cộng đúng bằng tổng), độ rộng nhà tuyển dụng (số tác giả ẩn danh khác nhau), kỹ năng đồng biến/ngược chiều, và các giá trị đầu vào mà mô hình hướng đọc. Ví dụ với LLM: tỷ lệ tăng từ 2,4% lên 13,3%, phần lớn do chính kỹ năng được nhắc nhiều hơn chứ không do cơ cấu tin, số nhà tuyển dụng nhắc tăng từ 66 lên 309, điểm gãy rơi vào 2022Q2 gần mốc ChatGPT ra mắt. Phần này được ẩn khỏi dashboard bằng công tắc `SHOW_WHY = False` trong `ui/pages/profile.py` (mã và test vẫn còn).

---

## 9. Dashboard (`app.py`, `ui/`)

Chạy: `python -m streamlit run skill_radar/app.py --server.port 8502` → http://127.0.0.1:8502. Giao diện tiếng Việt, **nền trắng cố định**, đọc duy nhất `gold.db`. Thanh công cụ của Plotly và thao tác kéo thả phóng to bị tắt (một biểu đồ bị phóng to không có cách quay lại); thao tác còn lại là rê chuột xem số liệu, bấm vào điểm/cột để chọn kỹ năng, và nút "3 năm / 5 năm / Tất cả" trên biểu đồ theo quý.

**Bấm để chọn kỹ năng:** trên các biểu đồ bấm được, kỹ năng vừa bấm trở thành *kỹ năng đang chọn* (hiện ở thanh bên với nút **Bỏ chọn**), biểu đồ làm mờ phần còn lại, và bên dưới hiện khung chi tiết kèm nút mở Hồ sơ kỹ năng.

| Màn hình | Nội dung |
| --- | --- |
| **Tổng quan** | 5 ô chỉ số (số tin phân tích, số kỹ năng theo dõi, kỹ năng phổ biến nhất, kỹ năng tăng nhanh nhất, giảm mạnh nhất so với 4 quý trước); treemap kỹ năng theo nhóm (diện tích = số tin, màu = thay đổi); biểu đồ vùng cơ cấu lượt nhắc theo nhóm; biểu đồ cuộc đua xếp hạng theo năm với thanh trượt chọn khoảng hạng (xem được cả hạng 16 trở xuống, bấm vào đường để mở chi tiết) |
| **Xu hướng** | 4 thẻ: So sánh kỹ năng (chọn tới 8 kỹ năng, tỷ lệ hoặc chỉ số đỉnh = 100, làm mượt 4 quý, vạch sự kiện COVID-19 / ChatGPT / sa thải hàng loạt), Bản đồ nhiệt, Thắng – thua, Vị thế & động lượng (bong bóng, bấm được) |
| **Hồ sơ kỹ năng** | Một kỹ năng: 5 ô chỉ số, lịch sử + kịch bản 4 quý tới có dải 80%, "chân dung" tin tuyển so với thị trường (remote, lương, senior…), kỹ năng hay đi kèm |
| **Hệ sinh thái** | 3 thẻ: Bản đồ công nghệ (t-SNE, tô màu theo cụm, bấm được), Bạn đồng hành của một kỹ năng, Ma trận lift |
| **Thị trường** | 3 thẻ: Làm từ xa (remote/onsite/hybrid theo quý; kỹ năng nào "remote" nhất), Lương & quyền lợi (minh bạch lương, trung vị lương công bố, lương theo kỹ năng), Cấp bậc & hợp đồng |
| **Skill Navigator** | Chọn bộ kỹ năng, hồ sơ mẫu, ngưỡng phù hợp, lọc remote/có lương; kết quả độ phủ, kỹ năng nên học tiếp, lộ trình tham lam, độ "ăn khách" của bộ kỹ năng theo thời gian |
| **Dự báo & độ tin cậy** | Hai khung trạng thái ("Đã kiểm chứng" cho nhãn hướng, "Chưa kiểm chứng" cho giá trị); 4 thẻ: Radar 1 năm tới (bấm được, có bảng và tải CSV), Kiểm chứng nhãn hướng (ma trận nhầm lẫn, macro-F1 từng mô hình), Kiểm chứng giá trị dự báo (chênh sai số so với baseline, sai số theo horizon, dự đoán so với thực tế), Tín hiệu cộng đồng (hiệu ứng thêm tín hiệu, dẫn trước – trễ npm) |

Bảng màu 8 nhóm kỹ năng cố định ở mọi biểu đồ; hai màu xanh/đỏ dành cho tăng/giảm. Các bảng địa lý (`location_year`) và nhà tuyển dụng (`employer`) vẫn nằm trong `gold.db` nhưng đã bỏ khỏi giao diện vì ít liên quan tới câu hỏi chọn kỹ năng.

---

## 10. Kiểm thử

**75 test**, đã chạy lại và **đạt cả 75** (`python -m pytest -q tests`, khoảng 30 giây).

- `tests/test_skill_radar.py` (13 test): luật nhận diện kỹ năng; bỏ thẻ HTML trước khi giải mã entity; taxonomy hợp lệ; kỳ lấy từ tiêu đề; mẫu số của tỷ lệ là toàn bộ tin; `to_panel` từ chối khoảng trống; **không mô hình nào nhìn thấy quý sau mốc dự báo**; mô hình gộp trả NaN khi lịch sử ngắn; `damped` khớp đường thẳng đã biết; ô chọn mô hình không chạm holdout; tính đủ điều kiện không dùng holdout; ranh giới nhãn; backtest chạy end-to-end và **tái lập được**.
- `tests/test_features_db.py` (62 ca sau khi mở rộng tham số): trích xuất đặc trưng (remote/hybrid, lương, cấp bậc, địa điểm, công ty); ghi/đọc SQLite và vòng khứ hồi `store`; hệ sinh thái (co-occurrence, lift, phân cụm); Skill Navigator; các hàm `insights`; `drivers` (điểm gãy, shift-share cộng đúng tổng, độ rộng, đồng biến); và **mọi trang dashboard import được** (một lỗi cú pháp ở một trang từng làm cả ứng dụng không chạy mà các test khác không phát hiện).

Ngoài test tự động, dashboard được kiểm tra thủ công bằng trình duyệt thật (Playwright): bấm chọn kỹ năng trên các biểu đồ bấm được, nền trắng khi hệ điều hành đặt chế độ tối, không còn nút thanh công cụ Plotly, kéo chuột không làm biểu đồ nhảy trục, thanh trượt hạng, tiêu đề không bị thanh header che.

---

## 11. Cách chạy lại toàn bộ

```powershell
pip install -r requirements.txt
python -m skill_radar.ingest.hn            # tải 185 chuỗi (có cache)
python -m skill_radar.ingest.npm
python -m skill_radar.ingest.stackexchange # đặt SE_API_KEY để chạy đủ trong 1 ngày
python -m skill_radar.process.hn_postings  # Bronze -> Silver (warehouse.db), ~6 phút
python -m skill_radar.process.signals      # nạp npm/Stack Overflow vào warehouse.db
python -m skill_radar.pipeline             # backtest + lead-lag + dự báo + bảng phân tích -> gold.db, ~1,5 phút
python -m streamlit run skill_radar/app.py --server.port 8502
python -m pytest -q tests
```

Đổi luật trích xuất đặc trưng trong `process/features.py`: chạy `python -m skill_radar.process.hn_postings --features-only` (~1,5 phút) rồi chạy lại `pipeline`. Chỉ cần xem dashboard thì không phải chạy các bước trên: `gold.db` đã có trong kho mã.

---

## 12. Hạn chế và việc còn lại

1. **Một nguồn nhu cầu duy nhất** (Hacker News): thiên lệch về startup/công nghệ và thị trường Mỹ, làm từ xa; không đại diện toàn ngành. Chỉ 15 tin (≈ 0,02%) nêu Việt Nam là địa điểm, nên **kết quả không nói được gì về thị trường Việt Nam**. Số tin/quý giảm theo thời gian (còn ≈ 700–1.100 tin/quý gần đây).
2. **Nhận diện bằng từ khóa/regex**: cả kỹ năng lẫn các đặc trưng mô tả (remote, lương, cấp bậc, địa điểm, công ty) có thể sót hoặc nhầm; **chưa được đo độ chính xác với nhãn người gán**. "Tin nhắc kỹ năng" chưa chắc là "đang cần người biết kỹ năng đó".
3. **Tín hiệu mỏng:** Stack Overflow mới 3 kỹ năng dùng được (tag `java` dở dang), GitHub Archive chưa làm → kết luận về giả thuyết dẫn trước có sức mạnh thống kê thấp. Muốn mạnh hơn: đặt `SE_API_KEY` để hoàn tất 68 tag, thêm GitHub Archive (Spark, lấy mẫu theo giờ).
4. **Dự báo giá trị chưa vượt baseline** `naive_last`; chỉ dự báo hướng được kiểm chứng, và mô hình hướng chỉ đọc đà gần đây của chính kỹ năng (không biết nguyên nhân). Điểm macro-F1 0,47 là mức trung bình, nên dùng để tham khảo chứ không phải lời hứa.
5. **Quy tắc đủ điều kiện ≥ 1% (2015–2022)** loại các kỹ năng mới nổi (LLM, Generative AI, RAG…) khỏi nhãn dù chúng có thể quan trọng nhất hiện nay; dashboard vẫn hiện lịch sử của các kỹ năng này nhưng không có dự báo được kiểm chứng.
6. **Cụm công nghệ yếu** (silhouette 0,149) và Skill Navigator là phép đếm mô tả trên tin quá khứ.
7. **Phân tích "vì sao tăng/giảm"** chỉ mô tả sự thay đổi đến từ đâu, không chứng minh nhân quả; hiện đang ẩn khỏi giao diện.
8. **Dữ liệu `archive*.zip`** ở thư mục gốc thuộc pipeline cũ, không được Skill Radar sử dụng (không đưa lên git).
9. Một số tháng 2015 của HN bị thiếu nên mô hình chỉ dùng từ 2015Q3.
10. **Việc còn lại (chưa làm):** mô hình chủ đề (NMF) và dự báo theo nhóm kỹ năng; hoàn tất Stack Overflow; chụp ảnh màn hình đưa vào báo cáo.
