# SMOL Project Guidelines

## What is this project?

SMOL (Spectra and Matrices Of Little graphs) is a database of all small connected simple undirected graphs (up to 10 vertices, ~12M graphs) with their spectral properties. It's designed for spectral graph theory research.

## Key concepts

- **graph6**: A compact string encoding for graphs used by nauty/geng
- **Non-backtracking matrix**: The Hashimoto matrix B, indexed by directed edges
- **Non-backtracking Laplacian**: I - D⁻¹B, random walk on directed edges
- **Spectral hash**: A 16-character hash of sorted eigenvalues for cospectral detection
- **Cospectral family**: Graphs sharing the same spectrum for a given matrix type

## Tech Stack

- **Backend**: FastAPI with Jinja2 templates
- **Frontend**: HTMX + Alpine.js, Pico CSS (coral accent #E85A4F), D3.js visualizations
- **Database**: PostgreSQL
- **Math**: MathJax for LaTeX rendering in glossary

## Commands

```bash
# Run tests
uv run pytest tests/ -v

# Generate graphs (n=1 to n=8)
uv run python scripts/generate.py --n-min 1 --n-max 8

# Refresh statistics cache
uv run python scripts/refresh_stats.py

# Run API locally
uv run uvicorn api.main:app --reload
```

## API Endpoints

```
GET /                    Home page (search interface)
GET /graph/{graph6}      Graph detail + cospectral mates
GET /graphs              Query/filter graphs (HTMX partial or JSON)
GET /compare?graphs=...  Compare multiple graphs
GET /random              Redirect to random graph
GET /random/cospectral   Redirect to random cospectral family
GET /glossary            Terminology with MathJax
GET /about               Stats, API docs, citation
GET /stats               Database statistics (JSON)
```

Content negotiation: Returns JSON by default, HTML for browser/HTMX requests.

## Website Structure

```
/              Search with tabs (Lookup / Search), results via HTMX
/graph/{g6}    Graph detail: viz, properties, cospectral mates, spectra
/compare       Side-by-side comparison with D3 visualizations
/glossary      Terms and matrix definitions (uses MathJax)
/about         Database stats, API reference, citation, references
```

Footer on all pages has "Random graph" and "Random cospectral family" links.

## Templates

- `base.html` - Layout, Pico CSS, custom styles, header nav, footer
- `home.html` - Alpine.js tabs for Lookup/Search, HTMX form submission
- `graph_detail.html` - D3 force-directed graph, drag-enabled
- `graph_list.html` - HTMX partial for search results
- `compare.html` - Grid of D3 visualizations, properties table
- `glossary.html` - Definition lists with MathJax
- `about.html` - Stats from cache, API docs

## Database

- Connection: `DATABASE_URL` env var or `dbname=smol` (local)
- Schema: `sql/schema.sql`
- Stats cached in `stats_cache` table (refresh with `scripts/refresh_stats.py`)

## Code organization

- `api/` - FastAPI backend with templates
- `db/` - Core library (matrices, spectra, metadata)
- `scripts/` - Generation pipeline and stats refresh
- `sql/` - Database schema
- `tests/` - Pytest tests
