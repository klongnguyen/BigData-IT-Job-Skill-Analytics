# Skill Radar — Báo cáo toàn bộ dự án

> Phân tích thị trường tuyển dụng CNTT và dự báo nhu cầu kỹ năng từ dữ liệu lớn.
> Mọi số liệu dưới đây lấy trực tiếp từ các tệp trong `skill_radar/data/` (manifest tạo lúc 2026-11-12 07:30 UTC) và mã nguồn trong `skill_radar/`.

---

## 1. Tổng quan

**Câu hỏi nghiên cứu:** hoạt động cộng đồng lập trình viên (Stack Overflow, npm, GitHub) có *đi trước* nhu cầu tuyển dụng một kỹ năng không, và có giúp *dự báo* nhu cầu đó không?

**Biến mục tiêu (nhu cầu):** tỷ lệ tin tuyển dụng nhắc tới một kỹ năng, theo quý
`share = số tin có nhắc kỹ năng / tổng số tin trong quý`.

**Nguồn nhu cầu:** các chuỗi hằng tháng "Ask HN: Who is hiring?" trên Hacker News.

**Kết luận ngắn (chi tiết ở mục 7):**
- Dự báo **hướng** thay đổi sau 4 quý (Đang lên / Ổn định / Suy giảm) **vượt** baseline "luôn Ổn định" và đã được kiểm chứng trên holdout 2023–2026.
- Dự báo **giá trị tỷ lệ** **không vượt** baseline đơn giản "giữ nguyên quý cuối", nên chỉ nên coi là kịch bản.
- **Tín hiệu cộng đồng không làm dự báo tốt hơn**: thêm tín hiệu vào mô hình không giảm sai số có ý nghĩa thống kê, và quan hệ dẫn trước – trễ không có bằng chứng.

---

## 2. Cấu trúc thư mục

```
BigData_Job_Analy/
├── README.md                  # trỏ sang skill_radar/README.md
├── PROJECT_REPORT.md          # tệp này
├── requirements.txt           # numpy, scipy, scikit-learn, pandas, pyarrow, requests, streamlit, plotly, pytest
├── pytest.ini
├── archive*.zip               # dữ liệu cũ của pipeline trước (không dùng trong Skill Radar)
├── tests/test_skill_radar.py  # kiểm thử
└── skill_radar/
    ├── taxonomy.py            # danh mục 75 kỹ năng + luật nhận diện
    ├── ingest/                # thu thập (hn.py, npm.py, stackexchange.py)
    ├── process/hn_postings.py # Bronze -> Silver -> Gold nhu cầu
    ├── panel.py               # ghép nhu cầu + tín hiệu thành bảng quý
    ├── models.py              # các mô hình dự báo
    ├── backtest.py            # backtest rolling-origin
    ├── leadlag.py             # phân tích dẫn trước – trễ
    ├── pipeline.py            # chạy toàn bộ, xuất artifact
    ├── app.py                 # dashboard Streamlit
    └── data/
        ├── raw/               # Bronze: dữ liệu thô, không sửa (≈46 MB)
        ├── processed/         # Silver + Gold nhu cầu (≈60 MB)
        └── gold/              # kết quả cuối cho dashboard (≈88 KB)
```

Kiến trúc dữ liệu theo mô hình **Bronze → Silver → Gold**:

| Tầng | Vị trí | Nội dung |
| --- | --- | --- |
| Bronze | `data/raw/` | Phản hồi API nguyên bản, không chỉnh sửa |
| Silver | `data/processed/hn_postings.parquet`, `hn_posting_skills.parquet` | Một dòng/tin tuyển dụng đã làm sạch; một dòng/(tin, kỹ năng) |
| Gold (nhu cầu) | `data/processed/hn_demand_month|quarter.parquet` | Tỷ lệ nhu cầu theo kỹ năng và kỳ |
| Gold (kết quả) | `data/gold/radar_*.parquet`, `radar_manifest.json` | Dự báo, lịch sử, đánh giá để dashboard đọc |

