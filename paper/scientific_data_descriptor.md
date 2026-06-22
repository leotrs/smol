# SMOL: a database of spectra and matrices of all small graphs

<!--
TARGET VENUE: Nature Scientific Data, Data Descriptor.
STATUS: complete draft (2026-06-22); dataset published, DOI and references filled.
Section order and headings follow the Scientific Data Data Descriptor template.
-->

**Author:** Leo Torres, Nora - Center for Science Communication (ORCID 0000-0002-2675-2775)
**Corresponding author:** Leo Torres (leo@leotrs.com)

---

## Abstract

Cospectral graphs, non-isomorphic graphs that share the spectrum of an
associated matrix, are central to spectral graph theory: they delimit exactly
what a given matrix can and cannot "hear" about a graph's structure. Yet
researchers studying cospectrality routinely re-enumerate small graphs and
re-derive their spectra, often with floating-point eigensolvers whose rounding
error can silently split or merge cospectral classes. We present **SMOL**
(Spectra and Matrices Of Little graphs), a database of all 12,293,434 simple
undirected graphs on up to 10 vertices (connected and disconnected), together
with the spectra and cospectrality classifications of **16 graph matrices**,
including standard operators (adjacency, the three Laplacians) and several
less-tabulated ones (non-backtracking, distance-based, eccentricity, Yoon, and
non-k-cycling matrices). Cospectrality is computed **exactly** for fourteen of
the sixteen matrices, from integer/rational characteristic polynomials rather
than floating-point eigenvalues, eliminating a class of precision errors that we
show causes prior float-based enumerations to mis-count cospectral families (only
the two largest operators, the non-k-cycling matrices, remain numerical).
SMOL is distributed as a relational database with a documented schema and a
public query API, providing a reusable "House of Graphs for spectra" that lets
others look up, filter, and download cospectral families instead of recomputing
them.

---

## Background & Summary

The spectrum of a matrix associated with a graph encodes structural information,
and the study of *which* structure each matrix encodes is the subject of
spectral graph theory [2,3]. A sharp way to
probe a matrix's discriminating power is to ask when two non-isomorphic graphs
are **cospectral** for it. The fraction of graphs that are determined by their
spectrum, and the structure of the cospectral families that are not, has been
tabulated for the adjacency and Laplacian matrices at small orders [4,5], and
the House of Graphs project [8] provides
a general-purpose, searchable catalogue of graphs and invariants. No comparable,
openly queryable resource exists that (i) covers the full census of small graphs,
(ii) spans a broad family of matrices beyond adjacency/Laplacian, and (iii)
guarantees that its cospectrality classification is exact rather than
floating-point approximate.

SMOL fills this gap. It enumerates every simple undirected graph on
n = 1, …, 10 vertices (Table 1) using the canonical generator `geng` from the
`nauty` package [1], computes 16 matrix spectra per graph,
and groups graphs into cospectral families per matrix. The 16 matrices were
chosen to span (a) the classical operators whose cospectrality is well studied,
giving a validation baseline, and (b) operators that are of active interest but
for which no small-graph cospectrality census has been published, where SMOL
contributes new tabulations.

The central methodological choice is **exactness**. Floating-point eigenvalue
hashing, the obvious way to test cospectrality at scale, fails for graphs whose
spectra are numerically close but not equal, and for matrices whose eigenvalues
are ill-conditioned. We instead key cospectrality on the exact characteristic
polynomial (an integer or, after clearing denominators, integer polynomial) for
fourteen of the sixteen matrices, including the two non-backtracking matrices,
whose complex spectra make floating-point classification least reliable. We show
in Technical Validation that this is not a theoretical nicety: at n = 10 the
exact computation both recovers true cospectral families that an 8-decimal
floating-point classification splits into singletons and removes spurious
families that rounding wrongly created, so a float-based census mis-counts
cospectrality.

The complete dataset (12.3 million graphs, 16 matrices) is provided as a
relational database with a documented schema (Data Records), archived with a
persistent identifier (Zenodo, DOI 10.5281/zenodo.20794132), and served live through a query API at
`smol-graphs-db.fly.dev`.

---

## Methods

### Graph enumeration

For each order n from 1 to 10 we generate one representative of every
isomorphism class of simple undirected graph using `geng` from `nauty`
[1], including disconnected graphs. Graphs are stored in
`graph6` format, the canonical ASCII encoding produced by `nauty`, which serves
as the primary key. The census sizes are listed in Table 1 and match the known
counts (OEIS A000088).

### Matrices

SMOL computes spectra for the 16 matrix types in Table 2. For a graph G with
adjacency matrix A and degree-diagonal D:

