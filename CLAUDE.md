# SMOL Project Guidelines

## What is this project?

SMOL (Spectra and Matrices Of Little graphs) is a database of all small connected simple undirected graphs with their spectral properties. It's designed for spectral graph theory research.

## Key concepts

- **graph6**: A compact string encoding for graphs used by nauty/geng
- **Non-backtracking matrix**: The Hashimoto matrix B, indexed by directed edges
- **Non-backtracking Laplacian**: I - D⁻¹B, random walk on directed edges
- **Spectral hash**: A 16-character hash of sorted eigenvalues for co-spectral detection

## Architecture

- **Database**: PostgreSQL (Supabase in production)
- **API**: FastAPI with content negotiation (JSON + HTML)
- **Frontend**: HTMX + Alpine.js (planned)
- **Hosting**: Fly.io (API), Netlify (frontend)

## Commands

```bash
# Run tests
uv run pytest tests/ -v

# Generate graphs
uv run python scripts/generate.py --n 1 --n 8

# Run API locally
uv run uvicorn api.main:app --reload
```

## API Endpoints

```
GET /graphs/{graph6}         Look up a graph + cospectral mates
GET /graphs?n=7&regular=true Query/filter graphs
GET /compare?graphs=D?{,DEo  Compare multiple graphs
GET /stats                   Database statistics
```

Content negotiation: Returns JSON by default, HTML when `Accept: text/html`.

## Website Structure

```
/           Search + results (home page)
/graph/{g6} Graph detail + cospectral mates
/compare    Compare 2+ graphs
/glossary   Terminology explanations
/about      What is SMOL, stats, API, citation
```

See `doc/wireframes.md` for detailed wireframes.

## Dependencies

- **Python**: numpy, scipy, networkx, psycopg2, fastapi, uvicorn, jinja2
- **System**: nauty (provides `geng` for graph enumeration), PostgreSQL

## Database

- Connection: `DATABASE_URL` env var or `dbname=smol` (local)
- Schema: `sql/schema.sql`

## Code organization

- `api/`: FastAPI backend with HTMX templates
- `db/`: Core library (matrices, spectra, metadata)
- `doc/`: Documentation and wireframes
- `scripts/`: Generation pipeline
- `sql/`: Database schema
- `tests/`: Pytest tests
