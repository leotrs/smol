# SMOL Deployment Strategy

## Overview

Deploy SMOL as a FastAPI application with SQLite on Fly.io.

**Phase 1 (current):** Deploy with n≤9 (~288K graphs, ~500MB-1GB DB), test, monitor costs.
**Phase 2 (later):** If costs acceptable, add n=10 (~12M graphs, ~35GB DB).

## Architecture

```
┌─────────────────────────────────┐
│         Fly.io Machine          │
│  ┌───────────┐  ┌────────────┐  │
│  │  FastAPI  │──│  SQLite DB │  │
│  │  uvicorn  │  │  (volume)  │  │
│  └───────────┘  └────────────┘  │
└─────────────────────────────────┘
           │
    Fly.io Proxy (HTTPS)
           │
      smol.fly.dev
```

## Estimated Costs (n≤9)

| Item | Cost |
|------|------|
| Compute (shared-cpu-1x, 256MB) | ~$2/mo |
| Volume (1GB) | ~$0.15/mo |
| **Total** | **~$2-3/mo** |

For n=10 (~35GB): Volume cost increases to ~$5.25/mo, may need more RAM.

## Phase 1: Migrate to SQLite

### 1.1 Update database.py

Create `api/database_sqlite.py` or modify `api/database.py` to support SQLite:

```python
import sqlite3
import json
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///smol.db")

def get_connection():
    db_path = DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_graph(graph6: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM graphs WHERE graph6 = ?", (graph6,))
    row = cur.fetchone()
    conn.close()
    if row:
        return parse_row(row)
    return None

def parse_row(row):
    """Convert SQLite row to dict, parsing JSON fields."""
    d = dict(row)
    # Parse JSON array fields
    for field in ['adj_eigenvalues', 'lap_eigenvalues', 'nb_eigenvalues_re',
                  'nb_eigenvalues_im', 'nbl_eigenvalues_re', 'nbl_eigenvalues_im',
                  'degree_sequence', 'betweenness_centrality',
                  'closeness_centrality', 'eigenvector_centrality']:
        if d.get(field):
            d[field] = json.loads(d[field])
    # Convert integer booleans
    for field in ['is_bipartite', 'is_planar', 'is_regular']:
        d[field] = bool(d[field])
    return d
```

### 1.2 Create SQLite schema

```sql
-- sql/schema_sqlite.sql
CREATE TABLE IF NOT EXISTS graphs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    n                   INTEGER NOT NULL,
    m                   INTEGER NOT NULL,
    graph6              TEXT NOT NULL UNIQUE,

    adj_eigenvalues     TEXT NOT NULL,
    adj_spectral_hash   TEXT NOT NULL,
    lap_eigenvalues     TEXT NOT NULL,
    lap_spectral_hash   TEXT NOT NULL,
    nb_eigenvalues_re   TEXT NOT NULL,
    nb_eigenvalues_im   TEXT NOT NULL,
    nb_spectral_hash    TEXT NOT NULL,
    nbl_eigenvalues_re  TEXT NOT NULL,
    nbl_eigenvalues_im  TEXT NOT NULL,
    nbl_spectral_hash   TEXT NOT NULL,

    is_bipartite        INTEGER NOT NULL,
    is_planar           INTEGER NOT NULL,
    is_regular          INTEGER NOT NULL,
    diameter            INTEGER NOT NULL,
    radius              INTEGER NOT NULL,
    girth               INTEGER,
    min_degree          INTEGER NOT NULL,
    max_degree          INTEGER NOT NULL,
    triangle_count      INTEGER NOT NULL,
    clique_number       INTEGER,
    chromatic_number    INTEGER,

    algebraic_connectivity  REAL,
    global_clustering       REAL,
    avg_local_clustering    REAL,
    avg_path_length         REAL,
    assortativity           REAL,
    degree_sequence         TEXT,
    betweenness_centrality  TEXT,
    closeness_centrality    TEXT,
    eigenvector_centrality  TEXT
);

CREATE INDEX IF NOT EXISTS idx_n ON graphs(n);
CREATE INDEX IF NOT EXISTS idx_n_m ON graphs(n, m);
CREATE INDEX IF NOT EXISTS idx_graph6 ON graphs(graph6);
CREATE INDEX IF NOT EXISTS idx_adj_hash ON graphs(adj_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_lap_hash ON graphs(lap_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_nb_hash ON graphs(nb_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_nbl_hash ON graphs(nbl_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_bipartite ON graphs(is_bipartite);
CREATE INDEX IF NOT EXISTS idx_planar ON graphs(is_planar);
CREATE INDEX IF NOT EXISTS idx_regular ON graphs(is_regular);
CREATE INDEX IF NOT EXISTS idx_min_degree ON graphs(min_degree);

CREATE TABLE IF NOT EXISTS stats_cache (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### 1.3 Update generate.py for SQLite

Modify to output SQLite instead of PostgreSQL.

### 1.4 Generate data locally

```bash
# Create SQLite database with n=1-9
DATABASE_URL=sqlite:///smol.db uv run python scripts/generate_sqlite.py --n 1
DATABASE_URL=sqlite:///smol.db uv run python scripts/generate_sqlite.py --n 2
# ... through n=9

