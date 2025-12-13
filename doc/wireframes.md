# SMOL Website Wireframes

## Information Architecture

```
/           Search + results
/graph/{g6} Graph detail + cospectral mates
/compare    Compare 2+ graphs
/glossary   Terminology explanations
/about      What is SMOL, stats, API, citation
```

## 1. Home (`/`)

```
┌─────────────────────────────────────────────────────────────┐
│  SMOL                                        [About]        │
│  Spectra and Matrices Of Little graphs                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────┐  [Search]          │
│  │ Enter graph6 or filter...           │                    │
│  └─────────────────────────────────────┘                    │
│                                                             │
│  Filters:  n: [3-10]   ☐ bipartite  ☐ planar  ☐ regular    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Results (21 graphs)                      [Compare selected]│
│                                                             │
│  ☐ │ graph6 │ n │ m │ properties      │ cospectral mates   │
│  ──┼────────┼───┼───┼─────────────────┼────────────────────│
│  ☐ │ D?{    │ 5 │ 4 │ bip planar      │ adj:1 lap:5 nb:2   │
│  ☐ │ DEo    │ 5 │ 4 │ bip planar      │ adj:1 lap:3 nb:0   │
│  ☐ │ DFw    │ 5 │ 5 │ bip planar reg  │ adj:0 lap:0 nb:0   │
│  ...                                                        │
│                                                             │
│  [Load more]                                                │
└─────────────────────────────────────────────────────────────┘
```

## 2. Graph Detail (`/graph/{g6}`)

```
┌─────────────────────────────────────────────────────────────┐
│  SMOL  ← Back                                [About]        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐   D?{                                     │
│  │              │   5 vertices, 4 edges                     │
│  │   [graph     │                                           │
│  │    drawing]  │   Properties                              │
│  │              │   ├ bipartite: yes                        │
│  │              │   ├ planar: yes                           │
│  └──────────────┘   ├ diameter: 2                           │
│                     └ triangles: 0                          │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Cospectral Mates                                           │
│                                                             │
│  adj (1)  │ DEo                          [Compare]          │
│  lap (5)  │ D?_, D?o, D?w, DEo, DFw      [Compare]          │
│  nb  (2)  │ DCw, DQo                     [Compare]          │
│  nbl (2)  │ DCw, DQo                     [Compare]          │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  ▶ Spectra (click to expand)                                │
└─────────────────────────────────────────────────────────────┘
```

## 3. Compare (`/compare?graphs=D?{,DEo`)

```
┌─────────────────────────────────────────────────────────────┐
│  SMOL  ← Back                                [About]        │
├─────────────────────────────────────────────────────────────┤
│  Comparing 2 graphs                                         │
│                                                             │
│  Spectra:  adj: SAME   lap: SAME   nb: DIFF   nbl: DIFF    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│        │ D?{              │ DEo              │              │
│  ──────┼──────────────────┼──────────────────┤              │
│        │ [drawing]        │ [drawing]        │              │
│  ──────┼──────────────────┼──────────────────┤              │
│  n     │ 5                │ 5                │              │
│  m     │ 4                │ 4                │              │
│  bip   │ yes              │ yes              │              │
│  plan  │ yes              │ yes              │              │
│  diam  │ 2                │ 3                │ ← different  │
│  tri   │ 0                │ 0                │              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 4. Glossary (`/glossary`)

```
┌─────────────────────────────────────────────────────────────┐
│  SMOL                                 [Home]  [About]       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Glossary                                                   │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Search terms...                                         ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Graph Encoding                                             │
│  ───────────────                                            │
│  graph6         Compact ASCII encoding for simple graphs.   │
│                 Example: "D?{" = star graph K₁,₄            │
│                                                             │
│  Matrix Types                                               │
│  ────────────                                               │
│  adjacency      A[i,j] = 1 if edge (i,j) exists. Symmetric. │
│                 Eigenvalues are real.                       │
│                                                             │
│  laplacian      L = I - D⁻¹ᐟ²AD⁻¹ᐟ². Eigenvalues in [0,2]. │
│                                                             │
│  non-backtracking                                           │
│                 2m×2m matrix on directed edges. B[e,f] = 1  │
│                 if e leads into f without backtracking.     │
│                 Complex eigenvalues.                        │
│                                                             │
│  nb-laplacian   L = I - D⁻¹B. Random walk on directed edges.│
│                                                             │
│  Spectral Concepts                                          │
│  ─────────────────                                          │
│  spectrum       Multiset of eigenvalues of a matrix.        │
│                                                             │
│  cospectral     Two graphs with identical spectrum for a    │
│                 given matrix type.                          │
│                                                             │
│  Graph Properties                                           │
│  ────────────────                                           │
│  bipartite      Vertices split into two sets, edges only    │
│                 between sets. No odd cycles.                │
│                                                             │
│  planar         Can be drawn without edge crossings.        │
│                                                             │
│  regular        All vertices have the same degree.          │
│                                                             │
│  diameter       Longest shortest path between any two nodes.│
│                                                             │
│  girth          Length of shortest cycle. ∞ if acyclic.     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 5. About (`/about`)

```
┌─────────────────────────────────────────────────────────────┐
│  SMOL                                 [Home]  [Glossary]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  About SMOL                                                 │
│  ══════════                                                 │
│  A database of all simple connected graphs up to 10         │
│  vertices with precomputed spectral properties.             │
│                                                             │
│  Useful for finding examples, counterexamples, and          │
│  exploring which matrix types distinguish which graphs.     │
│                                                             │
│  Statistics                                                 │
│  ──────────                                                 │
│   n │ graphs │ adj-cospectral │ nb-cospectral              │
│  ───┼────────┼────────────────┼───────────────              │
│   5 │     21 │              0 │            8               │
│   6 │    112 │              2 │           49               │
│  ...                                                        │
│  10 │  11.7M │          402K │         1.1M               │
│                                                             │
│  API                                                        │
│  ───                                                        │
│  All endpoints return JSON by default.                      │
│                                                             │
│  GET /graphs/{graph6}         Single graph lookup           │
│  GET /graphs?n=7&regular=true Filter graphs                 │
│  GET /compare?graphs=D?{,DEo  Compare graphs                │
│  GET /stats                   Database statistics           │
│                                                             │
│  Citation                                                   │
│  ────────                                                   │
│  @misc{smol2025,                                            │
│    title  = {SMOL: Spectra and Matrices Of Little graphs},  │
│    author = {...},                                          │
│    year   = {2025},                                         │
│    url    = {...}                                           │
│  }                                                          │
│                                                             │
│  Source code: github.com/...                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTMX + Alpine.js
- **Database**: PostgreSQL (Supabase)
- **Hosting**: Fly.io (API), Netlify (frontend)

## Content Negotiation

API endpoints return JSON by default. When `Accept: text/html` header is present (HTMX requests), they return HTML fragments.
