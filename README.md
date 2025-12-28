# SMOL: Spectra and Matrices Of Little Graphs

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A database of all small simple undirected graphs (connected and disconnected) with their spectral properties.

## What's in the database

For each simple undirected graph on up to 10 vertices (connected and disconnected), SMOL stores:

**Spectra for seven matrix types:**
- Adjacency matrix
- Laplacian matrix (symmetric normalized)
- Kirchhoff Laplacian (combinatorial)
- Signless Laplacian
- Non-backtracking (Hashimoto) matrix
- Non-backtracking Laplacian
- Distance matrix (connected graphs only)

**Structural metadata:**
- Vertex/edge counts
- Bipartiteness, planarity, regularity
- Diameter, radius, girth
- Degree sequence (min/max)
- Triangle count, clique number, chromatic number

**Network science properties:**
- Algebraic connectivity (Fiedler value)
- Global and local clustering coefficients
- Average path length, assortativity

**Tags (named graph detection):**
- Complete graphs, cycles, paths, stars, wheels
- Complete bipartite graphs, trees
- Petersen graph, Eulerian graphs, regular graphs

## Scale

| Vertices | Connected Graphs |
|----------|------------------|
| 1-8      | 12,113           |
| 9        | 261,080          |
| 10       | 11,716,571       |
| **Total**| **~12 million**  |

## Website

SMOL provides a web interface for exploring graphs:

- **Search**: Look up graphs by graph6 encoding or filter by properties
- **Graph detail**: View properties, spectra, and cospectral mates
- **Compare**: Side-by-side comparison of multiple graphs
- **Random**: Discover random graphs or cospectral families
- **Glossary**: Terminology and matrix definitions with MathJax

## API

All endpoints return JSON by default, HTML when accessed via browser.

**Live API:** https://smol-graphs-db.fly.dev

```bash
# Look up a graph by graph6
curl https://smol-graphs-db.fly.dev/graph/D%3F%7B

# Query graphs by properties
curl "https://smol-graphs-db.fly.dev/graphs?n=7&bipartite=true&limit=10"

# Compare multiple graphs
curl "https://smol-graphs-db.fly.dev/compare?graphs=D%3F%7B,DEo"

# Find spectrally similar graphs
curl "https://smol-graphs-db.fly.dev/similar/D%3F%7B?matrix=adj&limit=5"

# Random graph (redirects)
curl -L https://smol-graphs-db.fly.dev/random

# Random cospectral family (redirects)
curl -L https://smol-graphs-db.fly.dev/random/cospectral

# Database statistics
curl https://smol-graphs-db.fly.dev/stats

# Switching mechanisms for a graph
curl "https://smol-graphs-db.fly.dev/api/graph/GCQvBk/mechanisms"

# Mechanism coverage statistics
curl "https://smol-graphs-db.fly.dev/api/stats/mechanisms?n=8&matrix_type=adj"
```

**Switching Mechanisms:**

SMOL detects and stores switching mechanisms that explain why graphs are cospectral. Currently includes:
- **GM switching** (Godsil-McKay): Covers ~43% of adjacency-cospectral graphs at n=9

Graph detail pages show mechanism badges in a dedicated column for cospectral mates.

## Local Development

### Prerequisites

- Python 3.11+
- PostgreSQL
- nauty (provides `geng` for graph enumeration)

```bash
# macOS
brew install nauty postgresql
```

### Setup

```bash
uv sync
createdb smol
psql smol < sql/schema.sql
```

### Common commands

Uses [just](https://github.com/casey/just) for task running:

```bash
just serve              # Run API locally (http://localhost:8000)
just test               # Run tests
just test-cov           # Run tests with coverage
just generate           # Generate graphs n=1 to n=8
just generate 9 10      # Generate graphs for specific range
just compute-properties # Compute network science properties
just refresh-stats      # Refresh statistics cache
just db-stats           # Show graph counts by n
```

Or run commands directly:

```bash
uv run uvicorn api.main:app --reload
uv run pytest tests/ -v
```

## Configuration

Set `DATABASE_URL` to override the default PostgreSQL connection:

```bash
export DATABASE_URL="postgresql://user:pass@host:5432/smol"
```

Default: `dbname=smol` (local)

## Project Structure

```
smol/
├── api/                 # FastAPI backend
│   ├── main.py          # Routes with request logging
│   ├── database.py      # Async database layer (PG + SQLite)
│   ├── models.py        # Pydantic models
│   └── templates/       # Jinja2 + HTMX templates
├── db/                  # Core library
│   ├── matrices.py      # Matrix computations
│   ├── spectrum.py      # Eigenvalue computation
│   ├── metadata.py      # Graph properties
│   ├── graph_data.py    # GraphRecord processing
│   └── tags.py          # Named graph detection
├── scripts/
│   ├── generate.py          # Parallel graph generation (resumable)
│   ├── compute_properties.py # Network science properties
│   ├── compute_tags.py      # Backfill tags for graphs
│   └── refresh_stats.py     # Update statistics cache
├── sql/
│   ├── schema.sql           # PostgreSQL schema
│   └── schema_sqlite.sql    # SQLite schema
└── tests/                   # 305 tests
```

## Tech Stack

- **Backend**: FastAPI with Jinja2 templates
- **Frontend**: HTMX + Alpine.js, Pico CSS, D3.js for graph visualization
- **Database**: PostgreSQL (local dev) or SQLite with aiosqlite (production)
- **Deployment**: Fly.io with persistent volume
- **Math rendering**: MathJax

## Verification

Cospectral counts have been verified against published data:

| Matrix | Pairs | Status |
|--------|-------|--------|
| Adjacency | 699,403 | ✓ Perfect match |
| Laplacian (normalized) | 15,760 | ✓ Perfect match (n≥5) |
| Kirchhoff | 28,220 | ✓ Complete |
| Signless | 11,448 | ✓ Complete |
| Non-backtracking | 13,119,364 | Partial (matches for min_degree≥2) |
| NB Laplacian | 83,454 | ✓ Perfect match |
| Distance | 890,812 | ✓ Complete (connected graphs) |

All connected graphs have complete spectral data for all seven matrix types.

## License

MIT License. See [LICENSE](LICENSE) for details.
