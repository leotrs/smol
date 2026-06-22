#!/usr/bin/env python3
"""Render the two manuscript figures: the smallest cospectral family per matrix,
among connected graphs (Figure 1) and among minimum-degree->=2 graphs (Figure 2).

Self-contained: the families (graph6 strings) are the exact smallest families
found in the database; no database connection is needed to redraw.

    uv run python paper/make_figures.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec

# Smallest cospectral family per matrix among CONNECTED graphs.
FAM_CONNECTED = [
    ("Adjacency", ["ECRw", "EEiW"]),
    ("Kirchhoff Laplacian", ["EEzO", "EQjo"]),
    ("Signless Laplacian", ["DF{", "DT{"]),
    ("Normalized Laplacian", ["C]", "CF"]),
    ("Non-backtracking", ["CF", "CU"]),
    ("Non-backtracking Laplacian", ["CF", "CU"]),
    ("Distance", ["FCx}w", "FEivw"]),
    ("Distance Laplacian", ["FCr~o", "FEhvw"]),
    ("Distance Signless", ["DF{", "DT{"]),
    ("Normalized Distance", ["G?ouVs", "GCdbFk"]),
    ("Eccentricity", ["DCw", "DQw"]),
    ("k-blocking family", ["DC{", "DEk", "DQw"]),
    ("Yoon 2-Laplacian", ["ICrbvh{n_", "ICxvFh]n_"]),
    ("Yoon 3-Laplacian", ["ICpdbj[N_", "ICXedrMn?"]),
    ("Non-3-cycling", ["E?rw", "EQjo"]),
    ("Non-4-cycling", ["ECro", "EEio"]),
]

# Smallest cospectral family per matrix among MINIMUM-DEGREE->=2 graphs.
# None marks a matrix with no such family up to n = 10.
FAM_MINDEG2 = [
    ("Adjacency", ["FEhzo", "FEjfo"]),
    ("Kirchhoff Laplacian", ["FCvbw", "FCvfo"]),
    ("Signless Laplacian", ["E]zg", "EFzw"]),
    ("Normalized Laplacian", ["E?~o", "EFz_"]),
    ("Non-backtracking", ["GCdevg", "GCXmew"]),
    ("Non-backtracking Laplacian", None),
    ("Distance", ["FCx}w", "FEivw"]),
    ("Distance Laplacian", ["FCr~o", "FEhvw"]),
    ("Distance Signless", ["E]zg", "EFzw"]),
    ("Normalized Distance", ["G?ouVs", "GCdbFk"]),
    ("Eccentricity", ["FEhzo", "FEjfo"]),
    ("k-blocking family", ["H?`DBjw", "H?`DUbs"]),
    ("Yoon 2-Laplacian", ["ICrbvh{n_", "ICxvFh]n_"]),
    ("Yoon 3-Laplacian", ["ICpdbj[N_", "ICXedrMn?"]),
    ("Non-3-cycling", ["FCdbG", "FCXe_"]),
    ("Non-4-cycling", ["G?r@ds", "GCQRFo"]),
]

CORAL = "#E85A4F"


def draw_panel(fig, cell, name, members):
    axc = fig.add_subplot(cell)
    axc.set_axis_off()
    if members is None:
        axc.set_title(name, fontsize=9, pad=2)
        axc.text(0.5, 0.5, "no cospectral pair\nwith min degree ≥ 2\n(n ≤ 10)",
                 ha="center", va="center", fontsize=8.5, style="italic",
                 color="#555", transform=axc.transAxes)
        return
    n = nx.from_graph6_bytes(members[0].encode()).number_of_nodes()
    axc.set_title(f"{name}  (n={n})", fontsize=9, pad=2)
    inner = GridSpecFromSubplotSpec(1, len(members), subplot_spec=cell, wspace=0.05)
    for j, g6 in enumerate(members):
        ax = fig.add_subplot(inner[0, j])
        G = nx.from_graph6_bytes(g6.encode())
        pos = nx.kamada_kawai_layout(G) if G.number_of_edges() else nx.circular_layout(G)
        nx.draw(G, pos, ax=ax, node_size=22, width=0.7, node_color=CORAL, edge_color="#333")
        ax.set_axis_off()


def render(families, title, outstem):
    fig = plt.figure(figsize=(13, 13))
    outer = GridSpec(4, 4, figure=fig, hspace=0.32, wspace=0.12)
    for i, (name, members) in enumerate(families):
        draw_panel(fig, outer[divmod(i, 4)], name, members)
    fig.suptitle(title, fontsize=13, y=0.995)
    fig.savefig(f"{outstem}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    render(FAM_CONNECTED, "Smallest cospectral family per matrix (connected graphs)",
           "paper/fig1_cospectral_connected")
    render(FAM_MINDEG2, "Smallest cospectral family per matrix (minimum degree ≥ 2)",
           "paper/fig2_cospectral_mindeg2")
    print("wrote paper/fig1_cospectral_connected.png and paper/fig2_cospectral_mindeg2.png")
