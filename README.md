# SMOL: Spectra and Matrices Of Little Graphs

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A database of all small connected graphs with their spectral properties.

## What's in the database

For each connected graph on up to 10 vertices, SMOL stores:

**Spectra for four matrix types:**
- Adjacency matrix
- Laplacian matrix (symmetric normalized)
- Non-backtracking (Hashimoto) matrix
- Non-backtracking Laplacian

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
- Centrality distributions (betweenness, closeness, eigenvector)

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

```bash
# Look up a graph by graph6
curl https://smol.example.com/graph/D%3F%7B

# Query graphs by properties
curl "https://smol.example.com/graphs?n=7&bipartite=true&limit=10"

# Compare multiple graphs
curl "https://smol.example.com/compare?graphs=D%3F%7B,DEo"

# Random graph (redirects)
curl -L https://smol.example.com/random

# Random cospectral family (redirects)
curl -L https://smol.example.com/random/cospectral

# Database statistics
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
│   ├── main.py          # Routes and app
│   ├── database.py      # Database queries
│   ├── models.py        # Pydantic models
│   └── templates/       # Jinja2 + HTMX templates
│       ├── base.html    # Layout with Pico CSS
│       ├── home.html    # Search interface
│       ├── graph_detail.html
│       ├── graph_list.html
│       ├── compare.html
│       ├── glossary.html
│       └── about.html
├── db/                  # Core library
│   ├── matrices.py      # Matrix computations
│   ├── spectrum.py      # Eigenvalue computation
│   ├── metadata.py      # Graph properties
│   └── graph_data.py    # GraphRecord processing
├── scripts/
│   ├── generate.py          # Graph generation pipeline
│   ├── compute_properties.py # Network science properties
│   └── refresh_stats.py     # Update statistics cache
├── sql/
│   └── schema.sql           # Database schema
└── tests/
    ├── test_api.py          # API tests
    └── test_compute_properties.py
```

## Tech Stack

- **Backend**: FastAPI with Jinja2 templates
- **Frontend**: HTMX + Alpine.js, Pico CSS, D3.js for graph visualization
- **Database**: PostgreSQL
- **Math rendering**: MathJax

## License

MIT License. See [LICENSE](LICENSE) for details.
