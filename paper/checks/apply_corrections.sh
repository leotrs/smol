#!/bin/zsh
# Replace the kblock_family, non3cyc and non4cyc hashes in the SMOL Postgres database with the
# exact, reproducible ones (out/corrections.csv), and their rows in cospectral_families
# (out/families_corrected.csv). Updating 12.3M rows while 45 indexes are maintained runs for
# hours, so every index on graphs that does not back a constraint is dropped first (its
# definition saved to pg_indexes_graphs_saved.sql) and rebuilt after the update.
set -e
cd "$(dirname "$0")"
db() { psql -U leo.torres -d smol -v ON_ERROR_STOP=1 -X -q "$@"; }
PLAIN="FROM pg_indexes i WHERE i.tablename = 'graphs' AND NOT EXISTS (SELECT 1 FROM pg_constraint c WHERE c.conname = i.indexname)"
db -At -c "SELECT indexdef || ';' $PLAIN" > pg_indexes_graphs_saved.sql
DROPS=$(db -At -c "SELECT 'DROP INDEX ' || quote_ident(indexname) || ';' $PLAIN")
echo "$(date +%T) dropping $(wc -l < pg_indexes_graphs_saved.sql | tr -d ' ') indexes, then updating"
db <<SQL
BEGIN;
CREATE TEMP TABLE corr (graph6 text PRIMARY KEY, kb text, h3 text, h4 text);
\copy corr FROM 'out/corrections.csv' CSV HEADER
$DROPS
UPDATE graphs g SET kblock_family_spectral_hash = c.kb, non3cyc_spectral_hash = c.h3, non4cyc_spectral_hash = c.h4
  FROM corr c WHERE g.graph6 = c.graph6;
DELETE FROM cospectral_families WHERE matrix_type IN ('kblock_family', 'non3cyc', 'non4cyc');
\copy cospectral_families (matrix_type, n, spectral_hash, family_size) FROM 'out/families_corrected.csv' CSV HEADER
COMMIT;
SQL
echo "$(date +%T) update committed; vacuuming and rebuilding indexes"
db -c "VACUUM ANALYZE graphs"
db -f pg_indexes_graphs_saved.sql
echo "$(date +%T) done: $(db -At -c "SELECT count(*) FROM pg_indexes WHERE tablename = 'graphs'") indexes on graphs"
