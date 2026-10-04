"""Bronze -> Silver Spark ETL with stable IDs, provenance and timestamp quarantine."""

import argparse
import os
import shutil
import sys
import re
import html
import uuid

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from pyspark.sql import SparkSession, Window
from pyspark.sql.functions import (
    coalesce, col, concat_ws, date_format, lit, lower, month,
    regexp_replace, row_number, sha2, struct, to_json, try_to_timestamp, trim, udf, year, when,
)
from pyspark.sql.types import ArrayType, BooleanType, IntegerType, StringType

from src.common.schema import UNIFIED_JOB_FIELDS
from src.common.identity import stable_job_id
from src.common.taxonomy import (
    TAXONOMY_VERSION,
    extract_skills,
    load_dictionaries,
    normalize_source_tags,
    normalize_title,
)

BRONZE_HIST_DIR = os.path.join(BASE_DIR, "data", "bronze", "global", "historical")
BRONZE_FRESH_DIR = os.path.join(BASE_DIR, "data", "bronze", "global", "fresh")
SILVER_GLOBAL_DIR = os.path.join(BASE_DIR, "data", "silver", "global")
PROVENANCE_GLOBAL_DIR = os.path.join(BASE_DIR, "data", "provenance", "global", "job_provenance")
QUARANTINE_GLOBAL_DIR = os.path.join(BASE_DIR, "data", "quarantine", "global", "invalid_records")


def _remove_path(path):
    if not os.path.lexists(path):
        return
    if os.path.isdir(path) and not os.path.islink(path):
        shutil.rmtree(path)
    else:
        os.remove(path)


def _promote_staged_outputs(staged_outputs, run_id, replace_existing):
    backups = {}
    promoted = []
    try:
        if replace_existing:
            for target in staged_outputs.values():
                if os.path.lexists(target):
                    backup = f"{target}.backup-{run_id}"
                    os.replace(target, backup)
                    backups[target] = backup

        for stage, target in staged_outputs.items():
            os.replace(stage, target)
            promoted.append(target)
    except Exception as promotion_error:
        rollback_errors = []
        for target in reversed(promoted):
            try:
                _remove_path(target)
            except OSError as error:
                rollback_errors.append(f"remove {target}: {error}")
        for target, backup in reversed(list(backups.items())):
            try:
                if os.path.lexists(backup) and not os.path.lexists(target):
                    os.replace(backup, target)
            except OSError as error:
                rollback_errors.append(f"restore {backup} to {target}: {error}")
        if rollback_errors:
            raise RuntimeError(
                "Output promotion failed and rollback was incomplete; "
                f"recovery paths may remain: {rollback_errors}"
            ) from promotion_error
        raise

    if backups:
        print("[ETL] Previous outputs retained as backups:")
        for backup in backups.values():
            print(f"  {backup}")


def create_spark_session():
    os.environ.setdefault("JAVA_HOME", r"C:\java\jdk-17")
    os.environ.setdefault("HADOOP_HOME", r"C:\hadoop")
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
    spark = (SparkSession.builder.appName("ITJobSkill_BronzeToSilver_ETL")
             .master("local[*]").config("spark.driver.memory", "4g")
             .config("spark.sql.shuffle.partitions", "8")
             .config("spark.sql.session.timeZone", "UTC")
             .config("spark.hadoop.io.native.lib", "false").getOrCreate())
    spark.sparkContext.setLogLevel("WARN")
    return spark


def _source_column(columns, names, default):
    for name in names:
        if name in columns:
            return col(name)
    return lit(default)


def _remote_flag(value):
    return str(value or "").strip().casefold() in {"true", "1", "yes", "remote"}


def _country_or_null(value):
    text = str(value or "").strip()
    if (
        not text
        or text.casefold() in {"worldwide", "europe/other", "europe", "north america", "asia", "remote", "unknown", "none", "null", "nan", "n/a"}
        or any(marker in text.casefold() for marker in ("remote", "hybrid", "onsite", "on-site"))
        or "(" in text
        or ")" in text
    ):
        return None
    return text


