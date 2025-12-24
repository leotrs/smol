# Switching Mechanisms Implementation Plan

## Overview

Add comprehensive switching mechanism detection, storage, and exposure to SMOL.

## Phase 1: Database (DONE - Ready to Deploy)

✓ Schema created: `sql/add_mechanisms_table.sql`
✓ Populate script: `scripts/populate_mechanisms.py`

**Deploy steps:**
```bash
# 1. Create table
psql smol < sql/add_mechanisms_table.sql

# 2. Populate GM mechanisms for n=8,9
python scripts/populate_mechanisms.py --mechanism gm --file docs/adj_n8_gm_correct.txt --matrix adj
python scripts/populate_mechanisms.py --mechanism gm --file docs/adj_n9_gm_correct.txt --matrix adj

# 3. Refresh stats
psql smol -c "SELECT refresh_mechanism_stats();"
```

**Table structure:**
- `switching_mechanisms` - Main table (graph1_id, graph2_id, matrix_type, mechanism_type, config)
- `graph_mechanism_stats` - Materialized view for fast lookups
- Indexes on all key columns + GIN index on JSONB config

## Phase 2: API Endpoints (Firehose design)

**Priority 1 - Core endpoints:**
1. `GET /api/graph/{graph6}/mechanisms` - All mechanisms for one graph
2. `GET /api/stats/mechanisms?n=9` - Statistics
3. `GET /api/mechanisms/dump?n=9&mechanism=gm` - Bulk data (JSONL stream)

**Priority 2 - Utility endpoints:**
4. `GET /api/mechanisms/examples?mechanism=gm&limit=10` - Random examples
5. `GET /api/pair/mechanisms?g1=...&g2=...` - Specific pair detail

**Priority 3 - Export:**
6. `GET /api/export/mechanisms?n=9&format=csv` - CSV download

**Implementation files:**
- `api/routes/mechanisms.py` - New router
- Update `api/main.py` to include router
- Add to `api/database.py`: helper functions for mechanism queries

## Phase 3: Frontend - Graph Detail Page

**Location:** `api/templates/graph_detail.html`

**Changes:**
1. Update cospectral mates list to show mechanism badges
2. Add mechanism detail modal/expandable
3. Show switching configuration

**Example:**
```html
<div class="cospectral-mate">
  <a href="/graph/HCOfF?">HCOfF?</a>
  <span class="badge badge-gm" title="GM Switching">GM</span>
  <button class="show-config">▾</button>
  <div class="mechanism-config" hidden>
    Switch set: {0, 1, 2}
    Partition: [{7}, {3,4,5,6}]
  </div>
</div>
```

## Phase 4: Frontend - Stats Page ✓

**Location:** `api/templates/stats.html`

**Implementation:** New "Switching Mechanisms (Adjacency)" section added with table showing:
- n (vertex count)
- Graphs with mates (total)
- GM switching count
- Coverage percentage

**Backend:** `fetch_all_mechanism_stats()` in `api/database.py` fetches aggregated data by n

**Example output:**
```
n=8:  15.8% GM (272/1,722 graphs)
n=9:  43.1% GM (22,021/51,039 graphs)
```

## Phase 5: Frontend - Search/Filter ✓

**Location:** `api/templates/home.html`

**Implementation:** Added mechanism filter dropdown to search form with options:
- ✓ GM switching
- ✓ Has any mechanism
- ✓ No known mechanism

**Backend changes:**
- Added `has_mechanism` parameter to `query_graphs()` in `api/database.py`
- Filtering logic using subqueries on `switching_mechanisms` table
- Updated `/search` and `/search/count` endpoints in `api/main.py`
- Added 6 passing tests in `TestMechanismFiltering` class

## Phase 6: Frontend - Mechanism Explorer Page (NEW)

**Route:** `/mechanisms`

**Features:**
- Tab navigation: [GM] [NBL] [Bipartite] [Unknown]
- Paginated list of pairs for selected mechanism
- Quick stats at top
- Educational content: "What is GM switching?"
- Link to interactive visualization

