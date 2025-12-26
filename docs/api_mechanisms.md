# Switching Mechanisms API

## Design Philosophy

**Firehose endpoints** - Return complete datasets that clients can filter/process locally rather than many fine-grained endpoints.

## Core Endpoints

### 1. Get all mechanisms for a graph

```
GET /api/graph/{graph6}/mechanisms?matrix_type=adj
```

**Response:**
```json
{
  "graph6": "H?qbF?",
  "n": 9,
  "m": 15,
  "mechanisms": {
    "adj": [
      {
        "mate": "HCOfF?",
        "mechanism": "gm",
        "config": {
          "switching_set": [0, 1, 2],
          "partition": [[7], [3, 4, 5, 6]],
          "num_classes": 2
        }
      },
      {
        "mate": "H?otry",
        "mechanism": "nbl_2edge",
        "config": {
          "v1": 2, "v2": 5, "w1": 3, "w2": 7
        }
      }
    ]
  }
}
```

### 2. Bulk mechanism data (firehose)

```
GET /api/mechanisms/dump?n=9&matrix_type=adj&mechanism=gm
```

**Returns:** Newline-delimited JSON stream of ALL matching mechanisms
```jsonl
{"g1":"H?qbF?","g2":"HCOfF?","type":"gm","config":{...}}
{"g1":"H?otry","g2":"HCQfNo","type":"gm","config":{...}}
...
```

**Query params:**
- `n` - vertex count (optional, default: all)
- `matrix_type` - adj/kirchhoff/signless/etc (optional, default: all)
- `mechanism` - gm/nbl_2edge/etc (optional, default: all)
- `format` - json/jsonl/csv (default: jsonl for streaming)

### 3. Mechanism statistics

```
GET /api/stats/mechanisms?n=9&matrix_type=adj
```

**Response:**
```json
{
  "n": 9,
  "matrix_type": "adj",
  "total_graphs": 51039,
  "graphs_with_mates": 51039,
  "mechanisms": {
    "gm": {
      "graphs": 22021,
      "coverage": 0.431,
      "pairs": 11630,
      "avg_mates_per_graph": 1.06
    },
    "nbl_2edge": {
      "graphs": 0,
      "coverage": 0.0,
      "pairs": 0
    },
    "unknown": {
      "graphs": 29018,
      "coverage": 0.569,
      "pairs": 20418
    }
  },
  "mechanism_overlap": {
    "gm_only": 22021,
    "gm_and_nbl": 0,
    "multiple_mechanisms": 0
  }
}
```

### 4. Random examples

```
GET /api/mechanisms/examples?mechanism=gm&n=9&limit=10
```

**Response:**
```json
{
  "mechanism": "gm",
  "n": 9,
  "examples": [
    {
      "g1": "H?qbF?",
      "g2": "HCOfF?",
      "config": {...}
    },
    // ... 9 more
  ]
}
```

### 5. Mechanism by pair (detail)

```
GET /api/pair/mechanisms?g1={graph6}&g2={graph6}&matrix_type=adj
```

**Response:**
```json
{
  "g1": "H?qbF?",
  "g2": "HCOfF?",
  "matrix_type": "adj",
  "cospectral": true,
  "mechanisms": [
    {
      "type": "gm",
      "config": {
        "switching_set": [0, 1, 2],
        "partition": [[7], [3, 4, 5, 6]],
        "num_classes": 2
      }
    }
  ]
}
```

## Bulk Export Endpoint

```
GET /api/export/mechanisms?n=9&format=csv
```

Downloads complete CSV of all mechanisms at n=9:
```csv
graph1,graph2,matrix_type,mechanism,switching_set,partition_1,partition_2
H?qbF?,HCOfF?,adj,gm,"[0,1,2]","[7]","[3,4,5,6]"
...
```

## Implementation Notes

- All endpoints support `?format=json` or `?format=jsonl`
- Streaming endpoints (dump, export) use chunked transfer encoding
- Cache mechanism stats in materialized view, refresh hourly
- No pagination on firehose endpoints - return everything, let client filter
- For huge datasets (n=10+), consider gzip compression header

## Frontend Integration

```javascript
// Get all GM pairs at n=9 (firehose)
const response = await fetch('/api/mechanisms/dump?n=9&mechanism=gm');
const reader = response.body.getReader();
// Stream and process JSONL

// Get stats for display
const stats = await fetch('/api/stats/mechanisms?n=9&matrix_type=adj').then(r => r.json());
// Display: "43.1% explained by GM switching"

// Get mechanisms for specific graph
const mechs = await fetch('/api/graph/H?qbF?/mechanisms').then(r => r.json());
// Show badges next to cospectral mates
```