---

## 3. Thu thập dữ liệu (`ingest/`)

### 3.1 Nhu cầu — Hacker News "Who is hiring?" (`ingest/hn.py`) — **hoàn tất**
- **API:** Algolia HN (`hn.algolia.com/api/v1`), không cần khóa.
- **Cách làm:** (1) `search_by_date` với tag `story,author_whoishiring`, phân trang 1000 kết quả, lọc tiêu đề khớp `^ask hn: who is hiring?`; (2) mỗi chuỗi gọi `items/{id}` một lần để lấy cả cây bình luận.
- **Bền bỉ:** thử lại tối đa 5 lần với back-off lũy thừa khi gặp 429/5xx; nghỉ 0,4 s giữa các yêu cầu; User-Agent định danh là client học thuật.
- **Cache:** mỗi chuỗi lưu `data/raw/hn/{id}.json.gz` (nén gzip) và danh sách `threads.json`; chạy lại không tải lần hai.
- **Quy mô:** **185 chuỗi** (từ 04/2011), 186 tệp trong thư mục (185 chuỗi + `threads.json`).

### 3.2 Tín hiệu — npm (`ingest/npm.py`) — **hoàn tất**
- **API:** `api.npmjs.org/downloads/range` (API giới hạn ~18 tháng/lần nên chia cửa sổ 500 ngày).
- **Phạm vi:** 11 gói tương ứng 11 kỹ năng: `typescript`, `react`, `@angular/core`, `vue`, `jquery`, `svelte`, `next`, `graphql`, `tailwindcss`, `langchain`, `react-native`.
- **Xử lý:** cộng lượt tải theo tháng, **chỉ giữ tháng đủ ngày** (bỏ tháng đầu dở dang và tháng hiện tại). Mỗi gói lưu riêng ở `parts/` để có thể tiếp tục khi lỗi.
- **Kết quả:** `data/raw/npm/monthly_downloads.csv`, mỗi gói **141 tháng** (2015-02 → 2026-10).

### 3.3 Tín hiệu — Stack Overflow (`ingest/stackexchange.py`) — **chạy dở**
- **API:** Stack Exchange 2.3 `/questions` với `filter=total`, đếm số câu hỏi theo (tag, quý) từ 2011Q1.
- **Hạn mức:** 300 lượt/ngày nếu không có khóa; đặt biến môi trường `SE_API_KEY` để có 10.000 lượt/ngày (khóa chỉ đọc từ môi trường, không ghi ra đĩa). Chạy **tiếp nối được** (ghi nối vào CSV, mỗi lần tiếp tục chỗ dừng), thứ tự theo từng tag.
- **Hiện có (280 dòng):** tổng số câu hỏi (`__all__`, 63 quý), `javascript`, `python`, `typescript` (đủ 63 quý, 2011Q1–2026Q3) và `java` (mới 28 quý, 2011Q1–2017Q4 — chưa đủ để dùng).
- **Hệ quả:** chỉ **3 kỹ năng** (Python, JavaScript, TypeScript) có tín hiệu Stack Overflow dùng được.

### 3.4 Tín hiệu — GitHub Archive — **chưa làm**
`panel.py` đã có hàm `gh_signal()` đọc `data/raw/gharchive/language_share_month.csv`, nhưng tệp chưa tồn tại nên số kỹ năng có tín hiệu `gh_share` = 0.

| Nguồn | Vai trò | Trạng thái | Kỹ năng có tín hiệu |
| --- | --- | --- | --- |
| Hacker News | Mục tiêu (nhu cầu) | Xong | 75 (tất cả) |
| npm | Tín hiệu | Xong | 11 |
| Stack Overflow | Tín hiệu | Dở dang | 4 (3 dùng được trong lead-lag) |
| GitHub Archive | Tín hiệu | Chưa làm | 0 |

---

## 4. Xử lý dữ liệu

