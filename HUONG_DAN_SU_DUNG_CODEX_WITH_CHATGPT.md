# Hướng dẫn sử dụng Codex with ChatGPT hiệu quả

Tài liệu này hướng dẫn cách dùng skill `codex-with-chatgpt` trong Codex Extension của VS Code. Mô hình làm việc cốt lõi là:

- **ChatGPT** phân tích yêu cầu, đọc workspace, lập kế hoạch và review kết quả.
- **Codex** chỉnh sửa mã nguồn, chạy lệnh, kiểm thử và xử lý lỗi.
- ChatGPT chỉ có quyền **đọc** workspace; việc thay đổi file vẫn do Codex thực hiện.

## 1. Cách dùng nhanh nhất

Mở đúng thư mục dự án trong VS Code, sau đó gửi cho Codex một yêu cầu theo mẫu:

```text
Sử dụng Codex with ChatGPT để thực hiện yêu cầu sau:

Mục tiêu: <kết quả cần đạt>
Phạm vi: <thư mục hoặc chức năng liên quan>
Ràng buộc: <điều không được thay đổi>
Tiêu chí hoàn thành: <cách xác nhận đã xong>
Kiểm thử: <các test hoặc lệnh cần chạy>
```

Ví dụ:

```text
Sử dụng Codex with ChatGPT để bổ sung bước chuẩn hóa tên kỹ năng trong pipeline dữ liệu.

Mục tiêu: gộp các biến thể như "Py Spark", "pyspark" và "PySpark" thành một giá trị chuẩn.
Phạm vi: pipeline xử lý Silver Layer và các test liên quan.
Ràng buộc: không thay đổi schema đầu ra hiện tại.
Tiêu chí hoàn thành: dữ liệu được chuẩn hóa, không làm tăng số bản ghi lỗi.
Kiểm thử: chạy test của pipeline và một mẫu dữ liệu nhỏ.
```

Sau đó, Codex sẽ tự thực hiện vòng cộng tác:

1. Kiểm tra kết nối và trạng thái phiên làm việc.
2. Yêu cầu ChatGPT đọc đúng workspace và lập kế hoạch.
3. Đánh giá kế hoạch, rồi tự chỉnh sửa mã nguồn.
4. Chạy kiểm thử hoặc build phù hợp.
5. Để ChatGPT đọc thay đổi thực tế và review độc lập.
6. Sửa tiếp nếu cần, cho đến khi đạt tiêu chí hoàn thành.

## 2. Cách viết yêu cầu để nhận kết quả tốt

Một yêu cầu hiệu quả nên có năm thành phần:

### Mục tiêu rõ ràng

Mô tả kết quả cuối cùng thay vì chỉ nêu hoạt động chung chung.

- Tốt: `Tạo báo cáo so sánh độ phủ kỹ năng giữa dữ liệu lịch sử và dữ liệu mới.`
- Chưa tốt: `Phân tích dữ liệu giúp tôi.`

### Phạm vi cụ thể

Nêu module, pipeline, dashboard hoặc loại file được phép thay đổi. Nếu chưa biết vị trí file, có thể yêu cầu ChatGPT và Codex tự xác định.

```text
Phạm vi ưu tiên là pipeline Silver Layer. Nếu cần sửa ngoài phạm vi này, hãy giải thích lý do trước.
```

### Ràng buộc quan trọng

Nêu những thứ phải được giữ nguyên, chẳng hạn:

- Không đổi schema dữ liệu.
- Không xóa API hoặc tùy chọn đang được sử dụng.
- Không sửa dữ liệu nguồn.
- Không thêm dependency nếu chưa thật sự cần thiết.
- Giữ tương thích với Python hoặc Spark phiên bản hiện tại.

### Tiêu chí hoàn thành có thể kiểm tra

Ví dụ:

- Test hiện có đều chạy thành công.
- Không còn bản ghi trùng theo khóa đã định nghĩa.
- Dashboard hiển thị đúng bộ lọc và không lỗi khi dữ liệu rỗng.
- Pipeline xử lý được file mẫu và tạo đúng schema đầu ra.

### Yêu cầu kiểm thử

Nếu biết lệnh test, hãy ghi rõ. Nếu chưa biết, dùng:

