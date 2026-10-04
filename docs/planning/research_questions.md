# Research Questions (RQ1 – RQ6): Big Data IT Job Skill Analytics & Forecasting

Tài liệu này chuẩn hóa 6 câu hỏi nghiên cứu (Research Questions) theo định hướng chính thức của [FINAL_PLAN_BigData_IT_Job_Market_Skill_Forecasting.md](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/FINAL_PLAN_BigData_IT_Job_Market_Skill_Forecasting.md). 

> **Trạng thái đo lường:** Đây là các câu hỏi và mục tiêu nghiên cứu, chưa phải kết quả. Archive hiện có chỉ bao phủ năm 2023 và thiếu JD; snapshot fresh không tạo thành chuỗi liên tục. Các kỳ 2022–2026 trong công thức là phạm vi mục tiêu, chưa được dữ liệu hiện tại bảo đảm. Xem [Phase 01 audit](../data/phase01_data_audit.json) và [GO/NO-GO](go_no_go_report.md).

> [!IMPORTANT]
> **Nguyên tắc cốt lõi của dự án**: Dự báo xu hướng kỹ năng **phải được thực hiện theo từng nhóm nghề (Occupation-Based)**, không dự báo chung toàn ngành CNTT khi dùng cho tư vấn nghề nghiệp. Forecast dựa trên bộ ba: `(Occupation + Skill + Time)`.

---

## RQ1: Những vị trí CNTT nào đang có nhu cầu tuyển dụng cao trên thị trường quốc tế?
- **Mục tiêu**: Đo lường tỷ trọng nhu cầu tuyển dụng giữa 8 nhóm nghề CNTT cốt lõi trong những kỳ có dữ liệu nguồn đủ điều kiện.
- **Công thức**:
  $$P(O_i, T) = \frac{\text{Số tin của } O_i \text{ trong } T}{\text{Tổng số tin trong } T} \times 100\%$$
- **Đầu ra**: Biểu đồ phân bổ theo occupation và kỳ quan sát, luôn hiển thị nguồn, mẫu số và số tin.

---

## RQ2: Những kỹ năng nào được yêu cầu nhiều nhất đối với từng nhóm nghề CNTT?
- **Mục tiêu**: Xác định bộ kỹ năng cốt lõi (Core Skills) và mức độ xuất hiện cho từng nghề (ví dụ: Frontend Developer cần React, TypeScript; Data Engineer cần SQL, Spark, AWS).
- **Đơn vị phân tích**: Tin tuyển dụng duy nhất thuộc occupation, cùng kỳ quan sát và cùng phạm vi nguồn sau dedup. Archive lịch sử cung cấp `job_skills`/`source_tags`; không có JD để trích xuất. Với nguồn fresh có JD, skill extraction là một nhánh riêng. Không gộp hai loại bằng chứng vào cùng chuỗi nếu chưa chứng minh được tính so sánh.
- **Công thức (Demand Rate theo Occupation)**, với `R` là phạm vi nguồn cố định:
  $$\text{Demand Rate}(S_j \mid O_i, T, R) = \frac{\text{Số tin duy nhất } O_i \text{ trong } T,R \text{ có bằng chứng của } S_j}{\text{Tổng số tin duy nhất đủ điều kiện của } O_i \text{ trong cùng } T,R} \times 100\%$$
- **Coverage báo cáo riêng**: `skill_evidence_coverage = số tin đủ điều kiện có ít nhất một skill evidence / tổng số tin đủ điều kiện` trong cùng occupation, kỳ và phạm vi nguồn. Tin thiếu evidence vẫn nằm trong mẫu số Demand Rate; do đó phải hiển thị coverage để người đọc thấy giới hạn quan sát.
- **Đầu ra**: Bảng xếp hạng Top kỹ năng theo từng nghề và ma trận kỹ năng kết hợp (Co-occurrence), kèm mẫu số, loại bằng chứng kỹ năng, nguồn và coverage.

---

## RQ3: Nhu cầu kỹ năng thay đổi như thế nào theo thời gian trong từng occupation?
- **Mục tiêu**: Theo dõi chuỗi thời gian biến thiên nhu cầu của từng kỹ năng theo tháng/quý bên trong từng vị trí công việc cụ thể.
- **Công thức**: Chuỗi quan sát theo tháng $\text{Demand Rate}(S_j \mid O_i, t)$ cho các occupation-skill đủ support và các tháng thật có dữ liệu.
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
- **Mục tiêu**: Kiểm tra sự thay đổi xu hướng giữa dữ liệu lịch sử và mới khi các nguồn/kỳ có thể so sánh (ví dụ: biến động tỷ lệ xuất hiện GenAI/LLM/RAG).
- **Phương pháp**: So sánh demand rate, cơ cấu nguồn và khoảng bất định; chỉ kết luận drift khi sai khác nguồn và độ phủ đã được kiểm soát.
- **Đầu ra**: Báo cáo phân tích Concept Drift trên các kỹ năng công nghệ mới.

---

## RQ6: Việc kết hợp Historical Data với Recent Data và Recency Weighting có cải thiện khả năng dự báo xu hướng kỹ năng hay không?
- **Mục tiêu**: Đánh giá liệu mô hình kết hợp có cải thiện dự báo kỳ tiếp theo so với các baseline trên cùng future test hay không.
- **4 Mô hình thực nghiệm** (theo Final Plan):
  1. **Model A (Historical Only)**: Chỉ dữ liệu lịch sử đủ điều kiện tại từng cutoff rolling-origin.
  2. **Model B (Recent Only)**: Chỉ dữ liệu gần đây đủ điều kiện tại cùng cutoff.
  3. **Model C (Hybrid + Recency Weighting)**: Lịch sử + mới đủ điều kiện, với hệ số suy giảm thời gian $w_i = e^{-\lambda \cdot age}$.
  4. **Model D (Hybrid unweighted)**: Cùng dữ liệu lịch sử + mới, không dùng Recency Weighting.
- **Horizon và so sánh**: Dự báo kỳ tháng kế tiếp; các nhánh phải dùng cùng cutoff, kỳ test và quy tắc eligibility. Chưa chạy forecast khi cổng dữ liệu còn NO-GO.
- **Tiêu chí đánh giá**: Macro-F1, Balanced Accuracy, F1 theo lớp và baseline `Stable`/xu hướng gần nhất trên cùng tập test tương lai; không có chỉ số khi nhánh thiếu dữ liệu.