## Phase 7: Frontend - Visualization (Advanced)

**Interactive graph visualizer showing:**
- Switching set (red border)
- Partition classes (colored fills)
- Edges that change (dashed)
- Animation: G → apply switch → H

**Tech:** D3.js (already used for graph viz)

**Location:** New page `/visualize/mechanism?g1=...&g2=...`

## Phase 8: Additional Mechanisms

**After GM is complete, detect and add:**
1. NBL 2-edge switching (scripts already exist from NBL research)
2. Bipartite swap (k-edge generalization)
3. Seidel switching
4. Wang-Qiu-Hu (WQH) switching
5. Abiad-Haemers (AH) switching

**For each mechanism:**
- Write detector (similar to `gm_switching_proper.py`)
- Run on all pairs
- Populate mechanisms table
- Same frontend automatically works!

## Testing Plan

**Database:**
- ✓ Schema migration works
- ✓ Populate script handles duplicates
- ✓ Indexes improve query performance
- ✓ Materialized view refreshes correctly

**API:**
- Test each endpoint returns correct data
- Test JSONL streaming for large datasets
- Test query parameter combinations
- Performance test with n=9 (32k pairs)

**Frontend:**
- Test mechanism badges appear correctly
- Test config details are readable
- Test filtering by mechanism
- Test stats display correctly

## Deployment Order

1. Deploy schema (off-hours, quick)
2. Populate GM data for n=8,9 (~5 min)
3. Deploy API endpoints (no downtime)
4. Deploy frontend changes
5. Announce new feature!

## Performance Considerations

**Current scale:**
- n≤9: ~33k pairs, ~23k graphs with mechanisms
- Query time: <10ms with indexes
- Bulk export: ~1s for all n=9 pairs

**Future scale (n=10):**
- Estimated: ~500k pairs, ~1M graphs
- Need: Pagination, caching, compression
- Consider: Separate read-replica for bulk queries

## Documentation Needed

1. API docs (OpenAPI/Swagger) - auto-generated from FastAPI
2. Database schema diagram
3. "How to add a new mechanism" guide for contributors
4. Frontend component library docs
5. Tutorial: "Understanding GM Switching" (educational)

## Current Status

- [x] Schema designed
- [x] Populate script written
- [x] API design documented
- [x] Schema deployed to database
- [x] Data populated (n=8: 136 pairs, n=9: 11,630 pairs)
- [x] API endpoints implemented (graph mechanisms, stats)
- [x] Frontend updates implemented (mechanism column with badges)
- [x] Testing (16 tests added to test_api.py - all passing)
- [x] Stats page performance optimized (cached, <15ms load time)
- [x] Glossary updated with mechanism definitions and references
- [x] About page updated with mechanisms documentation
- [x] Search/filter by mechanism implemented (Phase 5)
- [ ] Deployment to production
- [ ] Expanded detector results (paused)

**Completed MVP (Phases 1-5):**
- ✓ Database schema with switching_mechanisms table
- ✓ GM switching detection for n=8,9
- ✓ API endpoints: `/api/graph/{g6}/mechanisms`, `/api/stats/mechanisms`
- ✓ Frontend: Mechanism column in cospectral mates table
- ✓ Teal badges for GM switching (light/dark mode)
- ✓ Stats page: Mechanism coverage table by vertex count (cached for performance)
- ✓ Property distributions (diameter, girth) with visual bar charts
- ✓ Tag counts display (20 graph types)
- ✓ Glossary: GM switching definition with equitable partitions
- ✓ Glossary: References section with key papers
- ✓ About page: Updated with 12.3M graphs count, complete API docs
- ✓ Search/filter by mechanism: dropdown in search form with GM/any/none options
- ✓ Tests for all new functionality (16 mechanism tests, 149 total passing)

**Next steps:**
1. Deploy to production (Fly.io)
2. Complete expanded GM detector run (if needed)
3. Add NBL 2-edge switching detection
4. Implement mechanism explorer page (Phase 6)
