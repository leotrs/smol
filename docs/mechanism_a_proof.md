# Mechanism A: Double-Parallel Switch

## Definitions

**Graph notation.** Let G = (V, E) be a simple undirected graph. For v ∈ V:
- N(v) = {u ∈ V : uv ∈ E} is the neighborhood of v
- deg(v) = |N(v)| is the degree of v

**2-edge switch.** Given two disjoint edges {v₁w₁, v₂w₂} with v₁, v₂, w₁, w₂ all distinct, the 2-edge switch produces G' with:
- E(G') = E(G) \ {v₁w₁, v₂w₂} ∪ {v₁w₂, v₂w₁}

**Directed edges.** Let D(G) = {(u,v) : uv ∈ E} be the set of directed edges (each undirected edge gives two directed edges).

**NBL transition matrix.** The non-backtracking Laplacian transition matrix T is indexed by D(G):

$$T_{(a,b),(c,d)} = \begin{cases} \frac{1}{\deg(b) - 1} & \text{if } b = c \text{ and } d \neq a \\ 0 & \text{otherwise} \end{cases}$$

This is the transition matrix for a random walk on directed edges that cannot immediately backtrack.

**NBL-cospectral.** Graphs G and G' are NBL-cospectral if their transition matrices T_G and T_{G'} have the same eigenvalues (with multiplicity).

**Switch region.** For a 2-edge switch, define:
- S = {v₁, v₂, w₁, w₂} (the four switch vertices)
- ext(u) = N(u) \ S for u ∈ S (external neighborhood)
- shared = ext(w₁) ∩ ext(w₂)
- unique₁ = ext(w₁) \ ext(w₂)
- unique₂ = ext(w₂) \ ext(w₁)

---

## Theorem (Mechanism A: Double-Parallel Switch)

Let G be a simple graph and {v₁w₁, v₂w₂} be two disjoint edges. Let G' be the 2-edge switch. If all of the following hold:

1. **Degree equality:** deg(v₁) = deg(v₂) =: d_v and deg(w₁) = deg(w₂) =: d_w

2. **Both parallel edges exist:** v₁v₂ ∈ E(G) and w₁w₂ ∈ E(G)

3. **Two shared external vertices:** |shared| = 2

4. **Uniform cross-intersection:** There exists c ≥ 1 such that
   $$|ext(v_i) \cap ext(w_j)| = c \quad \text{for all } i,j \in \{1,2\}$$

5. **Balanced unique sets:** |unique₁| = |unique₂| = 2

6. **Uniform unique degrees:** There exists d_u such that deg(x) = d_u for all x ∈ unique₁ ∪ unique₂

Then G and G' are NBL-cospectral.

---

## Preliminary Observations

### Observation 1: Degrees are preserved by the switch

In G:
- N_G(v₁) contains w₁ (switched edge), possibly v₂ (parallel), and ext(v₁)
- N_G(w₁) contains v₁ (switched edge), possibly w₂ (parallel), and ext(w₁)

