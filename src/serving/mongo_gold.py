"""Publish one verified Gold run to MongoDB for the dashboard."""

import argparse
import hashlib
import json
import os
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from dashboard.data import AUDIT, ROOT, TABLE_KEYS, GoldError, GoldRun, load_gold

MONGO_AUDIT = Path("docs/data/mongo_serving_audit.json")


def _native(value):
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _native(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_native(item) for item in value]
    if hasattr(value, "item"):
        return _native(value.item())
    if not isinstance(value, (dict, list, tuple)) and pd.isna(value):
        return None
    return value


def table_documents(frame, keys):
    """Stable row IDs and digest, independent of Parquet file order."""
    documents = []
    for raw in frame.to_dict(orient="records"):
        row = _native(raw)
        identity = json.dumps([row[key] for key in keys], ensure_ascii=False, separators=(",", ":"))
        documents.append({"_id": identity, "row": row})
    documents.sort(key=lambda document: document["_id"])
    digest = hashlib.sha256()
    for document in documents:
        digest.update(json.dumps(document, ensure_ascii=False, sort_keys=True,
                                 separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n")
    return documents, digest.hexdigest()


def publish_gold(root=ROOT, audit_path=None, mongo_uri=None, db_name="jobscope", evidence_path=None):
    """Publish only after all five collections have been read back and verified."""
    run = load_gold(root, audit_path)
    client = MongoClient(mongo_uri or os.environ.get("JOB_MONGO_URI", "mongodb://127.0.0.1:27017"),
                         serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    database = client[db_name]
    run_id = run.manifest["run_id"]
    existing = database.gold_runs.find_one({"_id": run_id})
    if existing:
        if existing.get("manifest_sha256") != run.manifest_sha256:
            raise GoldError("Existing MongoDB run has a different manifest hash")
        for table, keys in TABLE_KEYS.items():
            documents, digest = table_documents(run.tables[table], keys)
            meta = existing["tables"][table]
            readback = list(database[meta["collection"]].find({}, {"_id": 1, "row": 1}).sort("_id", 1))
            if readback != documents or meta["sha256"] != digest or meta["rows"] != len(documents):
                raise GoldError(f"Existing MongoDB table differs from verified Parquet: {table}")
        table_meta = existing["tables"]
        client.close()
        evidence = {"schema_version": 1, "run_id": run_id,
                    "manifest_sha256": run.manifest_sha256, "tables": table_meta}
        if evidence_path:
            path = Path(evidence_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(evidence, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return evidence
    names = {name: f"gold_{run_id}_{name}" for name in TABLE_KEYS}
    if any(name in database.list_collection_names() for name in names.values()):
        raise FileExistsError("A Gold collection already exists without a published run record")
    published = []
    table_meta = {}
    try:
        for table, keys in TABLE_KEYS.items():
            name = names[table]
            documents, digest = table_documents(run.tables[table], keys)
            published.append(name)
            if documents:
                for offset in range(0, len(documents), 500):
                    database[name].insert_many(documents[offset:offset + 500], ordered=True)
            else:
                database.create_collection(name)
            readback = list(database[name].find({}, {"_id": 1, "row": 1}).sort("_id", 1))
            if readback != documents:
                raise AssertionError(f"MongoDB round-trip mismatch: {table}")
            table_meta[table] = {"collection": name, "rows": len(documents), "sha256": digest}
        database.gold_runs.insert_one({
            "_id": run_id,
            "manifest_sha256": run.manifest_sha256,
            "manifest": run.manifest,
            "tables": table_meta,
        })
    except Exception:
        for name in published:
            database[name].drop()
        raise
    finally:
        client.close()
    evidence = {"schema_version": 1, "run_id": run_id,
                "manifest_sha256": run.manifest_sha256, "tables": table_meta}
    if evidence_path:
        path = Path(evidence_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(evidence, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return evidence


def load_gold_mongo(root=ROOT, audit_path=None, mongo_uri=None, db_name="jobscope", evidence_path=None):
    """Read the audit-pinned MongoDB run; local Parquet is not required."""
    root = Path(root).resolve()
    try:
        audit = json.loads(Path(audit_path or root / AUDIT).read_text(encoding="utf-8"))
        run_id = audit["run_id"]
        if not isinstance(run_id, str) or not all(char.isalnum() or char in "-_" for char in run_id):
            raise GoldError("Invalid Gold run ID")
        evidence = json.loads(Path(evidence_path or root / MONGO_AUDIT).read_text(encoding="utf-8"))
        if evidence.get("schema_version") != 1 or evidence.get("run_id") != run_id or \
                evidence.get("manifest_sha256") != audit["manifest_sha256"]:
            raise GoldError("MongoDB serving audit does not match pinned Gold run")
        client = MongoClient(mongo_uri or os.environ.get("JOB_MONGO_URI", "mongodb://127.0.0.1:27017"),
                             serverSelectionTimeoutMS=5000)
        try:
            client.admin.command("ping")
            database = client[db_name]
            published = database.gold_runs.find_one({"_id": run_id})
            if not published or published.get("manifest_sha256") != audit["manifest_sha256"]:
                raise GoldError("MongoDB run does not match pinned Gold audit")
            if published.get("tables") != evidence.get("tables"):
                raise GoldError("MongoDB tables do not match serving audit")
            manifest = published["manifest"]
            reconstructed = (json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
            canonical_hashes = {hashlib.sha256(candidate).hexdigest() for candidate in
                                (reconstructed, reconstructed.replace(b"\n", b"\r\n"))}
            if audit["manifest_sha256"] not in canonical_hashes:
                raise GoldError("MongoDB manifest content does not match pinned SHA-256")
            for field in ("run_id", "analysis_type", "taxonomy_version", "predictive_gate"):
                if manifest.get(field) != audit.get(field):
                    raise GoldError(f"MongoDB manifest/audit mismatch: {field}")
            if manifest.get("status") != "completed" or manifest.get("analysis_type") != "observed_descriptive_only":
                raise GoldError("MongoDB run is not a completed descriptive Gold run")
            tables = {}
            for table, keys in TABLE_KEYS.items():
                meta = published["tables"][table]
                if meta["rows"] != audit["outputs"][table]["rows"]:
                    raise GoldError(f"MongoDB/audit row count mismatch: {table}")
                documents = list(database[meta["collection"]].find({}, {"_id": 1, "row": 1}).sort("_id", 1))
                frame = pd.DataFrame([document["row"] for document in documents])
                expected, digest = table_documents(frame, keys)
                if len(documents) != meta["rows"] or documents != expected or digest != meta["sha256"]:
                    raise GoldError(f"MongoDB table integrity mismatch: {table}")
                tables[table] = frame
            return GoldRun(manifest, tables, published["manifest_sha256"])
        finally:
            client.close()
    except GoldError:
        raise
    except (OSError, ValueError, KeyError, TypeError, PyMongoError) as exc:
        raise GoldError(f"Cannot load verified MongoDB Gold: {exc}") from exc


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--audit-json")
    parser.add_argument("--mongo-uri", default=os.environ.get("JOB_MONGO_URI", "mongodb://127.0.0.1:27017"))
    parser.add_argument("--db", default=os.environ.get("JOB_MONGO_DB", "jobscope"))
    parser.add_argument("--evidence-json", default=str(ROOT / MONGO_AUDIT))
    args = parser.parse_args()
    print(json.dumps(publish_gold(args.root, args.audit_json, args.mongo_uri, args.db,
                                  args.evidence_json), ensure_ascii=False))
