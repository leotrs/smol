"""Graph tag detection.

Detects special graph types and returns a list of tags.
"""

import networkx as nx


def compute_tags(G: nx.Graph) -> list[str]:
    """Compute tags for a graph.

    Args:
        G: A networkx Graph

    Returns:
        List of tag strings (e.g., ['complete', 'regular', 'eulerian'])
    """
    tags = []
    n = G.number_of_nodes()
    m = G.number_of_edges()

    if n == 0:
        return tags

    degrees = [d for _, d in G.degree()]
    min_deg = min(degrees)
    max_deg = max(degrees)
    is_connected = nx.is_connected(G) if n > 0 else False

    # Regular: all vertices have same degree
    if min_deg == max_deg:
        tags.append("regular")

    # Eulerian: all vertices have even degree (and connected)
    if is_connected and all(d % 2 == 0 for d in degrees):
        tags.append("eulerian")

    # Tree: connected and m = n - 1
    is_tree = is_connected and m == n - 1
    if is_tree:
        tags.append("tree")

    # Complete: m = n(n-1)/2
    if m == n * (n - 1) // 2:
        tags.append("complete")

    # Cycle: 2-regular, connected, n = m
    if min_deg == max_deg == 2 and is_connected and n == m:
        tags.append("cycle")

    # Path: tree with max_degree <= 2
    if is_tree and max_deg <= 2:
        tags.append("path")

    # Star: tree with one vertex of degree n-1, others degree 1
    if is_tree and n >= 3:
        if sorted(degrees) == [1] * (n - 1) + [n - 1]:
            tags.append("star")

    # Wheel: one vertex of degree n-1, all others degree 3, and n >= 4
    if n >= 4 and is_connected:
        sorted_degrees = sorted(degrees)
        if sorted_degrees == [3] * (n - 1) + [n - 1]:
            tags.append("wheel")

    # Complete bipartite: bipartite and m = |A| * |B|
    if nx.is_bipartite(G) and is_connected:
        try:
            A, B = nx.bipartite.sets(G)
            if m == len(A) * len(B):
                tags.append("complete-bipartite")
        except nx.AmbiguousSolution:
            pass

    # Petersen graph: n=10, 3-regular, girth=5, diameter=2
    if n == 10 and min_deg == max_deg == 3:
        try:
            girth = nx.girth(G)
            diameter = nx.diameter(G)
            if girth == 5 and diameter == 2:
                tags.append("petersen")
        except nx.NetworkXError:
            pass

    # Cubic: 3-regular
    if min_deg == max_deg == 3:
        tags.append("cubic")

    # Triangle-free: no triangles
    if nx.triangles(G).get(0, 0) == 0 and sum(nx.triangles(G).values()) == 0:
        tags.append("triangle-free")

    # Complete multipartite: complement is a disjoint union of cliques
    # A graph is complete multipartite iff its complement is a union of cliques (no edges between cliques)
    if is_connected and n >= 2:
        complement = nx.complement(G)
        components = list(nx.connected_components(complement))
        # Check each component is a clique (complete subgraph)
        is_all_cliques = True
        for comp in components:
            comp_nodes = list(comp)
            subgraph = complement.subgraph(comp_nodes)
            # A clique has n*(n-1)/2 edges
            expected_edges = len(comp_nodes) * (len(comp_nodes) - 1) // 2
            if subgraph.number_of_edges() != expected_edges:
                is_all_cliques = False
                break
        if is_all_cliques:
            # Already have complete and complete-bipartite, this is for 3+ parts
            num_parts = len(components)
            if num_parts >= 3:
                tags.append("complete-multipartite")

    # Prism: C_n □ K_2 (two cycles connected by matching)
    # n must be even, 3-regular, m = 3n/2
    if n >= 6 and n % 2 == 0 and min_deg == max_deg == 3 and is_connected:
        half = n // 2
        if m == 3 * half:  # prism has 3n/2 edges
            prism = nx.circular_ladder_graph(half)
            if nx.is_isomorphic(G, prism):
                tags.append("prism")

    # Ladder: P_n □ K_2 (two paths connected by rungs)
    # Has 2k vertices, 3k-2 edges, max degree 3, min degree 2
    if n >= 4 and n % 2 == 0 and is_connected:
        half = n // 2
        if m == 3 * half - 2 and min_deg == 2 and max_deg == 3:
            # Check structure: should have exactly 4 vertices of degree 2 (corners)
            deg_2_count = sum(1 for d in degrees if d == 2)
            if deg_2_count == 4:
                ladder = nx.ladder_graph(half)
                if nx.is_isomorphic(G, ladder):
                    tags.append("ladder")

    # Strongly regular: regular graph with consistent adjacency counts
    if min_deg == max_deg and is_connected and n >= 4:
        k = min_deg
        if 0 < k < n - 1:  # not empty or complete
            srg_params = _check_strongly_regular(G, n, k)
            if srg_params:
                tags.append("strongly-regular")

    # Line graph: detected via Beineke's theorem (no forbidden induced subgraphs)
    if is_connected and n >= 2:
        if _is_line_graph(G):
            tags.append("line-graph")

    # Windmill: n copies of K_k sharing a universal vertex
    # Has 1 + n*(k-1) vertices, n*k*(k-1)/2 edges, one vertex of high degree
    if is_connected and n >= 4:
        if _is_windmill(G):
            tags.append("windmill")

    # Fan: P_n joined to a single vertex (apex)
    # Has n+1 vertices, 2n-1 edges, apex has degree n
    if is_connected and n >= 3:
        if _is_fan(G, n, m):
            tags.append("fan")

    # Vertex-transitive: automorphism group acts transitively on vertices
    # Complete graphs, cycles, and Petersen are trivially vertex-transitive
    if "complete" in tags or "cycle" in tags or "petersen" in tags:
        tags.append("vertex-transitive")
    # For other graphs, check using automorphism enumeration (expensive)
    # Skip for large graphs to avoid exponential blowup
    elif is_connected and min_deg == max_deg and n >= 2 and n <= 8:
        if _is_vertex_transitive(G):
            tags.append("vertex-transitive")

    return sorted(tags)