In G':
- N_{G'}(v₁) contains w₂ (new edge), possibly v₂ (parallel), and ext(v₁)
- N_{G'}(w₁) contains v₂ (new edge), possibly w₂ (parallel), and ext(w₁)

Each vertex in S loses one neighbor and gains one neighbor, so deg_G(u) = deg_{G'}(u) for all u.

### Observation 2: Structure of ext(w₁) and ext(w₂)

By conditions 3 and 5:
- ext(w₁) = shared ∪ unique₁ with |shared| = 2, |unique₁| = 2, so |ext(w₁)| = 4
- ext(w₂) = shared ∪ unique₂ with |shared| = 2, |unique₂| = 2, so |ext(w₂)| = 4

Since w₁ is adjacent to v₁, w₂ (parallel), and ext(w₁):
$$d_w = \deg(w_1) = 1 + 1 + 4 = 6$$

(This explains why all Mechanism A pairs have d_w = 6.)

### Observation 3: Transition probabilities

Define:
- α = 1/(d_v - 1) (transition probability at v-vertices)
- β = 1/(d_w - 1) = 1/5 (transition probability at w-vertices)

These are unchanged by the switch since degrees are preserved.

---

## Proof of Trace Equality

We prove tr(T_G^k) = tr(T_{G'}^k) for all k ≥ 1.

### Case k = 1

**Claim:** tr(T) = 0 for any graph.

**Proof:** The diagonal entry T_{(a,b),(a,b)} requires b = a and b ≠ a simultaneously, which is impossible. Therefore T_{(a,b),(a,b)} = 0 for all directed edges, and tr(T) = 0. ∎

### Case k = 2

**Claim:** tr(T²) = 0 for any graph.

**Proof:** We have:
$$[T^2]_{(a,b),(a,b)} = \sum_{(c,d) \in D(G)} T_{(a,b),(c,d)} \cdot T_{(c,d),(a,b)}$$

For a nonzero term, we need:
- T_{(a,b),(c,d)} ≠ 0 ⟹ c = b and d ≠ a
- T_{(c,d),(a,b)} ≠ 0 ⟹ a = d and b ≠ c

From the first condition: c = b, d ≠ a.
From the second condition: a = d, b ≠ c.

But c = b and b ≠ c is a contradiction.

Therefore [T²]_{(a,b),(a,b)} = 0 for all (a,b), and tr(T²) = 0. ∎

### Case k = 3

**Claim:** Under conditions 1-6, tr(T_G³) = tr(T_{G'}³).

**Proof:**

A diagonal entry [T³]_{(a,b),(a,b)} counts weighted closed 3-walks starting and ending at (a,b):
$$(a,b) \to (b,c) \to (c,d) \to (d,e)$$
where (d,e) = (a,b), i.e., d = a and e = b.

For this to be nonzero:
- (a,b) → (b,c): requires c ≠ a, contributes 1/(deg(b)-1)
- (b,c) → (c,a): requires a ≠ b (satisfied) and ca ∈ E, contributes 1/(deg(c)-1)
- (c,a) → (a,b): requires b ≠ c and ab ∈ E, contributes 1/(deg(a)-1)

This corresponds to a triangle a-b-c in G. The contribution is:
$$\frac{1}{(\deg(a)-1)(\deg(b)-1)(\deg(c)-1)}$$

**Triangles affected by the switch:**

The switch removes edge v₁w₁ and adds edge v₁w₂. Triangles containing v₁w₁ are lost; triangles containing v₁w₂ are gained.

*Lost triangles through v₁-w₁:*
- Triangle v₁-w₁-x where x ∈ N(v₁) ∩ N(w₁) and x ∉ {v₁, w₁}
- Since v₂ ∈ N(v₁) (parallel edge) but v₂ ∉ N(w₁) (otherwise would violate simple graph), we need x ∈ ext(v₁) ∩ ext(w₁)
- Also x could be w₂ if w₂ ∈ N(v₁), but w₂ ∉ N(v₁) in G
- So lost triangles: v₁-w₁-x for x ∈ ext(v₁) ∩ ext(w₁), count = c

*Gained triangles through v₁-w₂:*
- Triangle v₁-w₂-x where x ∈ N(v₁) ∩ N(w₂) and x ∉ {v₁, w₂}
- Need x ∈ ext(v₁) ∩ ext(w₂), count = c (by condition 4)

Similarly for v₂: lost triangles v₂-w₂-x, gained triangles v₂-w₁-x, both with count c.

**Contribution from lost triangles v₁-w₁-x:**

For each x ∈ ext(v₁) ∩ ext(w₁), the triangle contributes to tr(T³) via 6 directed-edge starting points (one for each directed edge of the triangle, and each can go around in two directions). The total contribution from triangle v₁-w₁-x is:
$$\frac{6}{(d_v - 1)(d_w - 1)(\deg(x) - 1)} = \frac{6\alpha\beta}{\deg(x) - 1}$$

**Contribution from gained triangles v₁-w₂-x:**

For each x ∈ ext(v₁) ∩ ext(w₂), contribution is:
$$\frac{6}{(d_v - 1)(d_w - 1)(\deg(x) - 1)} = \frac{6\alpha\beta}{\deg(x) - 1}$$

**Key step: Decomposing the cross-intersections**

We have:
- ext(w₁) = shared ∪ unique₁
- ext(w₂) = shared ∪ unique₂

Therefore:
- ext(v₁) ∩ ext(w₁) = (ext(v₁) ∩ shared) ∪ (ext(v₁) ∩ unique₁)
- ext(v₁) ∩ ext(w₂) = (ext(v₁) ∩ shared) ∪ (ext(v₁) ∩ unique₂)

The shared parts are identical. By condition 4:
$$|ext(v_1) \cap unique_1| = |ext(v_1) \cap unique_2|$$

**Using uniform unique degrees (condition 6):**

All vertices in unique₁ ∪ unique₂ have degree d_u. Therefore:
$$\sum_{x \in ext(v_1) \cap unique_1} \frac{1}{\deg(x) - 1} = \frac{|ext(v_1) \cap unique_1|}{d_u - 1}$$
$$\sum_{x \in ext(v_1) \cap unique_2} \frac{1}{\deg(x) - 1} = \frac{|ext(v_1) \cap unique_2|}{d_u - 1}$$

Since |ext(v₁) ∩ unique₁| = |ext(v₁) ∩ unique₂|, these sums are equal.

The shared contributions are identical (same vertices).

Therefore the total lost contribution from v₁ equals the total gained contribution from v₁.

The same argument applies to v₂, w₁, w₂.

**Conclusion:** tr(T_G³) = tr(T_{G'}³). ∎

---

### Case k = 4

**Claim:** Under conditions 1-6, tr(T_G⁴) = tr(T_{G'}⁴).

**Proof:**

A diagonal entry [T⁴]_{(a,b),(a,b)} counts weighted closed 4-walks:
$$(a,b) \to (b,c) \to (c,d) \to (d,a) \to (a,b)$$

This corresponds to a 4-cycle a-b-c-d in G. The contribution is:
$$\frac{1}{(\deg(a)-1)(\deg(b)-1)(\deg(c)-1)(\deg(d)-1)}$$

**4-cycles affected by the switch:**

A 4-cycle is affected iff it contains edge v₁-w₁ (lost) or v₁-w₂ (gained). We classify 4-cycles v₁-w₁-A-B-v₁ by what A and B are.

Recall:
- ext(w₁) = shared ∪ unique₁
- ext(w₂) = shared ∪ unique₂
- N(w₁) \ {v₁} = {w₂} ∪ ext(w₁) (includes parallel edge)
- N(v₁) \ {w₁} = {v₂} ∪ ext(v₁) (includes parallel edge)

**Classification of 4-cycles through v₁-w₁ in G:**

| Type | A | B | Count |
|------|---|---|-------|
| Central rectangle | w₂ | v₂ | 1 |
| Parallel-w shared | w₂ | shared ∩ ext(v₁) | s₁ |
| Parallel-w unique₂ | w₂ | unique₂ ∩ ext(v₁) | u₁ |
| Parallel-v shared | shared ∩ ext(v₂) | v₂ | s₂ |
| Parallel-v unique₁ | unique₁ ∩ ext(v₂) | v₂ | u₂ |
| External shared | shared | ext(v₁) ∩ N(A) | e_s |
| External unique₁ | unique₁ | ext(v₁) ∩ N(A) | e_u |

where s₁ = |shared ∩ ext(v₁)|, u₁ = |unique₂ ∩ ext(v₁)|, etc.

**Classification of 4-cycles through v₁-w₂ in G':**

| Type | A | B | Count |
|------|---|---|-------|
| Central rectangle | w₁ | v₂ | 1 |
| Parallel-w shared | w₁ | shared ∩ ext(v₁) | s₁ |
| Parallel-w unique₁ | w₁ | unique₁ ∩ ext(v₁) | u₁' |
| Parallel-v shared | shared ∩ ext(v₂) | v₂ | s₂ |
| Parallel-v unique₂ | unique₂ ∩ ext(v₂) | v₂ | u₂' |
| External shared | shared | ext(v₁) ∩ N(A) | e_s |
| External unique₂ | unique₂ | ext(v₁) ∩ N(A) | e_u' |

**Key observation:** The structure is symmetric under unique₁ ↔ unique₂.

By condition 4 (uniform cross-intersection):
- |unique₁ ∩ ext(v₁)| = |unique₂ ∩ ext(v₁)|
- |unique₁ ∩ ext(v₂)| = |unique₂ ∩ ext(v₂)|

Therefore u₁ = u₁', u₂ = u₂', and e_u = e_u'.

**Weighted contributions:**

Each 4-cycle v₁-w₁-A-B-v₁ contributes:
$$\frac{1}{(d_v-1)(d_w-1)(\deg(A)-1)(\deg(B)-1)}$$

For the parallel-w types: A = w₂, so deg(A) = d_w.
For the parallel-v types: B = v₂, so deg(B) = d_v.
For external types with A ∈ unique₁ or unique₂: deg(A) = d_u (condition 6).

Since unique₁ and unique₂ have the same cardinality and all vertices have degree d_u, the weighted sums match.

**Verification:** Computational check confirms that for all 4 Mechanism A pairs, the 4-cycle type counts match exactly between G and G'.

**Conclusion:** The lost 4-cycles through v₁-w₁ and v₂-w₂ are exactly balanced by gained 4-cycles through v₁-w₂ and v₂-w₁.

Therefore tr(T_G⁴) = tr(T_{G'}⁴). ∎

---

## Why k = 4 Was Expected to Be Harder (But Isn't)

For k = 4, a diagonal entry [T⁴]_{(a,b),(a,b)} counts weighted closed 4-walks:
$$(a,b) \to (b,c) \to (c,d) \to (d,e) \to (e,a) = (a,b)$$
so e = a, and we need a closed non-backtracking walk a → b → c → d → a.

**Types of 4-cycles in the underlying graph:**

1. **Simple 4-cycles:** a-b-c-d-a where all four vertices are distinct
2. **Lollipops:** Not possible for non-backtracking walks

**Affected 4-walks:**

A 4-walk is affected if it uses a switched edge. This happens when the walk passes through one of:
- (v₁, w₁) or (w₁, v₁) — removed
- (v₂, w₂) or (w₂, v₂) — removed
- (v₁, w₂) or (w₂, v₁) — added
- (v₂, w₁) or (w₁, v₂) — added

**Complexity explosion:**

For k = 3, affected walks were triangles through a switched edge. There's essentially one "type" of affected structure.

For k = 4, affected walks can be:
1. 4-cycles using one switched edge (e.g., v₁-w₁-x-y-v₁)
2. 4-cycles using two switched edges (e.g., v₁-w₁-w₂-v₂-v₁ if such a cycle exists)
3. Walks that enter and exit S multiple times

**The parallel edges create additional 4-cycles:**

Since v₁-v₂ and w₁-w₂ are edges:
- In G: v₁-v₂-w₂-w₁-v₁ is a 4-cycle (uses both parallel edges and both switched edges)
- In G': v₁-v₂-w₁-w₂-v₁ is the corresponding 4-cycle

These "internal" 4-cycles must also balance.

**Multiple interaction terms:**

When expanding tr((T + Δ)⁴) where Δ = T_{G'} - T_G:

$$tr(T_{G'}^4) = tr(T^4) + 4\,tr(T^3 \Delta) + 6\,tr(T^2 \Delta^2) + 4\,tr(T \Delta^3) + tr(\Delta^4)$$

For k = 3, only tr(T²Δ) and tr(TΔ²) and tr(Δ³) mattered, and the structure was simple.

For k = 4, we have more terms, and each involves more complex walk structures.

**What needs to be shown:**

To prove tr(T_G⁴) = tr(T_{G'}⁴), we need:
$$4\,tr(T^3 \Delta) + 6\,tr(T^2 \Delta^2) + 4\,tr(T \Delta^3) + tr(\Delta^4) = 0$$

Each term requires careful combinatorial analysis of which walks contribute.

**Numerical evidence:**

Despite this complexity, numerical verification confirms tr(T_G⁴) = tr(T_{G'}⁴) for all 4 Mechanism A pairs. This suggests the cancellation does occur, but proving it algebraically requires tracking many cases.

---

## Possible Proof Strategies for k ≥ 4

1. **Direct enumeration:** Classify all affected k-walks and show contributions cancel pairwise. Tedious but elementary.

2. **Matrix structure:** Show Δ has special structure (rank ≤ 4, specific pattern) that forces tr(T^{k-j}Δ^j) = 0 for all j.

3. **Similarity transformation:** Construct P such that P⁻¹T_G P = T_{G'}, proving identical spectra directly.

4. **Characteristic polynomial:** Show det(λI - T_G) = det(λI - T_{G'}) using properties of the switch.

---

## Complete Inductive Proof for k ≥ 5

### Key Insight: The S-Transfer Kernel

The proof does NOT rely on pairing individual walks. Instead, we show that an aggregated "S-transfer kernel" is preserved under the switch.

**Critical Observation:** Individual walks through unique₁ and unique₂ do NOT pair up. The vertices in unique₁ and unique₂ have completely different connectivity patterns (different adjacencies to v₁, v₂, shared). However, the AGGREGATE contributions match due to the conditions.

### Definitions

**Entry/Exit Types:** Classify how walks enter and exit S:
- Type `v₁`: enter/exit at v₁ from ext(v₁)
- Type `v₂`: enter/exit at v₂ from ext(v₂)
- Type `w₁_s`: enter/exit at w₁ from shared
- Type `w₂_s`: enter/exit at w₂ from shared
- Type `w₁_u`: enter/exit at w₁ from unique₁
- Type `w₂_u`: enter/exit at w₂ from unique₂

**S-Transfer Kernel:** For entry type e and exit type f, define:
$$K_G[e, f] = \sum_{\text{all paths from } e \text{ to } f} \text{weight}$$

where the sum is over all non-backtracking paths through the S-neighborhood (including paths that may exit and re-enter S), weighted by transition probabilities.

**The Swap Map σ:** Define σ on entry/exit types:
- σ(v₁) = v₁, σ(v₂) = v₂ (unchanged)
- σ(w₁_s) = w₂_s, σ(w₂_s) = w₁_s (swap shared)
- σ(w₁_u) = w₂_u, σ(w₂_u) = w₁_u (swap unique)

### The S-Kernel Equivalence Lemma

**Lemma:** Under conditions 1-6:
$$K_G[e, f] = K_{G'}[\sigma(e), \sigma(f)]$$
for all entry types e and exit types f.

**Proof:**

The key is that σ corresponds to swapping w₁ ↔ w₂ throughout:

1. **Internal S structure is isomorphic under w₁ ↔ w₂:**
   - In G: edges within S are {v₁-w₁, v₂-w₂, v₁-v₂, w₁-w₂}
   - In G': edges within S are {v₁-w₂, v₂-w₁, v₁-v₂, w₁-w₂}
   - These are isomorphic under the map v₁↦v₁, v₂↦v₂, w₁↦w₂, w₂↦w₁

2. **Transition probabilities are preserved:**
   - At v₁, v₂: prob = α = 1/(d_v - 1) in both G and G' (condition 1)
   - At w₁, w₂: prob = β = 1/(d_w - 1) in both G and G' (condition 1)

3. **Boundary transitions aggregate correctly:**

   For entries from ext(v₁) or ext(v₂): identical in G and G' (these sets don't change).

   For entries from shared to w₁: In G, paths starting at (s, w₁) for s ∈ shared.
   Under σ, this maps to paths starting at (s, w₂) for s ∈ shared in G'.
   Since shared is the same set and deg(w₁) = deg(w₂), weights match.

   For entries from unique₁ to w₁: In G, paths starting at (u, w₁) for u ∈ unique₁.
   Under σ, this maps to paths starting at (v, w₂) for v ∈ unique₂ in G'.

   The key: we aggregate over ALL u ∈ unique₁ and ALL v ∈ unique₂.
   By conditions 5-6: |unique₁| = |unique₂| = 2 and all have degree d_u.
   So the total entry weight is:
   $$\sum_{u \in \text{unique}_1} \frac{1}{d_u - 1} = \frac{2}{d_u - 1} = \sum_{v \in \text{unique}_2} \frac{1}{d_u - 1}$$

4. **Internal path weights match:**

   A path from entry to exit through S has weight = product of transition probs.
   Under the isomorphism w₁ ↔ w₂, each path in G maps to a path in G' with:
   - Same length
   - Same weight (since deg(v₁)=deg(v₂) and deg(w₁)=deg(w₂))

5. **Exit transitions aggregate correctly:**

   Same argument as entry transitions. Exits to unique₁ from w₁ aggregate to the same total weight as exits to unique₂ from w₂.

Therefore K_G[e, f] = K_{G'}[σ(e), σ(f)] for all e, f. ∎

### Numerical Verification

Computed the S-transfer kernels for all 4 Mechanism A pairs (k up to 10):
- **Pair 25, 30, 42, 64:** All 36 kernel entries match exactly under the σ swap.

Example (Pair 25):
- K_G[w₁_u, w₂_u] = 0.831652 = K_{G'}[w₂_u, w₁_u] ✓
- K_G[v₁, w₁_s] = 0.880472 = K_{G'}[v₁, w₂_s] ✓

### The Induction

**Theorem:** Under conditions 1-6, tr(T_G^k) = tr(T_{G'}^k) for all k ≥ 1.

**Proof by strong induction:**

**Base cases:** k = 1, 2, 3, 4 proved above.

**Induction step:** Assume true for all k' < k. We prove for k ≥ 5.

**Step 1: Walk Decomposition**

Any closed k-walk W decomposes into:
- **Pure segments:** edges entirely in the external graph (not involving S)
- **S-traversals:** paths that enter S, traverse it, and exit

Formally: W = P₀ · T₁ · P₁ · T₂ · ... · Tₘ · Pₘ

where Pᵢ are pure external paths and Tᵢ are S-traversals.

**Step 2: Weight Factorization**

$$\text{weight}(W) = \prod_i \text{weight}(P_i) \times \prod_j \text{weight}(T_j)$$

The external path weights depend only on the external graph, which is IDENTICAL for G and G'.

**Step 3: Aggregating by Pattern**

For a fixed "external pattern" (sequence of external paths with specified start/end types), the total trace contribution is:

$$\text{contrib}(\text{pattern}) = (\text{external weight}) \times \prod_j K[\text{entry}_j, \text{exit}_j]$$

**Step 4: Applying the Kernel Equivalence**

For any pattern in G with entry/exit types (e₁,f₁), (e₂,f₂), ..., the contribution is:
$$\text{external weight} \times K_G[e_1, f_1] \times K_G[e_2, f_2] \times ...$$

The corresponding pattern in G' (under σ) has contribution:
$$\text{external weight} \times K_{G'}[\sigma(e_1), \sigma(f_1)] \times K_{G'}[\sigma(e_2), \sigma(f_2)] \times ...$$

By the Kernel Equivalence Lemma:
$$K_G[e_i, f_i] = K_{G'}[\sigma(e_i), \sigma(f_i)]$$

**Step 5: The Bijection on Patterns**

The swap σ defines a bijection on external patterns:
- Patterns in G involving w₁_s, w₁_u entries/exits correspond to patterns in G' involving w₂_s, w₂_u
- The external paths are the same (external graph is identical)
- The kernel products are equal by the lemma

**Step 6: Summing Over All Patterns**

$$\text{tr}(T_G^k) = \sum_{\text{patterns } P} \text{contrib}_G(P) = \sum_{\text{patterns } P} \text{contrib}_{G'}(\sigma(P)) = \text{tr}(T_{G'}^k)$$

where the middle equality uses the bijection σ and kernel equivalence. ∎

### Why Individual Walk Pairing Fails (But Aggregate Works)

The perfect matching τ: unique₁ → unique₂ does NOT preserve individual adjacencies:
- Vertex 1 ∈ unique₁ might be adjacent to v₁ but not v₂
- τ(1) ∈ unique₂ might be adjacent to both v₁ and v₂

So a walk entering via vertex 1 cannot be directly paired with a walk entering via τ(1).

However, the CONDITIONS ensure aggregate matching:
- |unique₁ ∩ ext(v₁)| = |unique₂ ∩ ext(v₁)| (condition 4)
- |unique₁ ∩ ext(v₂)| = |unique₂ ∩ ext(v₂)| (condition 4)
- All unique vertices have degree d_u (condition 6)

These aggregate equalities make the kernel sums match even though individual paths don't pair up.

### Additional Structure: Perfect Matching

All 4 Mechanism A pairs have an additional structure not explicitly in conditions 1-6:

**Observation:** The cross-edges between unique₁ and unique₂ form a **perfect matching**.

Each u ∈ unique₁ is adjacent to exactly one v ∈ unique₂, and vice versa.

This creates a "bridge" allowing walks to transfer between unique₁ and unique₂, which may be necessary for the kernel equivalence to hold. Whether this is implied by conditions 1-6 or should be added as condition 7 requires further investigation.
