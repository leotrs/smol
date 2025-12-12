# SMOL: Spectra and Matrices Of Little Graphs

A database of all small connected graphs with their spectral properties.

## What's in the database

For each connected graph on up to 10 vertices, SMOL stores:

**Spectra for four matrices:**
- Adjacency matrix
- Laplacian matrix (D - A)
- Non-backtracking (Hashimoto) matrix
- Non-backtracking Laplacian (normalized Laplacian of the NB graph)

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

## Installation

```bash
uv sync
```

## Usage

Generate and populate the database:

```bash
# Generate graphs for n=1 through n=8
uv run python scripts/generate.py --n 1 --n 8

# Dry run (process without inserting)
uv run python scripts/generate.py --n 6 --dry-run
```

## Configuration

Set `SMOL_DB_URL` to override the default PostgreSQL connection:

```bash
export SMOL_DB_URL="postgresql://user:pass@host:5432/smol"
```

Default: `postgresql://localhost/smol`

## For Developers

### Non-Python Dependencies

**nauty** is required for graph enumeration. It provides `geng`, which generates all non-isomorphic graphs.

Install via Homebrew:
```bash
brew install nauty
```

Or build from source: https://pallini.di.uniroma1.it/

### Running Tests

```bash
uv run pytest tests/ -v
```

### Project Structure

```
smol/
├── db/                  # Core library
│   ├── matrices.py      # Matrix computations (A, L, B, L_B)
│   ├── spectrum.py      # Eigenvalue computation and hashing
│   ├── metadata.py      # Graph property computation
│   ├── graph_data.py    # Combines everything into GraphRecord
│   └── database.py      # PostgreSQL operations
├── scripts/
│   └── generate.py      # Generation pipeline
├── sql/
│   └── schema.sql       # Database schema
└── tests/
```