### 4.1 Danh mục kỹ năng (`taxonomy.py`)
- **75 kỹ năng**, chia 8 nhóm: ngôn ngữ (20), front-end (9), back-end (8), dữ liệu (12), AI/ML (10), cloud/DevOps (11), mobile (4), khác (1).
- Mỗi kỹ năng có: `aliases` (cách viết trong văn bản), `category`, và ánh xạ tín hiệu (`se_tag`, `npm`, `gh`).
- **Cú pháp alias:** chuỗi thường → khớp token nguyên, không phân biệt hoa/thường (không dính ký tự `\w . # +` hai bên); `re:` → regex không phân biệt hoa/thường; `cs:` → regex **phân biệt hoa/thường** cho các từ trùng tiếng Anh thường (ví dụ "Go", "Swift", "iOS", "RAG").
- Ví dụ xử lý nhập nhằng: "Go" chỉ tính khi viết hoa và không đi sau/trước các từ như *to, for, with, team, market…*; "React" không tính khi là "React Native" (kỹ năng riêng); "Java" không bị lẫn với "JavaScript".

### 4.2 Bronze → Silver (`process/hn_postings.py`)
Quy tắc ảnh hưởng đến thống kê:
1. Chỉ **bình luận cấp cao nhất** là tin tuyển dụng (trả lời là thảo luận, bị loại).
2. Kỳ lấy theo **tháng ghi trong tiêu đề chuỗi** (`(November 2026)`), không theo ngày tạo (chuỗi thường được tạo sớm 1–2 ngày). Nếu không đọc được tiêu đề thì dùng ngày tạo.
3. Tháng có hai chuỗi được gộp và khử trùng theo `comment_id`.
4. Làm sạch HTML: bỏ thẻ **trước**, giải mã entity (`&#x2F;`…) **sau**, chuẩn hóa khoảng trắng.
5. Bỏ tin dưới **50 ký tự**; mọi tin bị loại đều được đếm và báo cáo.
6. Gắn kỹ năng bằng các mẫu regex đã biên dịch.

**Báo cáo xử lý (`hn_report.json`):**

| Chỉ số | Giá trị |
| --- | --- |
| Số chuỗi | 185 |
| Số tháng | 185 (04/2011 → 11/2026) |
| Số quý | 63 |
| **Tin tuyển dụng giữ lại** | **93.354** |
| Bị loại: rỗng/đã xóa | 2 |
| Bị loại: quá ngắn (<50 ký tự) | 208 |
| Bị loại: trùng id | 0 |
| Tin nhắc ≥ 1 kỹ năng | 71.571 (≈76,7%) |
| Cặp (tin, kỹ năng) | 285.733 |

### 4.3 Gold nhu cầu
`demand_panel()` tính cho mỗi (kỳ, kỹ năng): `posts_with_skill`, `total_posts`, `n_months`, `share = posts_with_skill / total_posts`, lưới đầy đủ 75 kỹ năng × mọi kỳ (kỹ năng không xuất hiện = 0).

| Tệp | Số dòng | Cột |
| --- | --- | --- |
| `hn_postings.parquet` | 93.354 | thread_id, month, quarter, comment_id, author, created_at, text |
| `hn_posting_skills.parquet` | 285.733 | comment_id, skill |
| `hn_demand_month.parquet` | 13.875 | period, skill, posts_with_skill, total_posts, n_months, share |
| `hn_demand_quarter.parquet` | 4.725 | (như trên, theo quý) |

### 4.4 Bảng quý để mô hình hóa (`panel.py`)
- Loại **tháng đang diễn ra** (chỉ giữ tới tháng trọn vẹn gần nhất) và quý có **< 2 tháng** dữ liệu (`MIN_MONTHS = 2`).
- Tín hiệu ghép bằng `left join`, thiếu vẫn là `NaN`, **không điền bù**:
  - `se_share` = câu hỏi của tag / tổng câu hỏi trong quý;
  - `npm_dl` = tổng lượt tải của quý (chỉ quý đủ 3 tháng);
  - `gh_share` = tỷ lệ pull request theo ngôn ngữ (chưa có dữ liệu).