```text
Hãy tự xác định các kiểm thử phù hợp, chạy chúng và báo rõ phần nào chưa thể kiểm chứng.
```

## 3. Các mẫu prompt nên dùng

### Lập kế hoạch trước khi thay đổi lớn

```text
Sử dụng Codex with ChatGPT để phân tích kiến trúc hiện tại và lập kế hoạch triển khai <tính năng>.
Chưa chỉnh sửa file cho đến khi kế hoạch đã chỉ rõ các file liên quan, rủi ro và cách kiểm thử.
```

### Triển khai một tính năng hoàn chỉnh

```text
Sử dụng Codex with ChatGPT để triển khai <tính năng> từ đầu đến cuối.
ChatGPT lập kế hoạch và review; Codex thực hiện, chạy test và tự sửa các lỗi nằm trong phạm vi.
Hoàn tất khi <tiêu chí cụ thể>.
```

### Điều tra lỗi khó

```text
Sử dụng Codex with ChatGPT để chẩn đoán lỗi <mô tả lỗi>.
Trước tiên hãy xác định nguyên nhân dựa trên mã nguồn và trạng thái hiện tại.
Chỉ triển khai bản sửa khi đã có bằng chứng đủ mạnh, sau đó chạy test hồi quy.
```

### Review thay đổi chưa commit

```text
Sử dụng Codex with ChatGPT để review toàn bộ thay đổi chưa commit.
Tập trung vào lỗi logic, mất dữ liệu, khả năng tương thích, hiệu năng và thiếu test.
Chỉ sửa các vấn đề đã được xác nhận; không chỉnh sửa phong cách không cần thiết.
```

### Refactor an toàn

```text
Sử dụng Codex with ChatGPT để refactor <module> mà không thay đổi hành vi bên ngoài.
Yêu cầu ChatGPT xác định rủi ro và test bảo vệ trước; Codex thực hiện theo từng bước nhỏ và kiểm thử sau mỗi bước quan trọng.
```

### Nhiệm vụ phù hợp với dự án Big Data này

```text
Sử dụng Codex with ChatGPT để đánh giá pipeline Bronze → Silver → Gold.
Tìm các điểm có nguy cơ sai schema, trùng dữ liệu, rò rỉ dữ liệu giữa train/test hoặc xử lý không ổn định trên Spark.
Đề xuất và triển khai các sửa đổi ưu tiên cao, kèm kiểm thử phù hợp.
```

## 4. Khi nào nên dùng skill này

Nên dùng Codex with ChatGPT khi công việc có một hoặc nhiều đặc điểm sau:

- Thay đổi nhiều file hoặc nhiều tầng kiến trúc.
- Cần cân nhắc thiết kế trước khi viết mã.
- Debug lỗi phức tạp hoặc khó tái hiện.
- Refactor có nguy cơ làm thay đổi hành vi.
- Cần một lượt review độc lập sau khi triển khai.
- Cần đánh giá schema, pipeline dữ liệu, mô hình hoặc hiệu năng.

Với thay đổi rất nhỏ như sửa lỗi chính tả hoặc đổi một giá trị cấu hình rõ ràng, dùng Codex trực tiếp thường nhanh hơn.

## 5. Cách làm việc với ChatGPT Project đã cấu hình

Workspace này được liên kết với:

- Project: `BigData_Job_Analy`
- Connector: `Codex with ChatGPT · BigData_Job_Analy`
- Chế độ bộ nhớ: Project-only

Để tránh đọc nhầm workspace:

- Không đổi tên hoặc tạo thêm connector cho cùng workspace.
- Không đưa repository vào phần Sources của ChatGPT Project.
- Không mở chat C2C bên ngoài Project `BigData_Job_Analy`.
- Không dùng connector của một workspace khác.
- Khi tạo một cuộc hội thoại Codex mới, hãy để Codex mở một chat mới bên trong Project đã lưu.

Trong cùng một cuộc hội thoại Codex, skill sẽ tiếp tục sử dụng chat ChatGPT đã lưu thay vì tạo chat mới không cần thiết.

## 6. Những việc không cần làm thủ công

Khi dùng skill, bạn không cần:

