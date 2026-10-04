# BigData IT Job Skill Analytics

Hệ thống Big Data phục vụ phân tích thị trường tuyển dụng CNTT và dự báo xu hướng nhu cầu kỹ năng dựa trên dữ liệu tuyển dụng lịch sử kết hợp với dữ liệu tuyển dụng mới.

## Tổng quan đề tài

Đề tài tập trung xây dựng một hệ thống có khả năng thu thập, xử lý, phân tích và dự báo xu hướng của thị trường tuyển dụng CNTT. Dữ liệu tuyển dụng lịch sử sẽ được kết hợp với các tin tuyển dụng mới nhằm phản ánh tốt hơn sự thay đổi nhanh chóng của nhu cầu kỹ năng trong ngành công nghệ thông tin.

Các mục tiêu chính:

- Phân tích các vị trí CNTT đang có nhu cầu tuyển dụng cao.
- Xác định các kỹ năng quan trọng đối với từng vị trí CNTT.
- Theo dõi sự thay đổi nhu cầu kỹ năng theo thời gian.
- Phân loại xu hướng kỹ năng thành **Growing**, **Stable** hoặc **Declining**.
- Khi quality gate cho phép, so sánh bốn nhánh A/B/C/D trên cùng future test và baseline `Stable`.
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
│   ├── job_title_mapping_v0.json
│   ├── skills_v0.json       (runtime taxonomy)
│   └── skills.json          (legacy)
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
│   ├── PROJECT_PLAN.md       (legacy; see current Final Plan)
│   ├── data/
│   ├── planning/
│   └── reviews/
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

Kế hoạch chuẩn hiện tại, gồm câu hỏi nghiên cứu, kiến trúc hệ thống, chiến lược dữ liệu, lộ trình, thí nghiệm Machine Learning, phạm vi dashboard, rủi ro và tiêu chí GO / NO-GO:

**[Xem Final Plan →](FINAL_PLAN_BigData_IT_Job_Market_Skill_Forecasting.md)**

`docs/PROJECT_PLAN.md` là tài liệu lập kế hoạch ban đầu được giữ lại để tham khảo lịch sử; nội dung này đã được thay thế bởi Final Plan.

## Trạng thái hiện tại

Phase 01 đã được review lại dựa trên archive trong repository: 785.741 dòng thuộc năm 2023, có source tags nhưng không có job description. Sample historical được lấy trực tiếp từ archive; fixture synthetic đã tách riêng. Quyết định hiện tại là GO cho prototype, conditional GO cho descriptive analytics giới hạn và NO-GO cho forecasting đến khi có dữ liệu nhiều năm, provenance/license và đánh giá taxonomy độc lập. Xem [báo cáo GO/NO-GO](docs/planning/go_no_go_report.md), [audit dữ liệu](docs/data/phase01_data_audit.json) và [review Phase 01](docs/reviews/PHASE_01_SYSTEM_REVIEW.md).
