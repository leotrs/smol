# OEIS Sequences Relevant to SMOL

This document catalogs all OEIS (On-Line Encyclopedia of Integer Sequences) sequences relevant to the SMOL graph database.

## Core Graph Enumeration

### Basic Counts

**[A000088](https://oeis.org/A000088) - Number of unlabeled graphs on n vertices**
```
1, 1, 2, 4, 11, 34, 156, 1044, 12346, 274668, 12005168, ...
```
- The fundamental sequence for graph enumeration
- **Matches SMOL exactly**: Our database counts match these values ✓
- Represents all simple graphs (connected and disconnected)
- Also represents equivalence classes of sign patterns of totally nonzero symmetric n×n matrices

**[A001349](https://oeis.org/A001349) - Number of connected unlabeled graphs on n vertices**
```
1, 1, 1, 2, 6, 21, 112, 853, 11117, 261080, 11716571, ...
```
- The singleton graph K₁ is considered connected
- Inverse Euler transform of A000088
- **Relevant to SMOL**: We separate connected and disconnected graphs

**[A008406](https://oeis.org/A008406) - Triangle T(n,k): number of graphs with n nodes and k edges**
- Organized as a triangle: row n lists counts for k=0 to k=n(n-1)/2
- Row sums give A000088
- **Directly relevant**: SMOL allows queries by both n (vertices) and m (edges)
- Pattern: T(n,k)=1 for k=0, k=1, k=n(n-1)/2-1, and k=n(n-1)/2 (n≥2)

## Trees

**[A000055](https://oeis.org/A000055) - Number of unlabeled trees on n vertices**
```
1, 1, 1, 1, 2, 3, 6, 11, 23, 47, 106, 235, 551, 1301, ...
```
- Classic enumeration by Cayley (1875)
- **Relevant**: SMOL has tree detection in tags
- Related: A000081 (rooted trees), A000272 (labeled trees)

## Property-Based Sequences

### Planarity

**[A005470](https://oeis.org/A005470) - Number of unlabeled planar graphs on n vertices**
- Euler transform of A003094 (connected planar graphs)
- Values computed up to n=12 by Brendan McKay
- **Matches SMOL property**: `is_planar` boolean flag

### Bipartiteness

**[A033995](https://oeis.org/A033995) - Number of unlabeled bipartite graphs on n vertices**
```
1, 1, 2, 3, 7, 13, 35, 88, 303, 1119, 5479, 32303, ...
```
- **Matches SMOL property**: `is_bipartite` boolean flag
- Related: A047864 (labeled version), A005142 (connected bipartite)

**[A005142](https://oeis.org/A005142) - Connected triangle-free graphs on n nodes with chromatic number 2**
```
1, 1, 1, 1, 3, 5, 17, 44, 182, 730, ...
```
- These are connected bipartite graphs
- Triangle-free with chromatic number 2

### Regular Graphs

**[A005638](https://oeis.org/A005638) - Number of unlabeled 3-regular (cubic) graphs on 2n vertices**
```
1, 0, 1, 2, 6, 21, 94, 540, 4207, 42110, 516344, ...
```
- **Matches SMOL property**: `is_regular` boolean flag
- Euler transform of A002851 (connected cubic graphs)
- Related: A002851 (connected), A165653 (disconnected)

**[A002851](https://oeis.org/A002851) - Connected 3-regular simple graphs on 2n vertices**
```
1, 0, 1, 2, 5, 19, 85, 509, 4060, 41301, ...
```

**[A033301](https://oeis.org/A033301) - 4-regular graphs on 2n vertices**

**[A165626](https://oeis.org/A165626) - 5-regular graphs on 2n vertices**

### Strongly Regular Graphs

**[A076435](https://oeis.org/A076435) - Number of strongly regular graphs on n nodes**
```
1, 1, 2, 4, 3, 6, 2, 6, 5, ...
```

**[A088741](https://oeis.org/A088741) - Number of connected strongly regular graphs on n nodes**
```
1, 0, 1, 2, 2, 3, 1, 3, 3, ...
```

## Cycle-Related Sequences

### Eulerian Graphs

**[A003049](https://oeis.org/A003049) - Number of connected Eulerian graphs on n vertices**
```
1, 0, 1, 1, 4, 8, 37, 184, 1782, 31026, 1148626, ...
```
- Connected graphs where every vertex has even degree
- Inverse Euler transform of A002854
- **Relevant**: SMOL could detect Eulerian graphs (all even degrees)
- Related to Euler circuits/paths

### Hamiltonian Graphs

**[A003216](https://oeis.org/A003216) - Number of Hamiltonian graphs on n vertices**
```
1, 0, 1, 3, 8, 48, 383, 6196, 177083, ...
```
- Graphs containing a Hamiltonian cycle
- **Potential feature**: SMOL doesn't currently track Hamiltonian cycles
- Related: A246446 (non-Hamiltonian), A057864 (Hamiltonian path)

### Girth

**[A128240](https://oeis.org/A128240) - n-node connected graphs with girth 3**
- **Matches SMOL property**: `girth` integer field

**Connected 3-regular graphs by girth:**
- A014371 - girth at least 4 (triangle-free)
- A014372 - girth at least 5
- A014374 - girth at least 6
- A014375 - girth at least 7
- A014376 - girth at least 8

**Connected 3-regular graphs with exact girth:**
- A006923 - girth exactly 3
- A006924 - girth exactly 4
- A006925 - girth exactly 5
- A006926 - girth exactly 6
- A006927 - girth exactly 7

## Symmetry & Automorphisms

### Vertex-Transitive Graphs

**[A006799](https://oeis.org/A006799) - Vertex-transitive graphs on n vertices**
```
1, 2, 2, 4, 3, 8, 4, 14, 9, ...
```
- Graphs where automorphism group acts transitively on vertices
- **Note**: All vertex-transitive graphs are regular

**[A006800](https://oeis.org/A006800) - Connected vertex-transitive graphs on n vertices**
```
1, 1, 1, 2, 2, 5, 3, 10, 7, ...
```

### Edge-Transitive Graphs

**[A095424](https://oeis.org/A095424) - Connected edge-transitive graphs on n vertices**
```
1, 1, 2, 3, 4, 6, 5, 8, 9, 13, 7, 19, 10, 16, 25, 26, 12, 28, ...
```

### Automorphism Groups

**[A095348](https://oeis.org/A095348) - Number of distinct orders of automorphism groups of graphs on n nodes**
```
1, 1, 2, 5, 8, 14, 19, 30, 45, ...
```

**[A080803](https://oeis.org/A080803) - Minimal graph with automorphism group of order n**
```
0, 2, 9, 4, 15, 3, 14, 4, 15, 5, ...
```

## Cospectrality (DIRECTLY RELEVANT TO SMOL)

### Adjacency Matrix

**[A006608](https://oeis.org/A006608) - Number of graphs with cospectral mates (adjacency)**
```
0, 0, 0, 0, 2, 10, 110, 1722, 51039, 2560606, ...
```
- **MATCHES SMOL DATA**: Our n=9 value is 51,039 ✓✓✓
- Counts graphs that are NOT determined by their adjacency spectrum
- Smallest cospectral pair: K₁,₄ (star) and K₁ ∪ C₄ (n=5)

**[A178925](https://oeis.org/A178925) - Graphs determined by adjacency spectrum**
```
1, 2, 4, 11, 32, 146, 934, 10624, 223629, ...
```
- Complementary to A006608
- A000088(n) = A178925(n) + A006608(n)

**[A099881](https://oeis.org/A099881) - Number of pairs of cospectral graphs**
```
0, 0, 0, 0, 1, 5, 52, 771, 21025, ...
```
- Excludes pairs that are part of larger cospectral families
- Related to cospectral family structure

**[A099882](https://oeis.org/A099882) - Number of triples of cospectral graphs**
```
0, 0, 0, 0, 0, 0, 2, 52, 2015, ...
```
- Excludes triples that are part of quadruples, etc.
- First occurs at n=7 with 2 triples

## SMOL's Potential Contributions to OEIS

Based on extensive searching, **these sequences do not appear to exist in OEIS**:

### 1. Kirchhoff Laplacian Cospectrality
**Graphs with Kirchhoff (L = D - A) cospectral mates by n:**
```
0, 0, 0, 0, 0, 4, 130, 1767, 42595, ...
```
**SMOL data (n≤9):** 44,496 total graphs with cospectral mates

### 2. Signless Laplacian Cospectrality
**Graphs with Signless (Q = D + A) cospectral mates by n:**
```
0, 0, 0, 2, 4, 16, 102, 1201, 19001, ...
```
**SMOL data (n≤9):** 20,326 total graphs with cospectral mates

### 3. Normalized Laplacian Cospectrality
**Graphs with Normalized Laplacian cospectral mates by n:**
```
0, 0, 2, 4, 12, 32, 108, 413, 1824, ...
```
**SMOL data (n≤9):** 2,395 total graphs with cospectral mates

### 4. Non-Backtracking Matrix Cospectrality
**Graphs with NB (Hashimoto) matrix cospectral mates by n:**
```
0, 0, 0, 4, 15, 75, 449, 4297, 68749, ...
```
**SMOL data (n≤9):** 73,589 total graphs with cospectral mates

### 5. Non-Backtracking Laplacian Cospectrality
**Graphs with NBL (L_B = I - D⁻¹B) cospectral mates by n:**
```
0, 0, 0, 4, 8, 26, 100, 574, 4622, ...
```
**SMOL data (n≤9):** 5,334 total graphs with cospectral mates

### 6. Graphs with Min Degree ≥ 2 by Matrix Type

**Kirchhoff cospectral (min_degree ≥ 2):**
```
0, 0, 0, 0, 0, 0, 64, 1156, 31353, ...
```

**Signless cospectral (min_degree ≥ 2):**
```
0, 0, 0, 0, 0, 4, 37, 725, 13878, ...
```

## Summary Statistics (SMOL Database, n≤9)

| Matrix Type          | Total Graphs | Graphs w/ Mates | Percentage |
|---------------------|--------------|-----------------|------------|
| Adjacency           | 288,266      | 52,883          | 18.3%      |
| Kirchhoff           | 288,266      | 44,496          | 15.4%      |
| Signless            | 288,266      | 20,326          | 7.1%       |
| Normalized Laplacian| 288,266      | 2,395           | 0.8%       |
| Non-Backtracking    | 288,266      | 73,589          | 25.5%      |
| NBL                 | 288,266      | 5,334           | 1.8%       |

**Key observations:**
- Non-backtracking matrix has the MOST cospectral graphs (25.5%)
- Normalized Laplacian has the FEWEST cospectral graphs (0.8%) - best discriminator
- Adjacency matrix is middle-of-the-pack (18.3%)
- All six matrices together still fail to uniquely determine many graphs

## References

1. **OEIS - The On-Line Encyclopedia of Integer Sequences**
   https://oeis.org

2. **Haemers, W.H. and Spence, E. (2004)**
   "Enumeration of cospectral graphs"
   European Journal of Combinatorics, 25(2), 199-211

3. **Abiad, A., van de Berg, N., and Simoens, K. (2025)**
   "Counting cospectral graphs obtained via switching"
   arXiv:2503.08627

4. **Godsil, C.D. and McKay, B.D. (1982)**
   "Constructing cospectral graphs"
   Aequationes Mathematicae, 25, 257-268

5. **Robinson, R.W. and Wormald, N.C. (1983)**
   Numbers of cubic graphs (used in A005638)

6. **Harary, F. and Palmer, E.M. (1973)**
   "Graphical Enumeration"
   Academic Press, NY

## Notes for Future Work

### Potential OEIS Submissions
The five new cospectral sequences (Kirchhoff, Signless, Normalized Laplacian, NB, NBL) represent original contributions that could be submitted to OEIS. Each would need:
- Values for n=1 to at least n=10
- Clear definition and mathematical context
- References to spectral graph theory literature
- Cross-references to existing sequences (especially A006608)

### Related Queries SMOL Could Answer
With current data, SMOL could generate sequences for:
- Regular graphs by degree (k-regular for k=0,1,2,3,4,...)
- Bipartite vs non-bipartite splits
- Planar vs non-planar splits
- By diameter, radius, girth
- By clique number, chromatic number
- By triangle count
- Tree vs non-tree
- Eulerian graphs (all even degree)
- Combinations (e.g., "planar bipartite 3-regular graphs")

### Missing Data That Would Be Valuable
- Hamiltonian cycles/paths
- Graph automorphism groups (orders, structures)
- Vertex/edge transitivity
- Line graph detection
- Whether graph is strongly regular
- Exact chromatic number (currently greedy upper bound)
