#!/usr/bin/env python3
"""Bulk-load a SMOL SQLite file into PostgreSQL with COPY.

import_sqlite_to_pg.py inserts in batches while every index on `graphs` (46 of them) is
updated row by row, which runs at about 250 rows/s on 12.3M graphs. This version drops
the non-constraint indexes of each table, streams the rows through COPY, and recreates
the indexes once at the end. Columns are matched by name, as in import_sqlite_to_pg.py.

Usage:
    uv run python scripts/import_sqlite_to_pg_fast.py --sqlite smol_n10.db [--limit N]
"""

import argparse
import io
import json
import sqlite3
import sys
import time

import psycopg2

TABLES = ["graphs", "cospectral_families", "switching_mechanisms", "stats_cache"]
CHUNK = 50_000


def pg_columns(pg, table):
    with pg.cursor() as cur:
        cur.execute("""SELECT column_name, data_type FROM information_schema.columns
                       WHERE table_name = %s ORDER BY ordinal_position""", (table,))
        return cur.fetchall()


def copy_text(v, data_type):
    """One value in COPY text format."""
    if v is None:
        return r"\N"
    if data_type == "boolean":
        return "t" if v else "f"
    if data_type == "ARRAY":
        def elem(x):
            if x is None:
                return "NULL"
            if isinstance(x, str):
                return '"' + x.replace("\\", "\\\\").replace('"', '\\"') + '"'
            return repr(x)
        v = "{" + ",".join(elem(x) for x in json.loads(v)) + "}"
    s = str(v)
    return s.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")


def plain_indexes(pg, table):
    """(name, definition) of indexes that do not back a constraint."""
    with pg.cursor() as cur:
        cur.execute("""SELECT i.indexname, i.indexdef FROM pg_indexes i
                       WHERE i.tablename = %s AND NOT EXISTS (
                         SELECT 1 FROM pg_constraint c WHERE c.conname = i.indexname)""", (table,))
        return cur.fetchall()


def import_table(sl, pg, table, limit):
    pgcols = pg_columns(pg, table)
    slcols = {r[1] for r in sl.execute(f"PRAGMA table_info({table})")}
    cols = [(c, t) for c, t in pgcols if c in slcols]
    if not cols:
        print(f"{table}: no shared columns, skipping")
        return
    names = [c for c, _ in cols]
    idx = plain_indexes(pg, table)
    # Saved first, so a crash between DROP and the rebuild cannot lose an index.
    with open(f"pg_indexes_{table}.sql", "w") as f:
        f.writelines(d + ";\n" for _, d in idx)
    with pg.cursor() as cur:
        for name, _ in idx:
            cur.execute(f'DROP INDEX IF EXISTS "{name}"')
    pg.commit()
    total = sl.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    if limit:
        total = min(total, limit)
    rows = sl.execute(f"SELECT {', '.join(names)} FROM {table}" + (f" LIMIT {limit}" if limit else ""))
    t0, done = time.time(), 0
    with pg.cursor() as cur:
        while True:
            batch = rows.fetchmany(CHUNK)
            if not batch:
                break
            buf = io.StringIO()
            for r in batch:
                buf.write("\t".join(copy_text(v, t) for v, (_, t) in zip(r, cols)) + "\n")
            buf.seek(0)
            cur.copy_expert(f"COPY {table} ({', '.join(names)}) FROM STDIN", buf)
            done += len(batch)
            print(f"{time.strftime('%H:%M:%S')} {table}: {done}/{total} rows, {done / (time.time() - t0):.0f} rows/s", flush=True)
    pg.commit()
    t1 = time.time()
    with pg.cursor() as cur:
        for name, definition in idx:
            cur.execute(definition)
        if "id" in names:
            cur.execute("SELECT pg_get_serial_sequence(%s, 'id')", (table,))
            seq = cur.fetchone()[0]
            if seq:
                cur.execute(f"SELECT setval(%s, COALESCE((SELECT MAX(id) FROM {table}), 1))", (seq,))
    pg.commit()
    print(f"{time.strftime('%H:%M:%S')} {table}: {done} rows loaded, {len(idx)} indexes rebuilt in {time.time() - t1:.0f}s", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sqlite", required=True)
    ap.add_argument("--pg", default="dbname=smol")
    ap.add_argument("--limit", type=int, default=0, help="load only the first N rows per table (timing test)")
    ap.add_argument("--tables", nargs="*", default=TABLES)
    args = ap.parse_args()
    sl = sqlite3.connect(args.sqlite)
    pg = psycopg2.connect(args.pg)
    with pg.cursor() as cur:
        for table in reversed(TABLES):
            cur.execute(f"TRUNCATE {table} RESTART IDENTITY CASCADE")
    pg.commit()
    for table in args.tables:
        import_table(sl, pg, table, args.limit)
    sl.close()
    pg.close()


if __name__ == "__main__":
    sys.exit(main())
