"""SQLite storage for Skill Radar.

Two databases follow the Bronze/Silver/Gold layout:

    data/warehouse.db   Bronze (raw comments) + Silver (clean postings, skills, features). Large, local only.
    data/gold.db        Gold: small analytic tables that the dashboard reads. Tracked in git.

SQLite ships with Python, so the project needs no database server and no extra dependency.
"""

import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent / "data"
WAREHOUSE = DATA / "warehouse.db"
GOLD = DATA / "gold.db"


def connect(path, readonly=False):
    path = Path(path)
    if readonly:
        if not path.is_file():
            raise FileNotFoundError(path)
        conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
        conn.execute("PRAGMA journal_mode=DELETE")
    return conn


@contextmanager
def session(path, readonly=False):
    conn = connect(path, readonly)
    try:
        yield conn
        if not readonly:
            conn.commit()
    finally:
        conn.close()


def write_table(conn, name, frame, indexes=(), primary_key=None):
    """Replace table ``name`` with ``frame``; create the listed indexes (each a column or tuple of columns)."""
    conn.execute(f'DROP TABLE IF EXISTS "{name}"')
    frame = frame.copy()
    for column in frame.columns:                      # pandas string/bool/Period dtypes -> SQLite-friendly
        if str(frame[column].dtype).startswith("bool"):
            frame[column] = frame[column].astype("Int64")
        elif str(frame[column].dtype).startswith("period"):
            frame[column] = frame[column].astype(str)
    frame.to_sql(name, conn, index=False, chunksize=20000)
    for i, cols in enumerate(indexes):
        cols = [cols] if isinstance(cols, str) else list(cols)
        conn.execute(f'CREATE INDEX IF NOT EXISTS "ix_{name}_{i}" ON "{name}" ({", ".join(chr(34) + c + chr(34) for c in cols)})')
    return len(frame)


def read_sql(conn, sql, params=()):
    return pd.read_sql_query(sql, conn, params=params)


def tables(conn):
    return [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]


def has_table(conn, name):
    return name in tables(conn)


def kv_write(conn, name, mapping):
    """Store a flat key/value mapping as a two-column table (values as text)."""
    frame = pd.DataFrame({"key": list(mapping), "value": [str(v) for v in mapping.values()]})
    write_table(conn, name, frame)


def kv_read(conn, name):
    return dict(conn.execute(f'SELECT key, value FROM "{name}"').fetchall())


def ready(path):
    with closing(sqlite3.connect(path)) as conn:
        return bool(tables(conn))