def _check_strongly_regular(G: nx.Graph, n: int, k: int) -> tuple | None:
    """Check if G is strongly regular, return (n, k, λ, μ) or None."""
    nodes = list(G.nodes())
    adj_set = {v: set(G.neighbors(v)) for v in nodes}

    # Find λ (common neighbors of adjacent pair)
    lambda_val = None
    for u in nodes:
        for v in adj_set[u]:
            if u < v:
                common = len(adj_set[u] & adj_set[v])
                if lambda_val is None:
                    lambda_val = common
                elif common != lambda_val:
                    return None

    # Find μ (common neighbors of non-adjacent pair)
    mu_val = None
    for u in nodes:
        for v in nodes:
            if u < v and v not in adj_set[u]:
                common = len(adj_set[u] & adj_set[v])
                if mu_val is None:
                    mu_val = common
                elif common != mu_val:
                    return None

    if lambda_val is not None and mu_val is not None:
        return (n, k, lambda_val, mu_val)
    return None


def _is_line_graph(G: nx.Graph) -> bool:
    """Check if G is a line graph using Beineke's characterization."""
    n = G.number_of_nodes()
    if n <= 1:
        return True

    # Quick check: the claw K_{1,3} is forbidden
    for v in G.nodes():
        neighbors = list(G.neighbors(v))
        if len(neighbors) >= 3:
            for i in range(len(neighbors)):
                for j in range(i + 1, len(neighbors)):
                    for k in range(j + 1, len(neighbors)):
                        if (not G.has_edge(neighbors[i], neighbors[j]) and
                            not G.has_edge(neighbors[j], neighbors[k]) and
                            not G.has_edge(neighbors[i], neighbors[k])):
                            return False  # Found claw K_{1,3}

    try:
        return nx.is_valid_line_graph(G)
    except AttributeError:
        pass

    try:
        nx.inverse_line_graph(G)
        return True
    except (nx.NetworkXError, nx.NetworkXNotImplemented):
        return False


