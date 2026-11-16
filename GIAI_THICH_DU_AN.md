# Giải thích dự án Skill Radar (bản dễ hiểu)

> Đề tài: **Dự đoán xu hướng kỹ năng nghề nghiệp ngành Công nghệ thông tin**.
> Dự án có đúng với đề tài. Mã nguồn nằm trong `skill_radar/`. Số liệu chi tiết xem [PROJECT_REPORT.md](PROJECT_REPORT.md).

---

## 1. Mục tiêu

Dự án trả lời hai việc:

1. **Kỹ năng nào đang được tuyển nhiều hơn hay ít hơn?** Ví dụ Python đang lên, React đang giảm. Đây là phần "xu hướng".
2. **Một năm nữa mỗi kỹ năng sẽ ra sao?** Đây là phần "dự đoán".

Ngoài ra có một câu hỏi phụ để đề tài có chiều sâu nghiên cứu: *lượng người bàn về, tải hoặc dùng một công nghệ (Stack Overflow, npm) có tăng trước khi công ty tuyển nhiều hơn không?* Nếu có, có thể dùng nó để dự đoán sớm hơn.
Kết quả: **chưa thấy bằng chứng** cho điều này.

---

## 2. Thu thập dữ liệu

### 2.1 Nhu cầu tuyển dụng (dữ liệu chính)
- **Nguồn:** Hacker News. Mỗi tháng có một bài "Ask HN: Who is hiring?", nơi các công ty tự đăng tin tuyển dụng dưới dạng bình luận.
- **Cách lấy:** gọi API công khai của Algolia, tải 185 bài (từ 04/2011 đến nay), mỗi bài tải cả cây bình luận.
- **Lưu trữ:** dữ liệu thô lưu nguyên bản dạng nén, không sửa gì, để có thể xử lý lại bất cứ lúc nào.
- **Độ bền:** tự thử lại khi lỗi mạng, có cache nên chạy lại không tải lần hai.

### 2.2 Tín hiệu cộng đồng (dữ liệu phụ, để kiểm tra "có đi trước không")

| Nguồn | Nội dung | Trạng thái |
| --- | --- | --- |
| npm | Số lượt tải hằng tháng của 11 thư viện (React, Vue, TypeScript…) | Xong |
| Stack Overflow | Số câu hỏi theo từng thẻ công nghệ mỗi quý | Chạy dở: API giới hạn 300 lượt/ngày, mới có Python, JavaScript, TypeScript |
| GitHub | Hoạt động theo ngôn ngữ | Chưa làm |

---

## 3. Xử lý dữ liệu

Có 93.354 tin tuyển dụng là văn bản lộn xộn, cần biến thành con số "kỹ năng X chiếm bao nhiêu % tin tuyển dụng".

1. **Chỉ lấy tin tuyển dụng thật.** Chỉ bình luận cấp cao nhất là tin tuyển dụng. Bình luận trả lời là thảo luận nên bỏ.
2. **Làm sạch văn bản.** Bỏ thẻ HTML, giải mã ký tự đặc biệt. Bỏ tin rỗng hoặc dưới 50 ký tự (210 tin bị bỏ, đều được đếm lại).
3. **Xác định tháng đúng.** Lấy tháng ghi trong tiêu đề bài (ví dụ "November 2026"), không lấy ngày đăng, vì bài thường đăng sớm 1–2 ngày.
4. **Nhận diện kỹ năng bằng danh sách luật.** Danh mục gồm 75 kỹ năng, mỗi kỹ năng có nhiều cách viết (ví dụ "k8s" tính là Kubernetes). Tin nào có chữ khớp thì gắn kỹ năng đó. Phần này khó nhất vì có từ trùng nghĩa thường:
   - "Go" chỉ tính khi viết hoa và không nằm trong cụm như "go to".
   - "Java" không bị lẫn với "JavaScript".
   - "React Native" tách riêng khỏi "React".

   Kết quả: 285.733 cặp (tin, kỹ năng).
5. **Tính tỷ lệ theo quý.** `tỷ lệ = số tin nhắc kỹ năng / tổng số tin trong quý`. Dùng tỷ lệ thay vì số tin tuyệt đối vì số tin mỗi quý thay đổi nhiều. Chuỗi dùng để huấn luyện chạy từ 2015Q3 đến 2026Q3, tức 45 quý liên tục.

---

## 4. Dự đoán và kiểm tra

- Thử nhiều mô hình, từ đơn giản (giữ nguyên quý cuối) đến máy học (Ridge, Gradient Boosting), có và không có tín hiệu cộng đồng.
- Để tránh "ăn gian": dữ liệu tới hết 2022 dùng để chọn mô hình. Giai đoạn 2023–2026 chỉ dùng để chấm điểm một lần.

---

## 5. Kết quả

- Dự đoán **hướng** (lên, giảm hay ổn định sau 1 năm) tốt hơn hẳn việc đoán bừa "ổn định": macro-F1 là 0,47 so với 0,26.
- Dự đoán **con số chính xác** không hơn cách đơn giản "giữ nguyên quý cuối". Báo cáo nói rõ điều này.
- Python và PostgreSQL đang lên; TypeScript, React và Go đang giảm.
- Tín hiệu cộng đồng không làm dự đoán tốt hơn, và chưa thấy bằng chứng rằng chúng đi trước nhu cầu tuyển dụng.

---

## 6. Hạn chế

- Chỉ có một nguồn tuyển dụng là Hacker News, nghiêng về startup và công nghệ, nên không đại diện cho cả thị trường (đặc biệt không đại diện cho Việt Nam).
- Tín hiệu cộng đồng còn mỏng (Stack Overflow chưa xong, GitHub chưa có).
- Việc nhận diện kỹ năng bằng từ khóa chưa được đo độ chính xác so với người gán nhãn.
- Các kỹ năng AI mới (LLM, GenAI, RAG) chưa đạt ngưỡng 1% trong giai đoạn chọn mô hình (2015–2022), nên bị xếp "Chưa đủ bằng chứng".
