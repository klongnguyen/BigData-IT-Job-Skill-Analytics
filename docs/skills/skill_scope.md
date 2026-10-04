# Skill Scope & Taxonomy: Big Data IT Job Skill Analytics

Taxonomy runtime hiện tại là **v0.1** với 48 canonical skill ID. Cấu hình đang được nạp từ `configs/skills_v0.json` vì tên file là đường dẫn tương thích; key của JSON là canonical skill ID. Danh sách alias bên dưới được sinh từ chính cấu hình này để tránh tài liệu lệch với mã. `configs/skills.json` là bản legacy, không phải nguồn cấu hình runtime. Manifest lưu checksum riêng cho title/skill config để phân biệt chính xác từng lần sửa.

## Danh mục theo 8 nhóm

### Ngôn ngữ và web frontend

| Canonical ID | Tên hiển thị | Alias được cấu hình |
|---|---|---|
| `python` | Python | `python`, `python3` |
| `java` | Java | `java`, `core java`, `java 8`, `java 11`, `java 17` |
| `javascript` | Javascript | `javascript`, `javascript es6`, `ecmascript` |
| `typescript` | Typescript | `typescript` |
| `react` | React | `react`, `react.js`, `reactjs` |
| `next_js` | Next.js | `next.js`, `nextjs` |
| `html_css` | HTML/CSS | `html/css`, `html`, `css` |
| `c_plus_plus` | C++ | `c++`, `cpp` |
| `c_sharp` | C# | `c#`, `c sharp`, `.net c#` |
| `golang` | Go | `golang`, `go language`, `go lang` |
| `rust` | Rust | `rust`, `rustlang` |

### Database và phân tích dữ liệu

| Canonical ID | Tên hiển thị | Alias được cấu hình |
|---|---|---|
| `sql` | Sql | `sql`, `rdbms` |
| `pandas` | Pandas | `pandas` |
| `numpy` | Numpy | `numpy` |
| `mysql` | Mysql | `mysql` |
| `postgresql` | Postgresql | `postgres`, `postgresql`, `pgsql` |
| `mongodb` | Mongodb | `mongodb`, `mongo db` |
| `redis` | Redis | `redis` |
| `cassandra` | Cassandra | `cassandra`, `apache cassandra` |

### Big Data và streaming

| Canonical ID | Tên hiển thị | Alias được cấu hình |
|---|---|---|
| `spark` | Spark | `spark`, `apache spark`, `pyspark`, `spark sql` |
| `hadoop` | Hadoop | `hadoop`, `apache hadoop`, `hdfs`, `mapreduce` |
| `kafka` | Kafka | `kafka`, `apache kafka` |
| `hive` | Hive | `hive`, `apache hive` |
| `flink` | Flink | `flink`, `apache flink` |
| `airflow` | Airflow | `airflow`, `apache airflow` |

### Cloud

| Canonical ID | Tên hiển thị | Alias được cấu hình |
|---|---|---|
| `aws` | Aws | `aws`, `amazon web services`, `ec2`, `s3`, `lambda`, `redshift` |
| `azure` | Azure | `azure`, `microsoft azure`, `azure devops` |
| `gcp` | Google Cloud Platform | `gcp`, `google cloud`, `google cloud platform`, `bigquery` |

### DevOps và hạ tầng

| Canonical ID | Tên hiển thị | Alias được cấu hình |
|---|---|---|
| `docker` | Docker | `docker`, `containerization` |
| `kubernetes` | Kubernetes | `kubernetes`, `k8s` |
| `ci_cd` | CI/CD | `ci/cd`, `cicd`, `continuous integration`, `continuous deployment` |
| `jenkins` | Jenkins | `jenkins` |
| `terraform` | Terraform | `terraform`, `infrastructure as code` |
| `git` | Git | `git`, `github`, `gitlab` |

### BI và analytics

| Canonical ID | Tên hiển thị | Alias được cấu hình |
|---|---|---|
| `power_bi` | Power BI | `power bi`, `powerbi`, `dax`, `power query` |
| `tableau` | Tableau | `tableau`, `tableau desktop` |
| `excel` | Excel | `excel`, `microsoft excel`, `advanced excel` |
| `looker` | Looker | `looker`, `lookml` |

### AI và Machine Learning

| Canonical ID | Tên hiển thị | Alias được cấu hình |
|---|---|---|
| `scikit_learn` | Scikit-learn | `scikit-learn`, `sklearn` |
| `tensorflow` | Tensorflow | `tensorflow`, `keras` |
| `pytorch` | Pytorch | `pytorch`, `torch` |
| `nlp` | Natural Language Processing | `nlp`, `natural language processing` |
| `computer_vision` | Computer Vision | `computer vision`, `opencv` |

### GenAI và LLM

| Canonical ID | Tên hiển thị | Alias được cấu hình |
|---|---|---|
| `generative_ai` | Generative AI | `generative ai`, `gen ai`, `genai` |
| `llm` | Large Language Models | `llm`, `large language model`, `large language models` |
| `rag` | Retrieval-Augmented Generation | `rag`, `retrieval augmented generation`, `retrieval-augmented generation` |
| `langchain` | Langchain | `langchain`, `llamaindex` |
| `prompt_engineering` | Prompt Engineering | `prompt engineering`, `prompt design` |

## Quy tắc và giới hạn

- Matching không phân biệt hoa thường, kiểm tra ranh giới token để `C++`/`C#` nhận đúng và tránh khớp chuỗi con không liên quan.
- Chuẩn hóa title dùng cùng helper `src/common/taxonomy.py`; alias khớp dài hơn được ưu tiên khi có nhiều candidate.
- Skill extraction từ JD là keyword matching theo taxonomy, không phải mô hình ngữ nghĩa và chưa được đánh giá precision/recall bằng tập gán nhãn độc lập.
- Historical `job_skills` là source tags; không được gọi là kỹ năng trích từ JD. Pipeline cần ghi phân biệt `skills_origin` trong provenance.
- Tránh alias ngắn hoặc mơ hồ nếu chưa có ngữ cảnh. Ví dụ không dùng `go` đứng riêng; dùng `golang`, `go language`, hoặc `go lang`.
- Các alias và nhóm taxonomy là V0.1; thay đổi cấu hình cần cập nhật version provenance và đánh giá lại coverage.
