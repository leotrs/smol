"""
Check all cospectrality implications using direct hash comparison.
"""

import psycopg2

MATRIX_TYPES = ['adj', 'kirchhoff', 'signless', 'lap', 'nb', 'nbl', 'dist']

def get_cospectral_pairs_direct(conn, matrix_type, min_degree=2):
    """Get all cospectral pairs by comparing hashes directly."""
    hash_col = f"{matrix_type}_spectral_hash"
    
    query = f"""
        SELECT g1.graph6, g2.graph6
        FROM graphs g1
        JOIN graphs g2 ON g1.{hash_col} = g2.{hash_col} AND g1.id < g2.id
        WHERE g1.min_degree >= %s AND g2.min_degree >= %s
    """
    
    with conn.cursor() as cur:
        cur.execute(query, (min_degree, min_degree))
        return set((r[0], r[1]) for r in cur.fetchall())

def main():
    conn = psycopg2.connect("dbname=smol")
    
    print("Loading cospectral pairs via direct hash comparison (min_degree >= 2)...\n")
    
    pairs = {}
    for mt in MATRIX_TYPES:
        pairs[mt] = get_cospectral_pairs_direct(conn, mt, min_degree=2)
        print(f"{mt}: {len(pairs[mt])} pairs")
    
    print("\n" + "="*60)
    print("Checking implications: X-cospectral => Y-cospectral")
    print("="*60 + "\n")
    
    for x in MATRIX_TYPES:
        for y in MATRIX_TYPES:
            if x == y:
                continue
            
            x_pairs = pairs[x]
            y_pairs = pairs[y]
            
            if len(x_pairs) == 0:
                continue
            
            both = x_pairs & y_pairs
            x_only = x_pairs - y_pairs
            
            pct = 100 * len(both) / len(x_pairs)
            
            if len(x_only) == 0:
                status = "✓ HOLDS"
            else:
                status = f"✗ {len(x_only)} counterexamples"
            
            print(f"{x:10s} => {y:10s}: {len(both):6d}/{len(x_pairs):<6d} ({pct:5.1f}%)  {status}")
        print()
    
    conn.close()

if __name__ == "__main__":
    main()