def build_udfs():
    title_mapping, skills_dictionary = load_dictionaries()

    def clean_html(value):
        if value is None or not str(value).strip():
            return None
        text = re.sub(r"<[^>]+>", " ", str(value))
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text or None

    def work_mode(location, remote):
        text = str(location or "").casefold()
        if _remote_flag(remote) or "remote" in text:
            return "Remote"
        if "hybrid" in text:
            return "Hybrid"
        if "onsite" in text or "on-site" in text:
            return "Onsite"
        return None

    def normalize_role(value):
        return normalize_title(value, title_mapping)

    def extract_from_description(value):
        return extract_skills(value, skills_dictionary)

    def normalize_tags(value):
        return normalize_source_tags(value, skills_dictionary)

    title_udf = udf(normalize_role, StringType())
    skills_udf = udf(extract_from_description, ArrayType(StringType()))
    tags_udf = udf(normalize_tags, ArrayType(StringType()))
    return {
        "clean_html": udf(clean_html, StringType()),
        "norm_title": title_udf,
        "extract_skills": skills_udf,
        "normalize_tags": tags_udf,
        "extract_work_mode": udf(work_mode, StringType()),
        "remote_bool": udf(_remote_flag, BooleanType()),
        "valid_country": udf(_country_or_null, StringType()),
        "stable_job_id": udf(stable_job_id, StringType()),
    }


def _historical_frame(spark, udfs):
    path = os.path.join(BRONZE_HIST_DIR, "*.json")
    raw = spark.read.option("multiline", "true").json(path)
    columns = set(raw.columns)
    title = _source_column(columns, ("job_title", "title"), None)
    company = _source_column(columns, ("company_name", "job_company_name", "company"), None)
    location = _source_column(columns, ("job_location", "location"), None)
    country = _source_column(columns, ("job_country", "country"), None)
    posted = _source_column(columns, ("job_posted_date", "posted_at"), None)
    description = _source_column(columns, ("job_description", "description"), None)
    source_tags = _source_column(columns, ("job_skills", "tags"), None)
    source = _source_column(columns, ("source",), "kaggle_historical_archive")
    collected = _source_column(columns, ("collected_at",), None)
    ingestion = _source_column(columns, ("ingestion_id",), None)
    source_url = _source_column(columns, ("source_url", "url"), None)
    raw_checksum = _source_column(columns, ("raw_checksum",), None)
    raw_columns = sorted(name for name in columns if name not in {"job_id", "ingestion_id", "collected_at", "market", "source"})
    fallback_checksum = sha2(to_json(struct(*[col(name) for name in raw_columns])), 256)
    # Historical archive has no native job_id. Ignore legacy sequential IDs and
    # fall back to a content checksum whenever a stable source ID is absent.
    source_record_id = coalesce(
        _source_column(columns, ("source_record_id",), None).cast("string"),
        raw_checksum.cast("string"),
        fallback_checksum,
    )
    return raw.select(
        source.cast("string").alias("source"),
        source_record_id.cast("string").alias("source_record_id"),
        coalesce(raw_checksum.cast("string"), fallback_checksum).alias("raw_checksum"),
        source_url.cast("string").alias("source_url"),
        ingestion.cast("string").alias("ingestion_id"),
        collected.cast("string").alias("collected_at_raw"),
        title.cast("string").alias("title"), company.cast("string").alias("company"),
        location.cast("string").alias("location"), udfs["valid_country"](country).alias("country"),
        lit(None).cast("string").alias("city"),
        description.cast("string").alias("raw_description"),
        source_tags.cast("string").alias("source_tags_raw"),
        posted.cast("string").alias("posted_at_raw"),
        _source_column(columns, ("market",), "GLOBAL").cast("string").alias("market"),
        lit(None).cast("integer").alias("salary_min"),
        lit(None).cast("integer").alias("salary_max"),
        lit(None).cast("string").alias("currency"),
        udfs["remote_bool"](_source_column(columns, ("job_work_from_home", "remote"), False)).alias("is_remote"),
        lit(True).alias("is_historical"),
    )


def _fresh_frame(spark, udfs):
    path = os.path.join(BRONZE_FRESH_DIR, "*.json")
    raw = spark.read.option("multiline", "true").json(path)
    columns = set(raw.columns)
    source = _source_column(columns, ("source",), "")
    source_id = _source_column(columns, ("source_record_id", "raw_id", "id"), None).cast("string")
    title = _source_column(columns, ("title", "job_title"), None)
    company = _source_column(columns, ("company", "company_name"), None)
    location = _source_column(columns, ("location", "candidate_required_location"), None)
    description = _source_column(columns, ("description", "job_description"), None)
    tags = _source_column(columns, ("tags", "job_skills"), None)
    posted = _source_column(columns, ("posted_at", "publication_date"), None)
    collected = _source_column(columns, ("collected_at",), None)
    checksum = _source_column(columns, ("raw_checksum",), None)
    raw_columns = sorted(name for name in columns if name not in {"ingestion_id", "collected_at", "market", "source"})
    fallback_checksum = sha2(to_json(struct(*[col(name) for name in raw_columns])), 256)
    source_id = coalesce(source_id, checksum.cast("string"), fallback_checksum)
    return raw.select(
        source.cast("string").alias("source"), source_id.alias("source_record_id"),
        coalesce(checksum.cast("string"), fallback_checksum).alias("raw_checksum"),
        _source_column(columns, ("source_url", "url"), None).cast("string").alias("source_url"),
        _source_column(columns, ("ingestion_id",), None).cast("string").alias("ingestion_id"),
        collected.cast("string").alias("collected_at_raw"),
        title.cast("string").alias("title"), company.cast("string").alias("company"),
        location.cast("string").alias("location"),
        udfs["valid_country"](_source_column(columns, ("country",), None)).alias("country"),
        lit(None).cast("string").alias("city"),
        description.cast("string").alias("raw_description"),
        tags.cast("string").alias("source_tags_raw"), posted.cast("string").alias("posted_at_raw"),
        _source_column(columns, ("market",), "GLOBAL").cast("string").alias("market"),
        lit(None).cast("integer").alias("salary_min"),
        lit(None).cast("integer").alias("salary_max"),
        _source_column(columns, ("currency",), None).cast("string").alias("currency"),
        udfs["remote_bool"](_source_column(columns, ("remote", "job_work_from_home"), False)).alias("is_remote"),
        lit(False).alias("is_historical"),
    )


