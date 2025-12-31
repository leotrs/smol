---
title: 'SMOL: A Database of Spectral Properties for Small Graphs'
tags:
  - Python
  - spectral graph theory
  - graph database
  - eigenvalues
  - cospectral graphs
authors:
  - name: Leo Torres
    orcid: 0000-0002-8843-9341
    corresponding: true
    affiliation: 1
affiliations:
  - name: Independent Researcher
    index: 1
date: 31 December 2024
bibliography: paper.bib
---

# Summary

SMOL (Spectra and Matrices Of Little graphs) is a comprehensive database of simple undirected graphs with precomputed spectral properties for seven fundamental matrix types: adjacency, Kirchhoff Laplacian, signless Laplacian, normalized Laplacian, non-backtracking (Hashimoto), non-backtracking Laplacian, and distance matrices. The publicly deployed database contains all graphs up to 9 vertices, with the complete database extending to 10 vertices (approximately 12 million additional graphs) available upon request. SMOL provides both a web interface for interactive exploration and a RESTful API for programmatic access, enabling researchers to rapidly query spectral properties, enumerate cospectral pairs, and explore switching mechanisms without the computational overhead of eigenvalue computation. To our knowledge, SMOL is the most complete publicly available database of spectral properties for small graphs, combining exhaustive enumeration with multi-matrix spectral analysis.

# Statement of Need

Spectral graph theory studies graphs through the eigenvalues of associated matrices [@chung1997spectral; @cvetkovic1980spectra]. A central problem is understanding when non-isomorphic graphs share the same spectrum (cospectral graphs), which has implications for graph reconstruction, network comparison, and the limits of spectral methods [@godsil2001algebraic]. However, systematically studying spectral properties across graph families requires:

1. **Exhaustive enumeration** of all graphs in a given class (provided by tools like nauty [@mckay2014practical])
2. **Eigenvalue computation** for multiple matrix types (computationally expensive for large-scale studies)
3. **Cospectral pair detection** via spectral hash comparison
4. **Mechanism identification** to explain why graphs are cospectral [@godsil1982constructing]

While graph enumeration tools exist, no publicly available database provides precomputed spectral data at this scale. Researchers must either limit their studies to small samples or invest significant computational resources in redundant eigenvalue calculations. Prior versions of this database have been used in research on spectral properties of networks, but lacked public accessibility and comprehensive matrix coverage. SMOL addresses this gap by providing the first publicly accessible database with instant access to verified spectral properties for all graphs up to 10 vertices, enabling exploratory research that would otherwise be prohibitively expensive.

The database has been verified against published cospectral counts [@haemers2011enumeration] and includes detection of Godsil-McKay switching mechanisms [@godsil1982constructing], which explain approximately 43% of adjacency-cospectral pairs at 9 vertices. This verification ensures data integrity and provides a reliable foundation for research.

# Target Audience

SMOL is designed for researchers in:
- Spectral graph theory and algebraic graph theory
- Network science and complex systems
- Quantum walks and non-backtracking dynamics
- Graph signal processing

The web interface (https://smol-graphs-db.fly.dev) supports exploratory analysis with interactive visualizations, while the API enables integration with computational workflows and large-scale statistical studies. The full database extending to n=10 vertices is available upon request; public deployment is currently limited to n≤9 due to hosting resource constraints.

# Features

SMOL provides comprehensive spectral and structural data for each graph:

**Spectral properties:** Complete eigenvalue spectra for seven matrix types (adjacency, Kirchhoff Laplacian, signless Laplacian, normalized Laplacian, non-backtracking, non-backtracking Laplacian, distance matrix), enabling multi-matrix spectral analysis and comparison.

**Advanced search and filtering:** Web interface and API support complex queries combining structural properties (vertex/edge counts, diameter, girth, degree), spectral properties (algebraic connectivity), graph tags, and switching mechanism presence.

**Cospectral mate detection:** Pre-indexed cospectral pairs with spectral hashing for rapid lookup, supporting queries like "find all graphs cospectral to this graph for a given matrix type."

**Spectral similarity search:** Earth Mover's Distance computation to find graphs with similar (but not identical) spectra, enabling exploration of near-cospectral families.

**Interactive visualizations:** D3.js force-directed graph layouts, interactive spectral plots showing eigenvalues in the complex plane for all matrix types, with zoom and hover capabilities.

**Graph comparison:** Side-by-side visualization and property comparison for multiple graphs, with spectral distance matrices and mechanism visualizations showing vertex mappings.

**Structural metadata:** Graph properties including vertex/edge counts, bipartiteness, planarity, diameter, girth, radius, degree distribution, clustering coefficients, and algebraic connectivity.

**Switching mechanisms:** Detection of Godsil-McKay switching operations that transform graphs while preserving spectra, with approximately 43% coverage for adjacency-cospectral pairs at n=9.

**Named graph detection:** Automatic tagging of special graph families (complete graphs, cycles, paths, stars, wheels, trees, Petersen graph).

**RESTful API:** JSON responses for all data, supporting filters, pagination, sorting, random sampling, and programmatic access to all database features.

# Implementation

SMOL is implemented in Python using FastAPI for the web service and API, with PostgreSQL for development and SQLite for production deployment. Graph enumeration uses nauty's `geng` tool [@mckay2014practical], and eigenvalue computation employs NumPy and SciPy's optimized linear algebra routines. The codebase includes automated tests ensuring correctness of spectral computations and API responses.

All code, documentation, and deployment configurations are available under the MIT license at https://github.com/leotrs/smol, with comprehensive API documentation and example notebooks for common research tasks.

# Acknowledgements

This work builds upon decades of research in spectral graph theory and the foundational graph enumeration tools provided by the nauty package.

# References