# Or export from existing PostgreSQL
uv run python scripts/export_to_sqlite.py
```

## Phase 2: Deploy to Fly.io

### 2.1 Install Fly CLI

```bash
# macOS
brew install flyctl

# Login
fly auth login
```

### 2.2 Create Dockerfile

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application
COPY api/ api/
COPY db/ db/

# Create data directory for SQLite
RUN mkdir -p /data

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.3 Create fly.toml

```toml
# fly.toml
app = "smol-graphs"
primary_region = "iad"  # or nearest to you

[build]

[env]
  DATABASE_URL = "sqlite:////data/smol.db"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = false
  auto_start_machines = true
  min_machines_running = 1

[mounts]
  source = "smol_data"
  destination = "/data"

[[vm]]
  memory = "512mb"
  cpu_kind = "shared"
  cpus = 1
```

### 2.4 Deploy

```bash
# Create app (name must be globally unique on Fly.io)
fly apps create smol-graphs-db

# Create persistent volume (2GB for n≤9, increase later for n=10)
fly volumes create smol_data --region iad --size 2 --app smol-graphs-db
# Answer 'y' to the single-volume warning (acceptable for research tool)

# Deploy
fly deploy

# Check status
fly status
fly logs
```

### 2.5 Upload database

```bash
# First, check if placeholder file exists and remove it
fly ssh console --app smol-graphs-db
rm -f /data/smol.db
exit

# Upload via SFTP (takes several minutes for 1GB file)
fly ssh sftp shell --app smol-graphs-db
put smol.db /data/smol.db
quit

# Restart to pick up the database
fly apps restart smol-graphs-db
```

### 2.6 Custom domain (optional)

```bash
# Add certificate
fly certs add smol.leotrs.com

# Point DNS CNAME to smol-graphs.fly.dev
```

## Phase 3: Testing

```bash
# Test endpoints
curl https://smol-graphs-db.fly.dev/
curl https://smol-graphs-db.fly.dev/graph/D%3F%7B
curl https://smol-graphs-db.fly.dev/stats
curl https://smol-graphs-db.fly.dev/random

# Monitor
fly logs --app smol-graphs-db
fly status --app smol-graphs-db
```

## Phase 4: Monitor Costs

After ~1 month, check billing:

```bash
fly billing
```

Or visit https://fly.io/dashboard → Billing

**Decision point:** If costs are acceptable (~$2-5/mo), proceed with n=10.

## Adding n=10 (Future)

When ready to add n=10:

1. Generate n=10 data locally (will take many hours)
2. Resize volume: `fly volumes extend smol_data --size 50`
3. Possibly increase RAM: edit `fly.toml` → `memory = "1gb"`
4. Upload new database file
5. Restart: `fly apps restart smol-graphs`

## Maintenance

### View logs
```bash
fly logs --app smol-graphs-db
```

### SSH into machine
```bash
fly ssh console --app smol-graphs-db
```

### Restart
```bash
fly apps restart smol-graphs-db
```

### Update application
```bash
git pull
fly deploy
```

### Backup database
```bash
fly ssh sftp shell --app smol-graphs-db
get /data/smol.db ./smol-backup.db
```

## Rollback Plan

If Fly.io costs too much or doesn't work out:
- Download SQLite file
- Deploy to Hetzner VPS (~$5/mo) using original strategy
- Or switch back to PostgreSQL + managed hosting

## Migration Checklist

- [ ] Create `api/database_sqlite.py`
- [ ] Create `sql/schema_sqlite.sql`
- [ ] Create `scripts/generate_sqlite.py` or `scripts/export_to_sqlite.py`
- [ ] Test locally with SQLite
- [ ] Generate n=1-9 data into SQLite
- [ ] Create `Dockerfile`
- [ ] Create `fly.toml`
- [ ] `fly apps create`
- [ ] `fly volumes create`
- [ ] `fly deploy`
- [ ] Upload database file
- [ ] Test production endpoints
- [ ] Monitor for 1 month
- [ ] Decide on n=10