- **Chuỗi mô hình:** từ **2015Q3** (sau các tháng HN bị thiếu năm 2015) tới **2026Q3** = **45 quý liên tục**, không khoảng trống (`to_panel` báo lỗi nếu có khoảng trống). Tổng **79.180 tin** trong khoảng này.
- Số tin mỗi quý: 2015Q3 = 2.315, …, 2025Q3 = 929, 2025Q4 = 1.104, 2026Q1 = 974, 2026Q2 = 945, 2026Q3 = 722. Số tin/quý đã giảm so với giai đoạn đầu, nên tỷ lệ của kỹ năng hiếm dao động mạnh.

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

**Tham số chọn trên cửa sổ chọn:**

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
| **gbm** | 0,7640 | **0,5989** (mô hình hướng) |

---

## 7. Kết quả

### 7.1 Holdout 2023Q1–2026Q3 — sai số giá trị (53 kỹ năng, 54 ô origin×horizon)

Baseline tốt nhất: `naive_last`. Chênh lệch dương = tệ hơn baseline.

| Mô hình | MAE (điểm %) | h=1 | h=2 | h=3 | h=4 | Chênh vs baseline [KTC 95%] |
| --- | --- | --- | --- | --- | --- | --- |
| naive_last | **0,7746** | 0,669 | 0,741 | 0,817 | 0,899 | — |
| mean4 | 0,8421 | 0,691 | 0,801 | 0,906 | 1,010 | +0,067 [0,034; 0,109] tệ hơn |
| **ses** | **0,7514** | 0,635 | 0,716 | 0,796 | 0,889 | −0,023 [−0,031; −0,015] **tốt hơn** |
| damped | 0,7995 | 0,668 | 0,762 | 0,853 | 0,950 | +0,025 [−0,006; 0,059] không khác biệt |
| ridge | 0,8109 | 0,637 | 0,743 | 0,883 | 1,030 | +0,036 [0,004; 0,071] tệ hơn |
| gbm | 0,7679 | 0,623 | 0,711 | 0,837 | 0,940 | −0,007 [−0,041; 0,029] không khác biệt |
| ridge+signals | 0,8089 | 0,637 | 0,738 | 0,880 | 1,030 | +0,034 [0,002; 0,069] tệ hơn |
| gbm+signals | 0,7656 | 0,622 | 0,711 | 0,831 | 0,938 | −0,009 [−0,043; 0,028] không khác biệt |

**Diễn giải:** mô hình sản xuất cho giá trị là `damped` (chọn trên cửa sổ chọn) **không vượt** `naive_last` trên holdout (KTC chứa 0). Chỉ `ses` thắng baseline có ý nghĩa, nhưng chênh lệch chỉ ≈ 0,02 điểm %. Giữ nguyên quý cuối là baseline rất khó thắng với chuỗi này. Vì vậy dashboard ghi *"Chưa kiểm chứng"* cho giá trị dự báo và coi là kịch bản.

### 7.2 Tín hiệu cộng đồng có giúp dự báo không? (hiệu ứng cùng lớp mô hình)

| So sánh | Toàn bộ 53 kỹ năng | 10 kỹ năng có tín hiệu |
| --- | --- | --- |
| ridge+signals − ridge | −0,002 điểm % [−0,007; 0,004] | +0,019 [−0,006; 0,045] |
| gbm+signals − gbm | −0,002 điểm % [−0,006; 0,003] | +0,002 [−0,016; 0,026] |

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
| **gbm** (mô hình hướng) | 0,4651 | **0,4662** | 0,3834 |
| ridge+signals | 0,4659 | 0,4648 | 0,4383 |
| gbm+signals | 0,4579 | 0,4420 | 0,4182 |

**Kiểm chứng mô hình hướng (`gbm`, bootstrap cụm theo kỹ năng):** macro-F1 = **0,4662** so với **0,2636** của "luôn Stable"; **mức tăng +0,2026, KTC 95% [0,1464; 0,2537] → `validated = true`**. Lưu ý: ở ngưỡng 0,5 và 1,0, `naive_last` còn nhỉnh hơn `gbm` trên holdout; mô hình hướng được chọn *trước* trên cửa sổ chọn nên báo cáo nguyên trạng, không chọn lại.

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

