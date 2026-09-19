# BigData IT Job Skill Analytics

Hệ thống Big Data phục vụ phân tích thị trường tuyển dụng CNTT và dự báo xu hướng nhu cầu kỹ năng dựa trên dữ liệu tuyển dụng lịch sử kết hợp với dữ liệu tuyển dụng mới.

## Tổng quan đề tài

Đề tài tập trung xây dựng một hệ thống có khả năng thu thập, xử lý, phân tích và dự báo xu hướng của thị trường tuyển dụng CNTT. Dữ liệu tuyển dụng lịch sử sẽ được kết hợp với các tin tuyển dụng mới nhằm phản ánh tốt hơn sự thay đổi nhanh chóng của nhu cầu kỹ năng trong ngành công nghệ thông tin.

Các mục tiêu chính:

- Phân tích các vị trí CNTT đang có nhu cầu tuyển dụng cao.
- Xác định các kỹ năng quan trọng đối với từng vị trí CNTT.
- Theo dõi sự thay đổi nhu cầu kỹ năng theo thời gian.
- Phân loại xu hướng kỹ năng thành **Growing**, **Stable** hoặc **Declining**.
- So sánh ba phương án dự báo: chỉ dùng dữ liệu lịch sử, chỉ dùng dữ liệu gần đây và mô hình kết hợp.
- Xây dựng dashboard trực quan phục vụ phân tích thị trường việc làm và nhu cầu kỹ năng CNTT.

## Công nghệ dự kiến

- Python
- PySpark
- Apache Spark
- Hadoop / HDFS
- Spark MLlib
- MongoDB
- Streamlit
- Git / GitHub

Các công nghệ có thể bổ sung tùy theo tiến độ gồm Kafka, Docker, Plotly, Pandas và Scikit-learn.

## Kiến trúc hệ thống ban đầu

```text
Dữ liệu lịch sử + Dữ liệu tuyển dụng mới
                  |
                  v
            Bronze Layer
                  |
                  v
            Apache Spark
 Làm sạch / Loại trùng lặp /
 Chuẩn hóa / Trích xuất kỹ năng
                  |
                  v
            Silver Layer
                  |
                  v
 Feature Engineering + Analytics
                  |
           +------+------+
           |             |
           v             v
       Analytics     Spark MLlib
           |        Dự báo xu hướng
           +------+------+
                  |
                  v
              Gold Layer
                  |
                  v
               MongoDB
                  |
                  v
          Streamlit Dashboard
```

## Cấu trúc thư mục dự án

```text
BigData-IT-Job-Skill-Analytics/
├── configs/
│   └── skills.json
├── dashboard/
│   └── app.py
├── data/
│   ├── bronze/
│   │   ├── historical/
│   │   └── fresh/
│   ├── silver/
│   │   └── normalized_jobs/
│   └── gold/
│       ├── skill_stats/
│       ├── job_stats/
│       └── predictions/
├── docs/
│   └── PROJECT_PLAN.md
├── notebooks/
├── src/
│   ├── collection/
│   ├── etl/
│   ├── skills/
│   ├── analytics/
│   ├── ml/
│   └── common/
├── tests/
├── .gitignore
├── requirements.txt
└── README.md
```

> Các thư mục trong `data/` thể hiện kiến trúc dữ liệu logic theo mô hình Bronze - Silver - Gold. Các bộ dữ liệu có dung lượng lớn nên được lưu trên HDFS hoặc hệ thống lưu trữ phù hợp và không đưa trực tiếp lên GitHub.

## Kế hoạch dự án

Kế hoạch chi tiết bao gồm câu hỏi nghiên cứu, kiến trúc hệ thống, chiến lược dữ liệu, lộ trình 10 tuần, thí nghiệm Machine Learning, phạm vi dashboard, rủi ro và tiêu chí GO / NO-GO được trình bày tại:

**[Xem kế hoạch dự án đầy đủ →](docs/PROJECT_PLAN.md)**

## Trạng thái hiện tại

Đã hoàn thành cấu trúc repository ban đầu. Bước tiếp theo là khảo sát và xác thực nguồn dữ liệu lịch sử, nguồn dữ liệu tuyển dụng mới, đồng thời hoàn thiện Unified Job Schema trước khi triển khai pipeline thu thập dữ liệu và Spark ETL.
