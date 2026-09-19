# Research Questions (RQ1 – RQ5): Big Data IT Job Skill Analytics

Hệ thống đặt ra 5 câu hỏi nghiên cứu trọng tâm, mỗi câu hỏi đều có thể đo lường và trả lời trực tiếp từ dữ liệu tuyển dụng đã xử lý.

---

## RQ1: Nhu cầu tuyển dụng phân bố như thế nào giữa các nhóm vị trí CNTT?

### 1. Mục tiêu
Xác định mức độ quan tâm của thị trường lao động đối với từng vai trò CNTT và sự thay đổi tỷ trọng giữa các vị trí qua các năm (2020–2026).

### 2. Phương pháp & Công thức đo lường
- **Tỷ trọng tuyển dụng của vị trí $O_i$ trong khoảng thời gian $T$**:
  $$P(O_i, T) = \frac{\text{Số lượng tin tuyển dụng của } O_i \text{ trong } T}{\text{Tổng số lượng tin tuyển dụng trong } T} \times 100\%$$
- **Tốc độ tăng trưởng tuyển dụng (YoY / QoQ)**:
  $$Growth(O_i, T_1 \to T_2) = \frac{N(O_i, T_2) - N(O_i, T_1)}{N(O_i, T_1)} \times 100\%$$

### 3. Đầu vào & Đầu ra
- **Đầu vào**: `normalized_title`, `posted_at`.
- **Đầu ra**: Bảng phân bố tỷ lệ %, biểu đồ biến động tỷ trọng 8 nhóm nghề theo quý/năm.

---

## RQ2: Các kỹ năng cốt lõi và kỹ năng kết hợp (Skill Co-occurrence) nào là quan trọng nhất cho từng vị trí CNTT?

### 1. Mục tiêu
Xác định danh mục kỹ năng không thể thiếu (Core Skills) và các cặp kỹ năng thường xuyên xuất hiện cùng nhau (Complementary Skills) cho mỗi nghề nghiệp (ví dụ: Data Engineer cần SQL + Spark + AWS).

### 2. Phương pháp & Công thức đo lường
- **Tần suất xuất hiện kỹ năng $S_j$ trong vai trò $O_i$**:
  $$\text{Frequency}(S_j \mid O_i) = \frac{\text{Số JD thuộc } O_i \text{ có chứa } S_j}{\text{Tổng số JD thuộc } O_i} \times 100\%$$
- **Hệ số đồng xuất hiện (Co-occurrence / Jaccard Similarity)** giữa 2 kỹ năng $S_a$ và $S_b$:
  $$J(S_a, S_b \mid O_i) = \frac{|JD(S_a \cap S_b \mid O_i)|}{|JD(S_a \cup S_b \mid O_i)|}$$

### 3. Đầu vào & Đầu ra
- **Đầu vào**: `normalized_title`, `skills`.
- **Đầu ra**: Top 10 kỹ năng phổ biến nhất theo từng occupation; Ma trận đồng xuất hiện (Skill Co-occurrence Matrix) / Skill Network Graph.

---

## RQ3: Nhu cầu về các kỹ năng công nghệ biến động như thế nào theo thời gian (2020–2026)?

### 1. Mục tiêu
Theo dõi sự dịch chuyển công nghệ và phân loại kỹ năng thành 3 nhóm xu hướng:
- **Growing**: Đang tăng trưởng mạnh mẽ (ví dụ: GenAI, LLM, RAG, Rust).
- **Stable**: Ổn định, bền vững theo thời gian (ví dụ: SQL, Python, Git, Docker).
- **Declining**: Đang có xu hướng suy giảm hoặc bị thay thế.

### 2. Phương pháp & Công thức đo lường
- **Tỷ lệ xuất hiện của kỹ năng $S_j$ tại mốc thời gian $t$**:
  $$R(S_j, t) = \frac{N(S_j, t)}{Total\_Jobs(t)}$$
- **Hệ số góc xu hướng (Trend Slope $\beta$)**:
  Ước lượng qua hồi quy tuyến tính $R(S_j, t) = \alpha + \beta t + \epsilon$:
  - $\beta > \theta_{up}$: **Growing**
  - $-\theta_{down} \le \beta \le \theta_{up}$: **Stable**
  - $\beta < -\theta_{down}$: **Declining**

### 3. Đầu vào & Đầu ra
- **Đầu vào**: `skills`, `posted_at`, `normalized_title`.
- **Đầu ra**: Biểu đồ Time-series xu hướng kỹ năng, danh sách phân loại Growing/Stable/Declining.

---

## RQ4: Làm thế nào để xây dựng mô hình Machine Learning dự báo nhu cầu kỹ năng trong tương lai?

### 1. Mục tiêu
Dự báo nhu cầu kỹ năng trong 3–6 tháng hoặc 1 năm tới dựa trên chuỗi thời gian lịch sử kết hợp với các đặc trưng trễ (lagged features) và thuộc tính công việc.

### 2. Phương pháp & Mô hình
- **Time-series Forecasting**: ARIMA / Prophet / Holt-Winters cho xu hướng tổng thể của từng kỹ năng.
- **Supervised Machine Learning**: Random Forest Regressor / XGBoost / Spark ML GBTRegressor sử dụng:
  - Lag features: $R(S, t-1), R(S, t-2), R(S, t-3)$.
  - Rolling statistics: Rolling Mean, Rolling Std (3 tháng, 6 tháng).
  - Occupation dummy features.
- **Đánh giá**: Đo lường bằng RMSE, MAE, MAPE trên tập test thời gian (Time-based split: Train $\le 2024$, Validation $= 2025$, Test $= 2026$).

### 3. Đầu vào & Đầu ra
- **Đầu vào**: Chuỗi tỷ lệ nhu cầu kỹ năng theo tháng, các đặc trưng thống kê.
- **Đầu ra**: Tỷ lệ nhu cầu dự báo của từng kỹ năng trong các quý tiếp theo và khoảng tin cậy.

---

## RQ5: Việc kết hợp dữ liệu tuyển dụng mới (Fresh Data 2026) với dữ liệu lịch sử cải thiện độ chính xác dự báo ra sao so với các mô hình đơn lẻ?

### 1. Mục tiêu
Chứng minh giá trị thực tiễn của kiến trúc kết hợp (Hybrid Architecture) và kỹ thuật gán trọng số thời gian (Recency Weighting) trong việc thích ứng với biến động nhanh chóng của thị trường CNTT (Concept Drift).

### 2. Phương pháp so sánh
So sánh 3 chiến lược:
1. **Model A (Historical Only)**: Huấn luyện chỉ trên dữ liệu lịch sử (2020–2024), dự báo 2026.
2. **Model B (Fresh Only)**: Huấn luyện chỉ trên dữ liệu gần đây (cuối 2025–2026), dự báo 2026+.
3. **Model C (Hybrid with Recency Weighting)**: Huấn luyện trên toàn bộ dữ liệu lịch sử nhưng áp dụng hệ số suy giảm thời gian (Exponential Decay Weighting):
   $$w_i = e^{-\lambda (t_{current} - t_i)}$$

### 3. Tiêu chí đánh giá
- So sánh sai số dự báo: $\Delta \text{RMSE}, \Delta \text{MAE}, \Delta \text{MAPE}$.
- Đánh giá khả năng bắt kịp các kỹ năng mới nổi (ví dụ: các kỹ năng AI thế hệ mới xuất hiện đột biến trong 2024–2026).