**GitHub:** không có dữ liệu.

**Diễn giải:** với npm mọi KTC chứa 0 và placebo p > 0,15 → không có tín hiệu dẫn trước. Với Stack Overflow, tương quan **âm** nhẹ ở độ trễ dài, nhưng chỉ dựa trên 3 kỹ năng (không đủ để kết luận; 2 độ trễ có placebo p = 0 song mẫu quá nhỏ) và sự giảm của câu hỏi Stack Overflow phản ánh xu hướng chung của nền tảng hơn là nhu cầu tuyển dụng. Kết luận trung thực: **chưa có bằng chứng cho giả thuyết nghiên cứu**.

### 7.6 Đầu ra radar: nhãn cho 53 kỹ năng đủ điều kiện
Phân bố nhãn: **Stable 48 · Fading 3 · Rising 2** (22 kỹ năng còn lại: "Chưa đủ bằng chứng").

Top kỹ năng theo tỷ lệ năm qua (dự báo 4 quý; thay đổi tính bằng điểm %):

| Kỹ năng | Nhóm | Tỷ lệ năm qua | Dự báo 4 quý | Thay đổi | Nhãn |
| --- | --- | --- | --- | --- | --- |
| Python | ngôn ngữ | 25,1% | 27,0% | +1,82 | **Rising** |
| TypeScript | ngôn ngữ | 23,8% | 24,6% | −1,11 | **Fading** |
| React | front-end | 22,7% | 23,0% | −1,77 | **Fading** |
| PostgreSQL | dữ liệu | 18,4% | 19,8% | +1,49 | **Rising** |
| AWS | cloud | 15,6% | 15,8% | −0,29 | Stable |
| Machine Learning | AI | 14,9% | 14,9% | −0,67 | Stable |
| Kubernetes | cloud | 9,3% | 9,7% | +0,14 | Stable |
| Rust | ngôn ngữ | 8,4% | 9,3% | +0,53 | Stable |
| Go | ngôn ngữ | 7,3% | 7,0% | −1,21 | **Fading** |
| Node.js | back-end | 7,0% | 7,7% | +0,23 | Stable |
| Docker | cloud | 6,2% | 7,1% | +0,87 | Stable |
| Terraform | cloud | 5,8% | 6,1% | −0,15 | Stable |

Quan sát: Python, PostgreSQL đang lên; TypeScript, React, Go đang suy giảm; phần còn lại ổn định. Kỹ năng AI mới nổi (LLM, GenAI, LangChain, RAG) chưa đạt ngưỡng 1% trong cửa sổ chọn (2015–2022) nên bị xếp "Chưa đủ bằng chứng" thay vì được gán nhãn — đây là hệ quả của quy tắc đặt trước, cần lưu ý khi diễn giải.

Dự báo sản xuất cho các quý **2026Q4, 2027Q1, 2027Q2, 2027Q3** (4 quý × 75 kỹ năng = 300 dòng) kèm khoảng 80%.

---

## 8. Sản phẩm đầu ra

| Tệp (`skill_radar/data/gold/`) | Nội dung |
| --- | --- |
| `radar_series.parquet` | 75 dòng: mỗi kỹ năng — tỷ lệ năm qua / quý cuối, dự báo 4 quý, thay đổi (điểm %), nhãn hướng, mức bằng chứng (`validated` / `insufficient`), đỉnh lịch sử, số tin năm qua |
| `radar_paths.parquet` | 300 dòng: đường dự báo h=1..4 với `forecast`, `lo`, `hi` |
| `radar_history.parquet` | 3.375 dòng (75 kỹ năng × 45 quý): `share`, `posts`, `total` |
| `radar_manifest.json` | Bằng chứng, giao thức, kết quả backtest đầy đủ, mô hình được chọn, kiểm chứng hướng, phân vị khoảng, lead-lag |

