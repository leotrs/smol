# SMOL project tasks

# Run linter
lint:
    uv run ruff check .

# Run linter and tests
check: lint test

# Run all tests
test:
    uv run pytest tests/ -v

# Run tests with coverage
test-cov:
    uv run pytest tests/ -v --cov=api --cov=db --cov-report=term-missing

# Generate graphs (default n=1 to n=8)
generate n_min="1" n_max="8":
    uv run python scripts/generate.py --n-min {{n_min}} --n-max {{n_max}}

# Compute network science properties for graphs missing them
compute-properties *args:
    uv run python scripts/compute_properties.py {{args}}

# Refresh statistics cache
refresh-stats:
    uv run python scripts/refresh_stats.py

# Run API server locally
serve:
    uv run uvicorn api.main:app --reload --host 127.0.0.1

# Run API server on specific port
serve-port port:
    uv run uvicorn api.main:app --reload --host 127.0.0.1 --port {{port}}

# Check how many graphs need property computation
check-properties:
    psql smol -c "SELECT COUNT(*) as pending FROM graphs WHERE clique_number IS NULL"

# Database stats
db-stats:
    psql smol -c "SELECT n, COUNT(*) as graphs FROM graphs GROUP BY n ORDER BY n"
