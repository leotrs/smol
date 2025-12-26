"""
Directly verify cospectrality of the 78 NBL pairs.
"""

import psycopg2

def main():
    conn = psycopg2.connect("dbname=smol")
    
    # Get the 78 NBL cospectral pairs
    query = """
        SELECT g1.graph6, g2.graph6,
               g1.adj_spectral_hash = g2.adj_spectral_hash as adj_cospec,
               g1.lap_spectral_hash = g2.lap_spectral_hash as lap_cospec,
               g1.nb_spectral_hash = g2.nb_spectral_hash as nb_cospec,
               g1.kirchhoff_spectral_hash = g2.kirchhoff_spectral_hash as kirch_cospec,
               g1.signless_spectral_hash = g2.signless_spectral_hash as signless_cospec
        FROM cospectral_mates cm
        JOIN graphs g1 ON cm.graph1_id = g1.id
        JOIN graphs g2 ON cm.graph2_id = g2.id
        WHERE cm.matrix_type = 'nbl'
          AND g1.min_degree >= 2
          AND g2.min_degree >= 2
    """
    
    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
    
    print(f"Total NBL-cospectral pairs (min_deg >= 2): {len(rows)}\n")
    
    # Count how many are also cospectral for other types
    adj_count = sum(1 for r in rows if r[2])
    lap_count = sum(1 for r in rows if r[3])
    nb_count = sum(1 for r in rows if r[4])
    kirch_count = sum(1 for r in rows if r[5])
    signless_count = sum(1 for r in rows if r[6])
    
    print(f"Also adj-cospectral:      {adj_count}/78")
    print(f"Also lap-cospectral:      {lap_count}/78")
    print(f"Also nb-cospectral:       {nb_count}/78")
    print(f"Also kirchhoff-cospectral: {kirch_count}/78")
    print(f"Also signless-cospectral:  {signless_count}/78")
    
    # Show the non-NB-cospectral pairs
    print("\n" + "="*60)
    print("NBL-cospectral pairs that are NOT NB-cospectral:")
    print("="*60)
    non_nb = [(r[0], r[1]) for r in rows if not r[4]]
    for g1, g2 in non_nb[:10]:
        print(f"  {g1},{g2}")
    if len(non_nb) > 10:
        print(f"  ... and {len(non_nb) - 10} more")
    
    conn.close()

if __name__ == "__main__":
    main()
