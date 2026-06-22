# Cover letter — submission to Scientific Data

Dear Editors,

Please consider the enclosed Data Descriptor, "SMOL: Spectra and Matrices Of
Little graphs," for publication in Scientific Data.

SMOL is a database of all 12,293,434 simple undirected graphs on up to 10
vertices, together with the spectra and exact cospectrality classifications of 16
graph matrices. It is, to our knowledge, the first openly queryable resource that
combines the full small-graph census with a broad family of matrices (adjacency,
the three Laplacians, distance-based operators, eccentricity, Yoon, and the
non-backtracking and non-k-cycling matrices) and that guarantees its cospectrality
classifications are exact rather than floating-point approximate.

We believe the dataset is a strong fit for Scientific Data for three reasons:

1. **Reuse value.** Cospectral graphs delimit exactly what each matrix can and
   cannot recover about a graph. Researchers studying cospectrality currently
   re-enumerate small graphs and re-derive their spectra one project at a time;
   SMOL lets them look up, filter, and download cospectral families instead. It
   is, in effect, a "House of Graphs for spectra."

2. **Exactness and validation.** Cospectrality is computed exactly for 14 of the
   16 matrices, from integer/rational characteristic polynomials rather than
   floating-point eigenvalues. The dataset's adjacency cospectral-mate counts
   match OEIS A006608 exactly through n = 10, and the Laplacian/signless counts
   reproduce the Haemers–Spence tabulations, providing independent validation.

3. **Reproducibility.** The dataset is archived under a persistent identifier on
   Zenodo (DOI 10.5281/zenodo.20794132) under a CC0 public-domain dedication, all
   code is openly available, and the generation pipeline is deterministic, so the
   entire database is reproducible from source.

The manuscript has not been published elsewhere and is not under consideration by
another journal. The author declares no competing interests.

[[If applying for an APC waiver: We respectfully request consideration for an
article-processing-charge waiver on the basis of financial need; this work was
carried out without grant funding.]]

Thank you for your consideration.

Sincerely,
Leo Torres
Nora — Center for Science Communication
leo@leotrs.com · ORCID 0000-0002-2675-2775