- Sao chép nội dung file, diff hoặc log sang ChatGPT.
- Yêu cầu ChatGPT trực tiếp sửa file.
- Tự gửi các thông báo trạng thái kỹ thuật giữa Codex và ChatGPT.
- Tự tạo lại kết nối sau mỗi tác vụ.
- Tự quyết định file nào cần đọc trước.

Nếu ChatGPT hỏi bạn dán file hoặc log, hãy yêu cầu nó đọc dữ liệu từ connector đã liên kết. Codex sẽ tự gửi phần thông tin điều phối cần thiết và giữ nội dung lớn trong workspace.

## 7. Tiếp tục công việc sau khi đóng VS Code hoặc đổi phiên

Trong cuộc hội thoại Codex mới, chỉ cần nói:

```text
Sử dụng Codex with ChatGPT để tiếp tục công việc trong workspace này.
Hãy kiểm tra trạng thái hiện tại trước khi bắt đầu.
```

Nếu có một nhiệm vụ đang dang dở, bổ sung mục tiêu ngắn gọn:

```text
Tiếp tục nhiệm vụ chuẩn hóa kỹ năng trong Silver Layer. Kiểm tra checkpoint và thay đổi hiện có, không chạy lại phần đã hoàn tất.
```

Skill sẽ kiểm tra phiên, tránh gửi lại yêu cầu hoặc chạy lại bước đã hoàn tất, rồi tiếp tục từ trạng thái gần nhất.

## 8. Khi kết nối gặp lỗi

Hãy nói với Codex:

```text
Kiểm tra và tự sửa kết nối Codex with ChatGPT cho workspace này, sau đó tiếp tục nhiệm vụ đang dở.
```

Codex sẽ chạy kiểm tra sức khỏe và tự sửa các lỗi có thể xử lý. Bạn chỉ cần thao tác khi được yêu cầu đăng nhập, xác thực, nhập mã ghép đôi hoặc xác nhận quyền truy cập.

Lưu ý:

- Không tự tạo connector thứ hai.
- Không tự xóa Project hoặc cuộc chat đã lưu.
- Không cung cấp cookie, token hoặc thông tin đăng nhập cho Codex hay ChatGPT.
- Mã ghép đôi dùng một lần là thông tin duy nhất có thể cần nhập khi được hướng dẫn.

## 9. Checklist trước một tác vụ quan trọng

- [ ] Đã mở đúng thư mục workspace trong VS Code.
- [ ] Yêu cầu có mục tiêu và tiêu chí hoàn thành rõ ràng.
- [ ] Đã nêu phạm vi và các phần không được thay đổi.
- [ ] Đã yêu cầu kiểm thử hoặc xác minh kết quả.
- [ ] Không dán file, diff, log hoặc bí mật vào ChatGPT.
- [ ] Để Codex thực thi và để ChatGPT review độc lập.
- [ ] Chỉ kết thúc khi test phù hợp đã chạy hoặc phần chưa kiểm chứng được nêu rõ.

## 10. Mẫu yêu cầu khuyến nghị dùng hằng ngày

```text
Sử dụng Codex with ChatGPT cho nhiệm vụ này.

MỤC TIÊU:
<Kết quả cuối cùng cần đạt>

BỐI CẢNH:
<Vấn đề hiện tại và lý do cần thay đổi>

PHẠM VI:
<Module, pipeline hoặc chức năng liên quan>

RÀNG BUỘC:
- <Điều phải giữ nguyên>
- <Điều không được làm>

TIÊU CHÍ HOÀN THÀNH:
- <Kết quả có thể kiểm tra 1>
- <Kết quả có thể kiểm tra 2>

KIỂM THỬ:
<Lệnh test cụ thể hoặc yêu cầu tự xác định test phù hợp>

Hãy để ChatGPT lập kế hoạch và review độc lập. Codex chịu trách nhiệm thực thi,
chạy kiểm thử, tự sửa lỗi trong phạm vi và báo rõ mọi phần chưa thể xác minh.
```

Nguyên tắc ngắn gọn nhất để nhớ: **mô tả đích đến thật rõ, để ChatGPT suy nghĩ và review, để Codex thực thi và kiểm chứng**.