- **Adjacency** A.
- **Kirchhoff (combinatorial) Laplacian** L = D − A.
- **Signless Laplacian** Q = D + A.
- **Normalized Laplacian** I − D^(−1/2) A D^(−1/2).
- **Non-backtracking (Hashimoto)** matrix B on directed edges, and the
  **non-backtracking Laplacian** I − D^(−1)B (complex spectra) [7].
- **Distance** matrix and its **Laplacian** (Tr − Dist), **signless Laplacian**
  (Tr + Dist), and **normalized** variant, where Tr is the diagonal of
  transmissions; defined for connected graphs only.
- **Eccentricity** matrix (connected graphs only) [12].
- **Yoon m-Laplacians** for m = 2, 3 [13].
- **Non-k-cycling** matrices for k = 3, 4 (complex spectra) [14].
- **k-blocking family**, a composite, eigenvalue-free *signature* over the
  k-blocking operators M_k for k = 2, …, Δ.

Full definitions of the less-standard matrices are given in the cited sources and
in the project glossary.

### Spectral hashing and exact cospectrality

Two graphs are cospectral for a matrix iff they share its multiset of
eigenvalues, equivalently iff they share its characteristic polynomial. SMOL
assigns each (graph, matrix) pair a 16-character **spectral hash** and groups
graphs with equal hashes into cospectral families.

The hash is computed in one of two ways:

1. **Exact (13 matrices: adjacency, Kirchhoff, signless, normalized Laplacian,
   distance, distance Laplacian, distance signless, normalized distance,
   eccentricity, Yoon-2, Yoon-3, non-backtracking, and non-backtracking
   Laplacian).** We compute the exact characteristic polynomial coefficients and
   hash those integers. For integer matrices this is the fraction-free Bareiss
   determinant of xI − M; for the normalized matrices it is a monic generalized
   characteristic polynomial of the underlying pencil; for the Yoon matrices the
   rational matrix is scaled to clear a common denominator before the integer
   computation. The two non-backtracking matrices have complex spectra but are
   indexed by directed edges, so they are at most 2m ≤ 90 dimensional for m ≤ 45:
   small enough for an exact characteristic polynomial (the Hashimoto matrix is
   integer; the non-backtracking Laplacian I − D⁻¹B is rational, computed exactly
   and reduced to a canonical integer coefficient tuple). Because the coefficients
   are exact, equal hashes mean genuinely equal spectra: no false splits or merges
   from rounding.

2. **Floating-point (2 matrices: non-3-cycling, non-4-cycling).** These have
   complex spectra and matrices of up to several thousand dimensions (non-4-cycling
   reaches 3024 × 3024 at n = 9) for which an exact characteristic polynomial is
   computationally infeasible. Their spectra are computed numerically (eigenvalues
   rounded to 8 decimals) and hashed. The k-blocking family is a composite
   signature over several operators and is treated separately.

This split is recorded per matrix in the schema (Table 2) so that users can see
exactly which classifications are exact and which are numerical.

### Storage and access

Spectra need not be stored: every eigenvalue array can be recomputed on demand
from `graph6`, so SMOL stores only the 16 spectral hashes per graph plus
structural invariants, keeping the database compact. Cospectral families
(families of size ≥ 2) are precomputed into a dedicated table keyed by
(matrix, n, hash); family members are recovered by an indexed lookup on the
per-matrix hash column. The full database is PostgreSQL; a SQLite export drives a
public query API.

---

## Data Records