def _run_etl(spark, output_dirs):
    udfs = build_udfs()
    frames = []
    if os.path.exists(BRONZE_HIST_DIR) and os.listdir(BRONZE_HIST_DIR):
        frames.append(_historical_frame(spark, udfs))
    if os.path.exists(BRONZE_FRESH_DIR) and os.listdir(BRONZE_FRESH_DIR):
        frames.append(_fresh_frame(spark, udfs))
    if not frames:
        print("[ETL] No data found in Bronze Layer.")
        return False

    combined = frames[0]
    for frame in frames[1:]:
        combined = combined.unionByName(frame)

    processed = (combined
        .withColumn("source", when(
            col("source").isNull() | (trim(col("source")) == ""),
            when(col("is_historical"), lit("kaggle_historical_archive")).otherwise(lit(None).cast("string")),
        ).otherwise(trim(col("source"))))
        .withColumn("market", when(
            col("market").isNull() | (trim(col("market")) == ""), lit("GLOBAL")
        ).otherwise(trim(col("market"))))
        .withColumn("clean_description", udfs["clean_html"](col("raw_description")))
        .withColumn("description", col("clean_description"))
        .withColumn("experience_level", lit(None).cast("string"))
        .withColumn("normalized_title", udfs["norm_title"](col("title")))
        .withColumn("work_mode", udfs["extract_work_mode"](col("location"), col("is_remote")))
        .withColumn("posted_at", try_to_timestamp(col("posted_at_raw")))
        .withColumn("collected_at", try_to_timestamp(col("collected_at_raw")))
        .withColumn("description_origin", when(col("clean_description").isNull(), lit("missing")).otherwise(lit("original_jd")))
        .withColumn("skills_origin", when(col("is_historical"),
            when(col("source_tags_raw").isNull() | (trim(col("source_tags_raw")) == ""), lit("missing"))
            .otherwise(lit("source_tags"))).otherwise(
            when(col("clean_description").isNotNull(), lit("extracted_from_jd"))
            .when(col("source_tags_raw").isNull() | (trim(col("source_tags_raw")) == ""), lit("missing"))
            .otherwise(lit("source_tags"))))
        .withColumn("skills", when(col("is_historical") | col("clean_description").isNull(),
            udfs["normalize_tags"](col("source_tags_raw")))
            .otherwise(udfs["extract_skills"](col("clean_description"))))
        .withColumn("job_id", udfs["stable_job_id"](col("source"), col("source_record_id")))
        .withColumn("normalized_company", regexp_replace(lower(trim(coalesce(col("company"), lit("")))), r"\s+", " "))
        .withColumn("normalized_job_title", regexp_replace(lower(trim(coalesce(col("title"), lit("")))), r"\s+", " "))
        .withColumn("normalized_location", regexp_replace(lower(trim(coalesce(col("location"), lit("")))), r"\s+", " "))
        .withColumn("job_hash", sha2(concat_ws("|", col("normalized_company"), col("normalized_job_title"),
            col("normalized_location"), date_format(col("posted_at"), "yyyy-MM-dd")), 256)))

    invalid = processed.filter(
        col("posted_at").isNull()
        | col("title").isNull()
        | (trim(col("title")) == "")
        | col("source_record_id").isNull()
        | (trim(col("source_record_id")) == "")
        | col("source").isNull()
        | (trim(col("source")) == "")
    ).withColumn(
        "quarantine_reason",
        when(col("posted_at").isNull(), lit("missing_or_invalid_posted_at"))
        .when(col("title").isNull() | (trim(col("title")) == ""), lit("missing_title"))
        .when(col("source_record_id").isNull() | (trim(col("source_record_id")) == ""), lit("missing_source_record_id"))
        .otherwise(lit("missing_source")),
    )
    invalid_count = invalid.count()
    invalid.write.mode("errorifexists").parquet(output_dirs["quarantine"])
    valid = processed.filter(
        col("posted_at").isNotNull()
        & col("title").isNotNull()
        & (trim(col("title")) != "")
        & col("source_record_id").isNotNull()
        & (trim(col("source_record_id")) != "")
        & col("source").isNotNull()
        & (trim(col("source")) != "")
    )

    survivor_window = Window.partitionBy("job_hash").orderBy(
        col("collected_at").desc_nulls_last(), col("job_id").asc())
    survivors = (valid.withColumn("_survivor_rank", row_number().over(survivor_window))
                 .filter(col("_survivor_rank") == 1).drop("_survivor_rank"))

    silver_with_parts = (survivors
        .withColumn("year", year(col("posted_at")))
        .withColumn("month", month(col("posted_at"))))
    silver = silver_with_parts.select(*UNIFIED_JOB_FIELDS, "year", "month")
    expected_silver_columns = UNIFIED_JOB_FIELDS + ["year", "month"]
    if silver.columns != expected_silver_columns:
        raise ValueError(f"Silver schema mismatch: expected {expected_silver_columns}, got {silver.columns}")
    provenance = silver_with_parts.select(
        "job_id", "source", "source_record_id", "source_url", "description_origin",
        "skills_origin", lit(TAXONOMY_VERSION).alias("taxonomy_version"), "ingestion_id", "collected_at",
        "raw_checksum", lit("posted_at_valid").alias("timestamp_quality"))

    silver.write.mode("errorifexists").partitionBy("year", "month").parquet(output_dirs["silver"])
    provenance.write.mode("errorifexists").parquet(output_dirs["provenance"])
    print(f"[ETL] Wrote {silver.count():,} Silver survivors; quarantined {invalid_count:,} rows with invalid posted_at.")
    return True


