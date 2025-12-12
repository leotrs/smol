# SMOL Project Guidelines

## What is this project?

SMOL (Spectra and Matrices Of Little graphs) is a database of all small connected simple undirected graphs with their spectral properties. It's designed for spectral graph theory research.

## Key concepts

- **graph6**: A compact string encoding for graphs used by nauty/geng
- **Non-backtracking matrix**: The Hashimoto matrix B, indexed by directed edges
- **Non-backtracking Laplacian**: The normalized Laplacian of the non-backtracking graph (a novel matrix proposed by the project authors)
- **Spectral hash**: A 16-character hash of sorted eigenvalues for co-spectral detection

## Commands

```bash
# Run tests
uv run pytest tests/ -v

# Generate graphs (dry run)
uv run python scripts/generate.py --n 1 --n 8 --dry-run

# Generate and insert into database
uv run python scripts/generate.py --n 1 --n 8
```

## Dependencies

- **Python**: numpy, scipy, networkx, psycopg2
- **System**: nauty (provides `geng` for graph enumeration), PostgreSQL

## Database

- Name: `smol`
- Connection: `SMOL_DB_URL` env var or `postgresql://localhost/smol`
- Schema: `sql/schema.sql`

## Code organization

- `db/matrices.py`: Compute adjacency, Laplacian, non-backtracking, NB-Laplacian matrices
- `db/spectrum.py`: Compute eigenvalues and spectral hashes
- `db/metadata.py`: Compute graph properties (bipartite, planar, diameter, etc.)
- `db/graph_data.py`: `GraphRecord` dataclass and `process_graph()` function
- `db/database.py`: PostgreSQL insert/query operations
- `scripts/generate.py`: Main generation pipeline using geng
