"""
Apache Spark ETL Pipeline (Bronze -> Silver Layer):
1. Ingests raw data from Bronze Layer (Historical & Fresh).
2. Cleans text, strips HTML tags, formats timestamps.
3. Computes SHA-256 job_hash and deduplicates records.
4. Normalizes job titles into 8 canonical IT occupations.
5. Extracts normalized skills from descriptions.
6. Enforces the 18-field Unified Schema.
7. Saves to Silver Layer in partitioned Parquet format (year, month).
"""

import os
import sys
import re
import json
import hashlib
from datetime import datetime

import pyspark
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, udf, when, coalesce, lit, substring, 
    to_timestamp, year, month, concat_ws, sha2,
    monotonically_increasing_id
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, 
    TimestampType, ArrayType, BooleanType
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRONZE_HIST_DIR = os.path.join(BASE_DIR, "data", "bronze", "global", "historical")
BRONZE_FRESH_DIR = os.path.join(BASE_DIR, "data", "bronze", "global", "fresh")
SILVER_GLOBAL_DIR = os.path.join(BASE_DIR, "data", "silver", "global")
CONFIG_DIR = os.path.join(BASE_DIR, "configs")

TITLE_MAP_FILE = os.path.join(CONFIG_DIR, "job_title_mapping_v0.json")
SKILLS_MAP_FILE = os.path.join(CONFIG_DIR, "skills_v0.json")

def create_spark_session():
    # Set Java, Hadoop, and Python environments
    if "JAVA_HOME" not in os.environ:
        os.environ["JAVA_HOME"] = r"C:\java\jdk-17"
    if "HADOOP_HOME" not in os.environ:
        os.environ["HADOOP_HOME"] = r"C:\hadoop"
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

    spark = SparkSession.builder \
        .appName("ITJobSkill_BronzeToSilver_ETL") \
        .master("local[*]") \
        .config("spark.driver.memory", "4g") \
        .config("spark.sql.shuffle.partitions", "8") \
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic") \
        .config("spark.hadoop.io.native.lib", "false") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark

def load_dictionaries():
    with open(TITLE_MAP_FILE, "r", encoding="utf-8") as f:
        title_mapping = json.load(f)
    with open(SKILLS_MAP_FILE, "r", encoding="utf-8") as f:
        skills_dict = json.load(f)
    return title_mapping, skills_dict

def build_udfs(title_mapping, skills_dict):
    # 1. Clean HTML
    def clean_html(text):
        if not text:
            return ""
        clean = re.sub(r"<[^>]+>", " ", str(text))
        clean = clean.replace("&amp;", "&").replace("&nbsp;", " ").replace("&quot;", '"')
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    # 2. Normalize Title
    def normalize_title(title):
        if not title:
            return "Other IT"
        t_low = str(title).lower().strip()
        for role, variations in title_mapping.items():
            for var in variations:
                if var in t_low:
                    return role
        return "Other IT"

    # 3. Extract Skills
    # Precompile regex for efficiency
    compiled_skills = {}
    for skill, aliases in skills_dict.items():
        patterns = [rf"(?:\b|(?<=[\s,./])){re.escape(a)}(?:\b|(?=[\s,./]))" for a in aliases]
        compiled_skills[skill] = re.compile("|".join(patterns), re.IGNORECASE)

    def extract_skills(text):
        if not text:
            return []
        clean = clean_html(text)
        extracted = []
        for skill, pat in compiled_skills.items():
            if pat.search(clean):
                extracted.append(skill)
        return sorted(extracted)

    # 4. Extract City
    def extract_city(loc):
        if not loc or loc.lower() == "remote":
            return None
        parts = str(loc).split(",")
        return parts[0].strip() if parts else str(loc).strip()

    # 5. Extract Work Mode
    def extract_work_mode(loc, remote_flag):
        if remote_flag is True or (loc and "remote" in str(loc).lower()):
            return "Remote"
        if loc and "hybrid" in str(loc).lower():
            return "Hybrid"
        return "Onsite"

    clean_html_udf = udf(clean_html, StringType())
    norm_title_udf = udf(normalize_title, StringType())
    extract_skills_udf = udf(extract_skills, ArrayType(StringType()))
    extract_city_udf = udf(extract_city, StringType())
    extract_work_mode_udf = udf(extract_work_mode, StringType())

    return {
        "clean_html": clean_html_udf,
        "norm_title": norm_title_udf,
        "extract_skills": extract_skills_udf,
        "extract_city": extract_city_udf,
        "extract_work_mode": extract_work_mode_udf
    }

