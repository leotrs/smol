-- Switching mechanisms table
-- Stores all detected switching mechanisms for cospectral pairs
-- Multiple mechanisms can exist per pair

CREATE TABLE switching_mechanisms (
    graph1_id INTEGER NOT NULL REFERENCES graphs(id) ON DELETE CASCADE,
    graph2_id INTEGER NOT NULL REFERENCES graphs(id) ON DELETE CASCADE,
    matrix_type TEXT NOT NULL, -- 'adj', 'kirchhoff', 'signless', 'lap', 'nb', 'nbl'
    mechanism_type TEXT NOT NULL, -- 'gm', 'nbl_2edge', 'bipartite_swap', etc.
    config JSONB NOT NULL, -- Switching set, partition, etc.
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (graph1_id, graph2_id, matrix_type, mechanism_type),

    -- Ensure graph1_id < graph2_id for consistency
    CONSTRAINT ordered_pair CHECK (graph1_id < graph2_id),

    -- Foreign key to cospectral_mates
    FOREIGN KEY (graph1_id, graph2_id, matrix_type)
        REFERENCES cospectral_mates(graph1_id, graph2_id, matrix_type)
        ON DELETE CASCADE
);

-- Indexes for fast lookups
CREATE INDEX idx_mechanisms_graph1 ON switching_mechanisms(graph1_id);
CREATE INDEX idx_mechanisms_graph2 ON switching_mechanisms(graph2_id);
CREATE INDEX idx_mechanisms_matrix ON switching_mechanisms(matrix_type);
CREATE INDEX idx_mechanisms_type ON switching_mechanisms(mechanism_type);
CREATE INDEX idx_mechanisms_config ON switching_mechanisms USING gin(config);

-- Materialized view for graph-level statistics
CREATE MATERIALIZED VIEW graph_mechanism_stats AS
WITH graph_pairs AS (
    -- Get all graphs from both sides of pairs
    SELECT graph1_id as graph_id, matrix_type, mechanism_type
    FROM switching_mechanisms
    UNION ALL
    SELECT graph2_id, matrix_type, mechanism_type
    FROM switching_mechanisms
)
SELECT
    g.id as graph_id,
    g.n,
    gp.matrix_type,
    gp.mechanism_type,
    COUNT(*) as mate_count,
    bool_or(true) as has_mechanism
FROM graphs g
JOIN graph_pairs gp ON g.id = gp.graph_id
GROUP BY g.id, g.n, gp.matrix_type, gp.mechanism_type;

CREATE INDEX idx_graph_mech_stats_graph ON graph_mechanism_stats(graph_id);
CREATE INDEX idx_graph_mech_stats_n ON graph_mechanism_stats(n);
CREATE INDEX idx_graph_mech_stats_type ON graph_mechanism_stats(mechanism_type);

-- Refresh function for stats
CREATE OR REPLACE FUNCTION refresh_mechanism_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY graph_mechanism_stats;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE switching_mechanisms IS
'Stores detected switching mechanisms for each cospectral pair. Multiple mechanisms can exist per pair.';

COMMENT ON COLUMN switching_mechanisms.config IS
'JSONB containing mechanism-specific configuration:
- GM: {switching_set: [int], partition: [[int]], num_classes: int}
- NBL 2-edge: {v1: int, v2: int, w1: int, w2: int}
- Bipartite swap: {hubs: [int], leaves1: [int], leaves2: [int], k: int}';
