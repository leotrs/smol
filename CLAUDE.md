# SMOL Project Guidelines

## What is this project?

SMOL (Spectra and Matrices Of Little graphs) is a database of all small simple undirected graphs (up to 10 vertices, ~12M graphs) with their spectral properties. It's designed for spectral graph theory research.

## Key concepts

- **graph6**: A compact string encoding for graphs used by nauty/geng
- **Non-backtracking matrix**: The Hashimoto matrix B, indexed by directed edges
- **Non-backtracking Laplacian**: I - D⁻¹B, random walk on directed edges
- **Spectral hash**: A 16-character hash of sorted eigenvalues for cospectral detection
- **Cospectral family**: Graphs sharing the same spectrum for a given matrix type
- **Tags**: Named graph detection (complete, cycle, path, star, wheel, etc.)

## Graph Properties

Each graph stores:

**Structural properties:**
- `is_bipartite`, `is_planar`, `is_regular` (boolean flags)
- `diameter`, `girth`, `radius` (integer, nullable)
- `min_degree`, `max_degree`, `triangle_count`
- `clique_number`, `chromatic_number` (greedy upper bound)

**Network science properties:**
- `algebraic_connectivity` (second smallest Laplacian eigenvalue)
- `global_clustering` (transitivity)
- `avg_local_clustering` (average of local clustering coefficients)
- `avg_path_length` (only for connected graphs)
- `assortativity` (degree assortativity coefficient)

**Distributions (sorted arrays):**
- `degree_sequence` (sorted descending)
- `betweenness_centrality`, `closeness_centrality`, `eigenvector_centrality`

## Tech Stack

- **Backend**: FastAPI with Jinja2 templates
- **Frontend**: HTMX + Alpine.js, Pico CSS (coral accent #E85A4F), D3.js visualizations
- **Database**: PostgreSQL (local dev) or SQLite (production on Fly.io)
- **Async**: aiosqlite for non-blocking SQLite queries
- **Math**: MathJax for LaTeX rendering in glossary
- **Deployment**: Fly.io with persistent volume for SQLite

## Commands

```bash
just test                # Run all tests
just test-cov            # Run tests with coverage
just generate            # Generate graphs (n=1 to n=8)
just generate 9 10       # Generate graphs for specific range
just compute-properties  # Compute network science properties
just refresh-stats       # Refresh statistics cache
just serve               # Run API locally
just db-stats            # Show graph counts by n
just check-properties    # Check pending property computations

# Generation (parallel, resumable)
python scripts/generate.py --n 10 --workers 6  # 6 parallel workers
python scripts/generate.py --n 10 --resume     # Resume interrupted run

# Tags
python scripts/compute_tags.py                 # Backfill tags for all graphs

# Cospectrality analysis
python scripts/cospectral_tables.py            # Generate cospectrality tables
python scripts/cospectral_tables.py --max-n 9  # Limit to n <= 9

# Deployment
just deploy-db                                 # Export PG to SQLite and deploy to Fly.io
just deploy-db --max-n 9                       # Deploy only graphs with n <= 9
just deploy-db --skip-export                   # Skip export, use existing smol.db
```

## API Endpoints

```
GET /                    Home page (search interface)
GET /graph/{graph6}      Graph detail + cospectral mates + tags
GET /graphs              Query/filter graphs (HTMX partial or JSON)
GET /compare?graphs=...  Compare multiple graphs
GET /similar/{graph6}    Find spectrally similar graphs (L2 distance)
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
- Cospectral pairs pre-computed in `cospectral_mates` table for fast lookup
- Database contains ALL graphs (connected and disconnected)

## Known discrepancy with reference paper

Our NB/NBL cospectral counts differ slightly from published tables. Closest match:

**NB (Ã):** "All graphs" matches exactly at n=4, diverges at larger n (+4528 at n=9)

**NBL (L̃):** "All graphs" matches exactly at n=4,5, diverges slightly (+296 at n=9)

The source of divergence is unidentified. Possibilities: precision differences (we use 8 decimals), different graph sets, or errors in the reference.

## Code organization

- `api/` - FastAPI backend with templates
  - `database.py` - Async database layer (supports PostgreSQL and SQLite)
  - `main.py` - API routes with request logging
- `db/` - Core library (matrices, spectra, metadata)
  - `tags.py` - Named graph detection (complete, cycle, path, star, etc.)
- `scripts/` - Generation pipeline and stats refresh
  - `generate.py` - Parallel graph generation (multiprocessing, resumable)
  - `compute_tags.py` - Backfill tags for existing graphs
- `sql/` - Database schema (PostgreSQL and SQLite versions)
- `tests/` - Pytest tests (183 tests)