def run_etl(
    silver_dir=SILVER_GLOBAL_DIR,
    provenance_dir=PROVENANCE_GLOBAL_DIR,
    quarantine_dir=QUARANTINE_GLOBAL_DIR,
    replace_existing=False,
):
    targets = {
        "silver": os.path.abspath(silver_dir),
        "provenance": os.path.abspath(provenance_dir),
        "quarantine": os.path.abspath(quarantine_dir),
    }
    if len(set(targets.values())) != len(targets):
        raise ValueError("Silver, provenance, and quarantine output paths must be distinct.")
    paths = list(targets.values())
    for index, path in enumerate(paths):
        for other in paths[index + 1:]:
            try:
                common = os.path.commonpath([path, other])
            except ValueError:  # Different Windows drives cannot overlap.
                continue
            if common in {path, other}:
                raise ValueError("Silver, provenance, and quarantine output paths cannot contain one another.")

    existing = [path for path in targets.values() if os.path.lexists(path)]
    if existing and not replace_existing:
        raise FileExistsError(
            "Refusing to replace existing ETL outputs. Choose temporary output directories, "
            "or pass --replace-existing to replace them while retaining backups: "
            + ", ".join(existing)
        )

    run_id = uuid.uuid4().hex
    staged_paths = {
        name: f"{target}.staging-{run_id}" for name, target in targets.items()
    }
    staged_outputs = {
        staged_paths[name]: target for name, target in targets.items()
    }
    for stage in staged_paths.values():
        if os.path.lexists(stage):
            raise FileExistsError(f"ETL staging path already exists: {stage}")
        os.makedirs(os.path.dirname(stage), exist_ok=True)

    spark = create_spark_session()
    try:
        written = _run_etl(spark, staged_paths)
        if written:
            _promote_staged_outputs(staged_outputs, run_id, replace_existing)
    finally:
        try:
            spark.stop()
        finally:
            for stage in staged_paths.values():
                _remove_path(stage)


def _parse_args():
    parser = argparse.ArgumentParser(description="Build Bronze-to-Silver job data with provenance.")
    parser.add_argument("--silver-dir", default=SILVER_GLOBAL_DIR, help="Silver Parquet output directory")
    parser.add_argument("--provenance-dir", default=PROVENANCE_GLOBAL_DIR, help="Provenance Parquet output directory")
    parser.add_argument("--quarantine-dir", default=QUARANTINE_GLOBAL_DIR, help="Quarantine Parquet output directory")
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Replace existing outputs after staging; previous outputs are retained as run-specific backups.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_etl(
        silver_dir=args.silver_dir,
        provenance_dir=args.provenance_dir,
        quarantine_dir=args.quarantine_dir,
        replace_existing=args.replace_existing,
    )
