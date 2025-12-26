"""
Check cospectrality implications between matrix types.
For each pair of matrix types X, Y: does X-cospectral imply Y-cospectral?
"""

import psycopg2

MATRIX_TYPES = ['adj', 'kirchhoff', 'signless', 'lap', 'nb', 'nbl', 'dist']

def get_cospectral_pairs(conn, matrix_type, min_degree=2):
    """Get all cospectral pairs for a given matrix type."""
    query = """
        SELECT g1.graph6, g2.graph6
        FROM cospectral_mates cm
        JOIN graphs g1 ON cm.graph1_id = g1.id
        JOIN graphs g2 ON cm.graph2_id = g2.id
        WHERE cm.matrix_type = %s
          AND g1.min_degree >= %s
          AND g2.min_degree >= %s
    """
    with conn.cursor() as cur:
        cur.execute(query, (matrix_type, min_degree, min_degree))
        return set(tuple(sorted([r[0], r[1]])) for r in cur.fetchall())

def main():
    conn = psycopg2.connect("dbname=smol")
    
    print("Loading cospectral pairs (min_degree >= 2)...\n")
    
    pairs = {}
    for mt in MATRIX_TYPES:
        pairs[mt] = get_cospectral_pairs(conn, mt, min_degree=2)
        print(f"{mt}: {len(pairs[mt])} pairs")
    
    print("\n" + "="*60)
    print("Checking implications: X-cospectral => Y-cospectral")
    print("="*60 + "\n")
    
    # For each X, Y: check if pairs[X] ⊆ pairs[Y]
    for x in MATRIX_TYPES:
        for y in MATRIX_TYPES:
            if x == y:
                continue
            
            x_pairs = pairs[x]
            y_pairs = pairs[y]
            
            if len(x_pairs) == 0:
                continue
            
            # How many X-cospectral pairs are also Y-cospectral?
            both = x_pairs & y_pairs
            x_only = x_pairs - y_pairs
            
            pct = 100 * len(both) / len(x_pairs)
            
            if len(x_only) == 0:
                status = "✓ IMPLICATION HOLDS"
            else:
                status = f"✗ {len(x_only)} counterexamples"
            
            print(f"{x:10s} => {y:10s}: {len(both):6d}/{len(x_pairs):<6d} ({pct:5.1f}%)  {status}")
        print()
    
    conn.close()

if __name__ == "__main__":
    main()
