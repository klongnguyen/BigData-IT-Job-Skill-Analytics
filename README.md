# BigData IT Job Skill Analytics

A Big Data system for analyzing the IT recruitment market and forecasting skill-demand trends using historical and fresh job-posting data.

## Project Overview

The project focuses on collecting, processing, analyzing, and forecasting IT job-market trends. Historical recruitment data is combined with newly collected job postings so the system can better reflect the fast-changing demand for technology skills.

Main objectives:

- Analyze high-demand IT occupations.
- Identify important skills for each occupation.
- Track skill-demand changes over time.
- Classify skill trends as **Growing**, **Stable**, or **Declining**.
- Compare historical-only, recent-only, and hybrid forecasting approaches.
- Build an interactive dashboard for job-market and skill-demand analytics.

## Proposed Technology Stack

- Python
- PySpark
- Apache Spark
- Hadoop / HDFS
- Spark MLlib
- MongoDB
- Streamlit
- Git / GitHub

Optional components may include Kafka, Docker, Plotly, Pandas, and Scikit-learn.

## Initial Architecture

```text
Historical Data + Fresh Job Data
              |
              v
        Bronze Layer
              |
              v
        Apache Spark
 Cleaning / Deduplication /
 Normalization / Skill Extraction
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
 Analytics       Spark MLlib
       |         Trend Forecast
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

## Repository Structure

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

> The `data/` directories represent the logical Bronze-Silver-Gold data layout. Large datasets should normally be stored in HDFS/object storage and excluded from Git.

## Project Plan

For the detailed research questions, architecture, 10-week roadmap, data strategy, machine-learning experiments, dashboard scope, risks, and GO/NO-GO criteria, see:

**[View the full project plan →](docs/PROJECT_PLAN.md)**

## Current Status

Initial repository structure created. The next milestone is to validate historical/fresh data sources and define the unified job-posting schema before implementing the ingestion and Spark ETL pipeline.