**Mô hình sản xuất:** giá trị = `damped` (φ = 0,25); hướng = `gbm`.

### Dashboard Streamlit (`app.py`)
Chạy: `python -m streamlit run skill_radar/app.py --server.port 8502` → http://localhost:8502. Giao diện tiếng Việt, 3 trang:
1. **Radar** — số kỹ năng Đang lên / Ổn định / Suy giảm, biểu đồ Plotly, bảng xếp hạng theo tỷ lệ năm qua (có nút tải CSV), thanh trạng thái "Đã kiểm chứng" / "Chưa kiểm chứng".
2. **Lịch sử & dự báo** — biểu đồ Plotly lịch sử tỷ lệ + đường dự báo và dải 80%.
3. **Độ tin cậy** — so sánh mô hình, hiệu ứng tín hiệu, kết quả dẫn trước – trễ.

---

## 9. Kiểm thử (`tests/test_skill_radar.py`)
Chạy `python -m pytest -q tests/test_skill_radar.py`. Phủ: luật nhận diện kỹ năng; bỏ thẻ HTML trước khi giải mã entity; taxonomy hợp lệ; kỳ lấy từ tiêu đề; mẫu số của tỷ lệ là toàn bộ tin; `to_panel` từ chối khoảng trống; **không mô hình nào nhìn thấy quý sau mốc dự báo**; mô hình gộp trả NaN khi lịch sử ngắn; `damped` khớp đường thẳng đã biết; ô chọn mô hình không chạm holdout; tính đủ điều kiện không dùng holdout; ranh giới nhãn; backtest chạy end-to-end và **tái lập được**.
*(Báo cáo này chưa chạy lại bộ test; kết quả test chưa được xác minh trong phiên làm báo cáo.)*

---

## 10. Cách chạy lại toàn bộ

```powershell
pip install -r requirements.txt
python -m skill_radar.ingest.hn            # tải 185 chuỗi (có cache)
python -m skill_radar.ingest.npm
python -m skill_radar.ingest.stackexchange # đặt SE_API_KEY để chạy đủ trong 1 ngày
python -m skill_radar.process.hn_postings  # Bronze -> Silver -> Gold nhu cầu
python -m skill_radar.pipeline             # backtest + lead-lag + dự báo + artifact
python -m streamlit run skill_radar/app.py --server.port 8502
python -m pytest -q tests/test_skill_radar.py
```

---

## 11. Hạn chế và việc còn lại

1. **Một nguồn nhu cầu duy nhất** (Hacker News): thiên lệch về startup/công nghệ, không đại diện toàn thị trường tuyển dụng; số tin/quý giảm theo thời gian (còn ~700–1.100 tin/quý gần đây).
2. **Nhận diện kỹ năng bằng từ khóa/regex**: có thể sót hoặc nhầm các từ nhập nhằng dù đã có luật; chưa có đo độ chính xác với nhãn người gán.
3. **Tín hiệu mỏng:** Stack Overflow mới 3 kỹ năng dùng được (tag `java` dở dang), GitHub Archive chưa làm → kết luận về giả thuyết dẫn trước có sức mạnh thống kê thấp. Muốn mạnh hơn: đặt `SE_API_KEY` để hoàn tất 68 tag, thêm GitHub Archive (Spark, lấy mẫu theo giờ).
4. **Dự báo giá trị chưa vượt baseline** `naive_last`; chỉ dự báo hướng được kiểm chứng.
5. **Quy tắc đủ điều kiện ≥ 1% (2015–2022)** loại các kỹ năng mới nổi (LLM, GenAI, RAG…) khỏi nhãn dù chúng có thể quan trọng nhất hiện nay.
6. **Dữ liệu `archive*.zip`** ở thư mục gốc thuộc pipeline cũ, không được Skill Radar sử dụng.
7. Một số tháng 2015 của HN bị thiếu nên mô hình chỉ dùng từ 2015Q3.