def run_etl():
    print("==================================================")
    print(" starting Apache Spark ETL: Bronze -> Silver")
    print("==================================================")
    spark = create_spark_session()
    title_mapping, skills_dict = load_dictionaries()
    udfs = build_udfs(title_mapping, skills_dict)

    dfs = []

    # 1. Read Bronze Historical (JSON)
    if os.path.exists(BRONZE_HIST_DIR) and os.listdir(BRONZE_HIST_DIR):
        print(f"[ETL] Reading Bronze Historical Data from {BRONZE_HIST_DIR}...")
        df_hist_raw = spark.read.option("multiline", "true").json(os.path.join(BRONZE_HIST_DIR, "*.json"))
        hist_cols = df_hist_raw.columns

        title_col = col("job_title") if "job_title" in hist_cols else col("title")
        company_col = col("company_name") if "company_name" in hist_cols else col("company")
        loc_col = col("job_location") if "job_location" in hist_cols else col("location")
        country_col = col("job_country") if "job_country" in hist_cols else col("country")
        posted_col = col("job_posted_date") if "job_posted_date" in hist_cols else col("posted_at")
        
        if "job_description" in hist_cols:
            desc_col = col("job_description")
        elif "job_skills" in hist_cols:
            desc_col = concat_ws(". ", title_col, col("job_skills"))
        else:
            desc_col = title_col

        salary_col = when(
            (col("salary_year_avg").isNotNull()) & (col("salary_year_avg") != "") & (col("salary_year_avg") != "null"),
            col("salary_year_avg").cast("double").cast(IntegerType())
        ).otherwise(lit(None).cast(IntegerType())) if "salary_year_avg" in hist_cols else lit(None).cast(IntegerType())

        remote_col = col("job_work_from_home") if "job_work_from_home" in hist_cols else lit(False)

        df_hist = df_hist_raw.select(
            concat_ws("_", lit("hist"), monotonically_increasing_id()).alias("job_id"),
            coalesce(title_col, lit("Unknown Title")).alias("title"),
            coalesce(company_col, lit("Unknown Company")).alias("company"),
            coalesce(loc_col, lit("Remote")).alias("location"),
            coalesce(country_col, lit("Worldwide")).alias("country"),
            desc_col.alias("raw_description"),
            posted_col.alias("posted_at_raw"),
            col("collected_at"),
            col("source"),
            col("market"),
            salary_col.alias("salary_min"),
            salary_col.alias("salary_max"),
            lit("USD").alias("currency"),
            remote_col.alias("is_remote")
        )
        dfs.append(df_hist)

    # 2. Read Bronze Fresh (JSON)
    if os.path.exists(BRONZE_FRESH_DIR) and os.listdir(BRONZE_FRESH_DIR):
        print(f"[ETL] Reading Bronze Fresh Data from {BRONZE_FRESH_DIR}...")
        df_fresh_raw = spark.read.option("multiline", "true").json(os.path.join(BRONZE_FRESH_DIR, "*.json"))
        fresh_cols = df_fresh_raw.columns

        id_col = col("raw_id") if "raw_id" in fresh_cols else concat_ws("_", lit("fresh"), monotonically_increasing_id())
        desc_col = col("description") if "description" in fresh_cols else col("title")

        df_fresh = df_fresh_raw.select(
            id_col.alias("job_id"),
            col("title"),
            col("company"),
            col("location"),
            lit("Worldwide").alias("country"),
            desc_col.alias("raw_description"),
            col("posted_at").alias("posted_at_raw"),
            col("collected_at"),
            col("source"),
            col("market"),
            lit(None).cast(IntegerType()).alias("salary_min"),
            lit(None).cast(IntegerType()).alias("salary_max"),
            col("currency"),
            col("remote").alias("is_remote")
        )
        dfs.append(df_fresh)

    if not dfs:
        print("[ETL] No data found in Bronze Layer! Exiting.")
        spark.stop()
        return

    # Union all datasets
    combined_df = dfs[0]
    for df_item in dfs[1:]:
        combined_df = combined_df.unionByName(df_item)

    initial_count = combined_df.count()
    print(f"[ETL] Total raw records loaded from Bronze: {initial_count:,}")

    # 3. Apply Transformations
    print("[ETL] Applying Transformations, Normalization & Skill Extraction...")
    processed_df = combined_df \
        .withColumn("description", udfs["clean_html"](col("raw_description"))) \
        .withColumn("normalized_title", udfs["norm_title"](col("title"))) \
        .withColumn("city", udfs["extract_city"](col("location"))) \
        .withColumn("work_mode", udfs["extract_work_mode"](col("location"), col("is_remote"))) \
        .withColumn("skills", udfs["extract_skills"](col("description"))) \
        .withColumn("posted_at", to_timestamp(col("posted_at_raw"), "yyyy-MM-dd HH:mm:ss")) \
        .withColumn("collected_at", to_timestamp(col("collected_at"), "yyyy-MM-dd HH:mm:ss")) \
        .withColumn("experience_level", 
            when(col("title").rlike("(?i)junior|fresher|intern"), "Junior")
            .when(col("title").rlike("(?i)senior|lead|principal|architect"), "Senior")
            .otherwise("Mid")
        ) \
        .withColumn("job_hash", sha2(concat_ws("|", col("company"), col("title"), col("location"), substring(col("posted_at_raw"), 1, 10)), 256))

    # 4. Deduplication
    print("[ETL] Performing Deduplication on job_hash...")
    dedup_df = processed_df.dropDuplicates(["job_hash"])
    dedup_count = dedup_df.count()
    duplicates_removed = initial_count - dedup_count
    print(f"[ETL] Duplicates removed: {duplicates_removed:,} (Remaining clean records: {dedup_count:,})")

    # 5. Extract Partition Columns (year, month)
    silver_df = dedup_df \
        .withColumn("year", coalesce(year(col("posted_at")), lit(2026))) \
        .withColumn("month", coalesce(month(col("posted_at")), lit(9))) \
        .select(
            "job_id", "title", "normalized_title", "company", "location", "city", "country",
            "market", "work_mode", "description", "experience_level", "salary_min", "salary_max",
            "currency", "posted_at", "collected_at", "source", "skills", "year", "month"
        )

    # 6. Save to Silver Layer (Parquet Partitioned)
    print(f"[ETL] Writing Cleaned Data to Silver Layer at {SILVER_GLOBAL_DIR}...")
    silver_df.write \
        .mode("overwrite") \
        .partitionBy("year", "month") \
        .parquet(SILVER_GLOBAL_DIR)

    print(f"[ETL] Successfully completed Spark ETL! Output saved to Silver Layer.")
    spark.stop()

if __name__ == "__main__":
    run_etl()