The dataset is archived at Zenodo (https://doi.org/10.5281/zenodo.20794132) under
a **CC0 1.0 public-domain dedication** and comprises:

- `smol.db` / SQL dumps: the relational database (schema in `sql/schema.sql`).
- Per-n flat files (CSV/Parquet) of the `graphs` and `cospectral_families`
  tables for users who do not want a database engine.
- `schema.sql` and a data dictionary documenting every table and column.

**`graphs`** (one row per graph; 12,293,434 rows): `graph6` (primary key), `n`,
`m` (edge count), the 16 `<matrix>_spectral_hash` columns, and structural
invariants (bipartite/planar/regular flags, diameter, radius, girth, min/max
degree, triangle count, clique and chromatic numbers, and network-science
descriptors such as algebraic connectivity and clustering). A NULL hash means
the matrix is undefined for that graph (e.g. distance-based matrices on
disconnected graphs, or a nilpotent non-k-cycling operator).

**`cospectral_families`** (one row per cospectral family of size ≥ 2): keyed by
(`matrix_type`, `n`, `spectral_hash`) with a `family_size` count. Members are
the graphs sharing that (n, hash). Per-matrix totals are in Table 2.

Table 1. Census sizes (number of simple undirected graphs).

| n | graphs |
|---|--------|
| 1 | 1 |
| 2 | 2 |
| 3 | 4 |
| 4 | 11 |
| 5 | 34 |
| 6 | 156 |
| 7 | 1,044 |
| 8 | 12,346 |
| 9 | 274,668 |
| 10 | 12,005,168 |
| **total** | **12,293,434** |

Table 2. The 16 matrices, classification method, and cospectral-family totals
over all n (families = number of families of size ≥ 2; members = graphs in some
family; largest = size of the biggest single family).

| key | matrix | spectrum | classification | families | members | largest |
|-----|--------|----------|----------------|----------|---------|---------|
| adj | Adjacency | real | exact | 1,188,183 | 2,613,489 | 21 |
| kirchhoff | Kirchhoff Laplacian | real | exact | 677,396 | 1,456,934 | 23 |
| signless | Signless Laplacian | real | exact | 316,061 | 656,933 | 9 |
| lap | Normalized Laplacian | real | exact | 13,791 | 29,264 | 43 |
| nb | Non-backtracking | complex | exact | 229,247 | 2,074,004 | 398 |
| nbl | Non-backtracking Laplacian | complex | exact | 26,833 | 62,690 | 106 |
| dist | Distance | real | exact | 661,241 | 1,415,724 | 21 |
| distlap | Distance Laplacian | real | exact | 383,794 | 809,094 | 16 |
| distsign | Distance Signless Laplacian | real | exact | 159,568 | 327,991 | 9 |
| distnorm | Normalized Distance Laplacian | real | exact | 3,781 | 7,566 | 3 |
| ecc | Eccentricity | real | exact | 1,582,305 | 6,060,545 | 8,300 |
| kblock_family | k-blocking family | signature | exact | 99,556 | 263,920 | 580 |
| yoon2 | Yoon 2-Laplacian | real | exact | 86 | 172 | 2 |
| yoon3 | Yoon 3-Laplacian | real | exact | 10 | 20 | 2 |
| non3cyc | Non-3-cycling | complex | numerical | 63,559 | 204,415 | 242 |
| non4cyc | Non-4-cycling | complex | numerical | 14,084 | 48,308 | 141 |

---

## Technical Validation

**Reproduction of known counts.** The census sizes (Table 1) match the known
number of simple graphs (OEIS A000088). SMOL's count of graphs with an adjacency
cospectral mate matches OEIS A006608 (the number of graphs not determined by
their adjacency spectrum) exactly across the full range, *including n = 10*
(Table 3a). The combinatorial-Laplacian and signless-Laplacian counts likewise
reproduce the published Haemers-Spence tabulations [5].

Table 3a. Graphs with an adjacency cospectral mate: SMOL vs OEIS A006608.

| n | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|----|
| SMOL (exact) | 2 | 10 | 110 | 1,722 | 51,039 | 2,560,606 |
| A006608 | 2 | 10 | 110 | 1,722 | 51,039 | 2,560,606 |

The n = 10 entry is the sharpest test, and it doubles as a demonstration of the
exactness payoff: an 8-decimal floating-point classification gives 2,560,604 at
n = 10 (two short), whereas the exact characteristic-polynomial count is
2,560,606, matching A006608. Exactness is what makes SMOL agree with the
authoritative value.

**Exactness recovers cospectral families that floating point misses.** We
compared, for each of the 13 exactly-classified matrices, the exact
characteristic-polynomial classification against an 8-decimal floating-point
eigenvalue classification. For the eleven real-spectrum matrices the two agree
exactly at n ≤ 9; at n = 10 the exact computation recovers a small number of
cospectral families that rounding had split into singletons (Table 3), each a
pair of graphs with genuinely equal spectra wrongly separated.

The two non-backtracking matrices, whose complex spectra are exactly where
floating-point eigensolvers are least reliable, show the largest corrections. At
n = 10, exact classification of the non-backtracking matrix removes 417 spurious
cospectral families that 8-decimal rounding had created (by splitting true
families inconsistently) and recovers 2,363 additional members from families
rounding had split into singletons; the non-backtracking Laplacian gains one
recovered family. We verified recovered families by independently recomputing the
exact characteristic polynomial of their members; the exact classification never
groups graphs with different characteristic polynomials, so no spurious merges
occur.

Table 3. Cospectral families among the real-spectrum matrices at n = 10 recovered
by exact computation that an 8-decimal floating-point classification splits (each
recovered family is a pair).

| matrix | recovered families | graphs |
|--------|--------------------|--------|
| adjacency | 1 | 2 |
| distance Laplacian | 2 | 4 |
| eccentricity | 4 | 8 |
| signless Laplacian | 1 | 2 |

**Remaining numerical matrices.** Only the two non-k-cycling matrices are
classified numerically; their matrices reach several thousand dimensions, beyond
exact characteristic-polynomial computation at this scale.

**Comparison with an earlier non-backtracking enumeration.** Our non-backtracking
and non-backtracking Laplacian cospectral counts agree with the earlier
enumeration of [7] at small n (exactly for the "all graphs" tally through n = 4,
and through n = 5 for the non-backtracking Laplacian) and diverge for larger n.
The divergence *persists under exact classification*: SMOL's exact
characteristic-polynomial counts agree closely with its floating-point counts, so
it is not a rounding artifact in the present data. As the earlier enumeration was
floating-point based, the most plausible source is a computational difference
between the two enumerations; SMOL provides the exact, fully reproducible counts.

---

## Usage Notes

The database can be queried three ways: (1) directly in SQL against the provided
schema; (2) via the public REST API at `smol-graphs-db.fly.dev` (endpoints for
single-graph lookup, filtered search, cospectral-family listing, and on-demand
spectra); (3) by loading the per-n flat files. Eigenvalue arrays are not stored
but are recomputed on demand from `graph6` (a single function call), so any
spectrum in the dataset is reproducible bit-for-bit from the public code.

Typical uses: looking up the cospectral mates of a given graph for any of the 16
matrices; enumerating all cospectral families of a chosen matrix and order to
test a conjecture; or using the cospectral families as a benchmark of
spectrally-indistinguishable graphs.

---

## Code Availability

All code to regenerate the database (enumeration, matrix construction, exact
characteristic-polynomial hashing, and the API) is openly available at
https://github.com/leotrs/smol and archived with the dataset at Zenodo
(https://doi.org/10.5281/zenodo.20794132) under the MIT license; the dataset
itself is released under CC0 1.0. The generation pipeline is
deterministic given `nauty`'s `geng`, so the entire dataset is reproducible from
source.

---

## Data Citation

Torres, L. (2026). SMOL: Spectra and Matrices Of Little graphs [Data set].
Zenodo. https://doi.org/10.5281/zenodo.20794132

## References

Confirmed:

1. McKay, B. D., & Piperno, A. (2014). Practical graph isomorphism, II.
   *Journal of Symbolic Computation*, 60, 94-112. (nauty / geng)
2. Brouwer, A. E., & Haemers, W. H. (2012). *Spectra of Graphs*. Springer.
3. Cvetković, D., Rowlinson, P., & Simić, S. (2010). *An Introduction to the
   Theory of Graph Spectra*. Cambridge University Press.
4. van Dam, E. R., & Haemers, W. H. (2003). Which graphs are determined by their
   spectrum? *Linear Algebra and its Applications*, 373, 241-272.
5. Haemers, W. H., & Spence, E. (2004). Enumeration of cospectral graphs.
   *European Journal of Combinatorics*, 25(2), 199-211.
6. Godsil, C. D., & McKay, B. D. (1982). Constructing cospectral graphs.
   *Aequationes Mathematicae*, 25(1), 257-268.
7. Jost, J., Mulas, R., & Torres, L. (2023). Spectral theory of the
   non-backtracking Laplacian for graphs. *Discrete Mathematics*, 346(10),
   113536.
8. Brinkmann, G., Coolsaet, K., Goedgebeur, J., & Mélot, H. (2013). House of
   Graphs: a database of interesting graphs. *Discrete Applied Mathematics*,
   161(1-2), 311-314.
9. OEIS Foundation. Sequence A000088 (number of graphs on n unlabeled nodes).
   *The On-Line Encyclopedia of Integer Sequences*.
10. OEIS Foundation. Sequence A006608 (number of graphs on n nodes not determined
    by their adjacency spectrum; values via Brouwer & Spence, 2009).
    *The On-Line Encyclopedia of Integer Sequences*.

11. Coolsaet, K., D'hondt, S., & Goedgebeur, J. (2023). House of Graphs 2.0: a
    database of interesting graphs and more. *Discrete Applied Mathematics*, 325,
    97-107.
12. Mahato, I., Gurusamy, R., Kannan, M. R., & Arockiaraj, S. (2020). Spectra of
    eccentricity matrices of graphs. *Discrete Applied Mathematics*, 285,
    252-260.
13. Yoon, M. (2025). Graph Laplacians with higher accuracy. arXiv:2504.04461.
14. Arrigo, F., Higham, D. J., & Noferini, V. (2020). Beyond non-backtracking:
    non-cycling network centrality measures. *Proceedings of the Royal Society A*,
    476(2235), 20190653.