def _is_windmill(G: nx.Graph) -> bool:
    """Check if G is a windmill graph Wd(k,n): n copies of K_k sharing one vertex.

    k must be >= 2 (each blade is at least an edge).
    """
    # Find the universal vertex (highest degree, should be unique)
    degrees = dict(G.degree())
    max_deg = max(degrees.values())
    universal_candidates = [v for v, d in degrees.items() if d == max_deg]

    if len(universal_candidates) != 1:
        return False

    universal = universal_candidates[0]
    neighbors = set(G.neighbors(universal))

    # Remove universal vertex, remaining graph should be disjoint cliques
    H = G.subgraph([v for v in G.nodes() if v != universal]).copy()

    if not H.nodes():
        return False

    # Check each connected component is a clique
    components = list(nx.connected_components(H))
    if len(components) < 2:
        return False  # Need at least 2 blades for windmill

    clique_sizes = set()
    for comp in components:
        comp_nodes = list(comp)
        k = len(comp_nodes)
        if k < 2:
            return False  # Each blade must have at least 2 non-universal vertices (k >= 2 means K_k with k >= 3 total including universal)
        # Check it's a clique
        expected_edges = k * (k - 1) // 2
        actual_edges = H.subgraph(comp_nodes).number_of_edges()
        if actual_edges != expected_edges:
            return False
        # Check all connected to universal
        if not all(v in neighbors for v in comp_nodes):
            return False
        clique_sizes.add(k)

    # All cliques should be the same size
    if len(clique_sizes) != 1:
        return False

    return True


def _is_fan(G: nx.Graph, n: int, m: int) -> bool:
    """Check if G is a fan graph F_{1,k}: path P_k joined to apex vertex."""
    # Fan with k path vertices has k+1 total vertices, 2k-1 edges
    k = n - 1  # number of path vertices
    expected_edges = 2 * k - 1
    if m != expected_edges or k < 2:
        return False

    # Try each vertex as potential apex
    for apex in G.nodes():
        # Remove apex, check if remaining is a path with all vertices connected to apex
        other_nodes = [v for v in G.nodes() if v != apex]
        H = G.subgraph(other_nodes)

        # Path has k vertices and k-1 edges
        if H.number_of_edges() != k - 1:
            continue

        # Check it's a path: exactly 2 vertices of degree 1, rest degree 2
        h_degrees = sorted([d for _, d in H.degree()])
        if k == 2:
            expected_path_degrees = [1, 1]
        else:
            expected_path_degrees = [1, 1] + [2] * (k - 2)

        if h_degrees != expected_path_degrees:
            continue

        # Verify all path vertices connected to apex
        if all(G.has_edge(v, apex) for v in other_nodes):
            return True

    return False


def _is_vertex_transitive(G: nx.Graph) -> bool:
    """Check if G is vertex-transitive using automorphism group."""
    try:
        from networkx.algorithms.isomorphism import GraphMatcher

        n = G.number_of_nodes()
        if n <= 1:
            return True

        nodes = list(G.nodes())
        first = nodes[0]

        # Check if every vertex can be mapped to the first vertex
        for v in nodes[1:]:
            # Try to find an automorphism mapping first -> v
            found = False
            GM = GraphMatcher(G, G)
            # Limit number of isomorphisms checked to avoid exponential blowup
            max_isos_to_check = 10000
            for i, iso in enumerate(GM.isomorphisms_iter()):
                if iso[first] == v:
                    found = True
                    break
                if i >= max_isos_to_check:
                    # Too many automorphisms, give up
                    return False
            if not found:
                return False

        return True
    except Exception:
        return False
