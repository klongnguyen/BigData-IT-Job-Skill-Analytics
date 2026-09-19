# Research Questions (RQ1 – RQ6): Big Data IT Job Skill Analytics & Forecasting

Tài liệu này chuẩn hóa 6 câu hỏi nghiên cứu (Research Questions) theo định hướng chính thức của [FINAL_PLAN_BigData_IT_Job_Market_Skill_Forecasting.md](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/FINAL_PLAN_BigData_IT_Job_Market_Skill_Forecasting.md). 

> [!IMPORTANT]
> **Nguyên tắc cốt lõi của dự án**: Dự báo xu hướng kỹ năng **phải được thực hiện theo từng nhóm nghề (Occupation-Based)**, không dự báo chung toàn ngành CNTT khi dùng cho tư vấn nghề nghiệp. Forecast dựa trên bộ ba: `(Occupation + Skill + Time)`.

---

## RQ1: Những vị trí CNTT nào đang có nhu cầu tuyển dụng cao trên thị trường quốc tế?
- **Mục tiêu**: Đo lường tỷ trọng và sự tăng trưởng nhu cầu tuyển dụng giữa 8 nhóm nghề CNTT cốt lõi trên thị trường quốc tế qua các năm (2022–2026).
- **Công thức**:
  $$P(O_i, T) = \frac{\text{Số tin của } O_i \text{ trong } T}{\text{Tổng số tin trong } T} \times 100\%$$
- **Đầu ra**: Biểu đồ phân bổ tỷ trọng và tốc độ tăng trưởng (YoY / QoQ) của 8 vị trí CNTT.

---

## RQ2: Những kỹ năng nào được yêu cầu nhiều nhất đối với từng nhóm nghề CNTT?
- **Mục tiêu**: Xác định bộ kỹ năng cốt lõi (Core Skills) và mức độ xuất hiện cho từng nghề (ví dụ: Frontend Developer cần React, TypeScript; Data Engineer cần SQL, Spark, AWS).
- **Công thức (Demand Rate theo Occupation)**:
  $$\text{Demand Rate}(S_j \mid O_i, T) = \frac{\text{Số JD thuộc } O_i \text{ có chứa } S_j \text{ trong } T}{\text{Tổng số JD thuộc } O_i \text{ trong } T} \times 100\%$$
- **Đầu ra**: Bảng xếp hạng Top kỹ năng theo từng nghề và ma trận kỹ năng kết hợp (Co-occurrence).

---

## RQ3: Nhu cầu kỹ năng thay đổi như thế nào theo thời gian trong từng occupation?
- **Mục tiêu**: Theo dõi chuỗi thời gian biến thiên nhu cầu của từng kỹ năng theo tháng/quý bên trong từng vị trí công việc cụ thể.
- **Công thức**: Chuỗi thời gian $\text{Demand Rate}(S_j \mid O_i, t)$ qua các mốc thời gian $t \in \{2022, \dots, 2026\}$.
- **Đầu ra**: Biểu đồ Time-series xu hướng kỹ năng theo từng occupation.

---

## RQ4: Những kỹ năng nào đang Growing, Stable, Declining trong từng nhóm nghề?
- **Mục tiêu**: Phân loại trạng thái xu hướng của từng kỹ năng theo từng vị trí (ví dụ: TypeScript là *Growing* với Frontend Developer; Kafka là *Growing* với Backend Developer; Angular là *Declining* với Frontend Developer).
- **Công thức**: Dựa trên tốc độ tăng trưởng và hệ số góc hồi quy xu hướng $\beta$:
  - $\beta > \theta_{up}$: **Growing**
  - $-\theta_{down} \le \beta \le \theta_{up}$: **Stable**
  - $\beta < -\theta_{down}$: **Declining**
- **Đầu ra**: Bảng phân loại xu hướng kỹ năng chi tiết theo từng Occupation.

---

## RQ5: Dữ liệu tuyển dụng mới (Recent Data) có làm thay đổi xu hướng so với dữ liệu lịch sử hay không?
- **Mục tiêu**: Kiểm tra hiện tượng dịch chuyển công nghệ (**Concept Drift**) giữa giai đoạn lịch sử (2022–2024) và giai đoạn gần đây (2025–2026) (ví dụ: sự bùng nổ đột biến của Generative AI, LLM, RAG trong các tin tuyển dụng mới).
- **Phương pháp**: So sánh phân bố xác suất và kiểm định thống kê Kolmogorov-Smirnov / PSI giữa tập Historical và tập Recent.
- **Đầu ra**: Báo cáo phân tích Concept Drift trên các kỹ năng công nghệ mới.

---

## RQ6: Việc kết hợp Historical Data với Recent Data và Recency Weighting có cải thiện khả năng dự báo xu hướng kỹ năng hay không?
- **Mục tiêu**: Chứng minh giá trị thực nghiệm của mô hình kết hợp (Hybrid Model) so với các mô hình đơn lẻ.
- **3 Mô hình thực nghiệm**:
  1. **Model A (Historical Only)**: Huấn luyện trên dữ liệu lịch sử (2022–2024).
  2. **Model B (Recent Only)**: Huấn luyện trên dữ liệu gần đây (2025–2026).
  3. **Model C (Hybrid + Recency Weighting)**: Huấn luyện trên toàn bộ dữ liệu kèm hệ số suy giảm thời gian $w_i = e^{-\lambda \cdot age}$.
- **Tiêu chí đánh giá**: So sánh Accuracy, Precision, Recall, F1-Score và sai số dự báo trên tập kiểm thử thời gian (Test set 2026 Q3).
