# SMOL: Spectra and Matrices Of Little Graphs

A database of all small connected graphs with their spectral properties.

## What's in the database

For each connected graph on up to 10 vertices, SMOL stores:

**Spectra for four matrices:**
- Adjacency matrix
- Laplacian matrix (symmetric normalized)
- Non-backtracking (Hashimoto) matrix
- Non-backtracking Laplacian

**Structural metadata:**
- Vertex/edge counts
- Bipartiteness, planarity, regularity
- Diameter, radius, girth
- Degree sequence (min/max)
- Triangle count

## Scale

| Vertices | Connected Graphs |
|----------|------------------|
| 1-8      | 12,113           |
| 9        | 261,080          |
| 10       | 11,716,571       |
| **Total**| **~12 million**  |

## API

SMOL provides a REST API for programmatic access:

```bash
# Look up a graph
curl https://smol.example.com/graphs/D%3F%7B

# Query graphs
curl "https://smol.example.com/graphs?n=7&bipartite=true&limit=10"

# Compare graphs
curl "https://smol.example.com/compare?graphs=D%3F%7B,DEo"

# Database stats
curl https://smol.example.com/stats
```

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

### Generate graphs

```bash
# Generate graphs for n=1 through n=8
uv run python scripts/generate.py --n 1 --n 8

# Dry run (process without inserting)
uv run python scripts/generate.py --n 6 --dry-run
```

### Run the API locally

```bash
uv run uvicorn api.main:app --reload
```

### Run tests

```bash
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
│   ├── main.py          # Routes and app
│   ├── database.py      # Database queries
│   ├── models.py        # Pydantic models
│   └── templates/       # HTML templates (HTMX)
├── db/                  # Core library
│   ├── matrices.py      # Matrix computations
│   ├── spectrum.py      # Eigenvalue computation
│   ├── metadata.py      # Graph properties
│   └── graph_data.py    # GraphRecord processing
├── doc/                 # Documentation
│   └── wireframes.md    # Website wireframes
├── scripts/
│   └── generate.py      # Generation pipeline
├── sql/
│   └── schema.sql       # Database schema
└── tests/
```
