# SMOL Deployment

## Current Status

**Deployed:** https://smol-graphs-db.fly.dev/
**Database:** SQLite, 889 MB (n≤9, 288,266 graphs)
**Volume:** 10GB persistent storage
**Cost:** ~$2-3/month

## Architecture

```
┌─────────────────────────────────┐
│         Fly.io Machine          │
│  ┌───────────┐  ┌────────────┐  │
│  │  FastAPI  │──│  SQLite DB │  │
│  │  uvicorn  │  │  (volume)  │  │
│  └───────────┘  └────────────┘  │
└─────────────────────────────────┘
           │
    Fly.io Proxy (HTTPS)
           │
  smol-graphs-db.fly.dev
```

## Deployment Process

### 1. Export PostgreSQL to SQLite

```bash
# Export with all data up to n=9
just deploy-db --max-n 9

# Or for all data (n≤10)
just deploy-db
```

This script:
1. Creates `smol.db` from PostgreSQL data
2. Verifies row counts
3. Splits into 50MB chunks
4. Uploads chunks to Fly.io via SFTP
5. Concatenates chunks on remote server
6. Swaps database files atomically

### 2. Deploy Code Changes

```bash
# Deploy latest code
fly deploy -a smol-graphs-db

# Check status
fly status -a smol-graphs-db
fly logs -a smol-graphs-db
```

## Database Management

### Check Database on Server

```bash
# View file size
fly ssh console -a smol-graphs-db -C "ls -lh /data/smol.db"

# Check volume usage
fly ssh console -a smol-graphs-db -C "df -h /data"

# Query database
fly ssh console -a smol-graphs-db -C "sqlite3 /data/smol.db 'SELECT COUNT(*) FROM graphs;'"
```

### Update Database

```bash
# Export and deploy updated database
just deploy-db --max-n 9
```

### Manual Upload (if needed)

```bash
# SSH into machine
fly ssh console -a smol-graphs-db

# Check volume
ls -lh /data/
df -h /data

# For manual SFTP upload:
fly ssh sftp shell -a smol-graphs-db
put smol.db /data/smol.db
quit
```

## Configuration

### fly.toml

```toml
app = "smol-graphs-db"
primary_region = "iad"

[build]

[env]
  DATABASE_URL = "sqlite:////data/smol.db"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = false
  auto_start_machines = true
  min_machines_running = 1

[mounts]
  source = "smol_data"
  destination = "/data"

[[vm]]
  memory = "512mb"
  cpu_kind = "shared"
  cpus = 1
```

### Volume

```bash
# List volumes
fly volumes list -a smol-graphs-db

# Extend volume (can only increase, not decrease)
fly volumes extend vol_vgjx6072y8mwdl1v -s 20 -a smol-graphs-db
```

## Monitoring

### Logs

```bash
# Tail logs
fly logs -a smol-graphs-db

# With app name filtering
fly logs -a smol-graphs-db --app smol-graphs-db
```

### Metrics

```bash
# App status
fly status -a smol-graphs-db

# Scale info
fly scale show -a smol-graphs-db

# Volume usage
fly ssh console -a smol-graphs-db -C "df -h /data"
```

## Maintenance

### Restart Application

```bash
fly apps restart smol-graphs-db
```

### Update Code

```bash
git pull
fly deploy -a smol-graphs-db
```

### Backup Database

```bash
# Download via SFTP
fly ssh sftp shell -a smol-graphs-db
get /data/smol.db ./smol-backup-$(date +%Y%m%d).db
quit

# Or via SCP (requires proxy setup)
fly proxy 10022:22 -a smol-graphs-db &
scp -P 10022 root@localhost:/data/smol.db ./backup.db
```

## Cost Breakdown

| Resource | Spec | Cost/Month |
|----------|------|------------|
| Compute | shared-cpu-1x, 512MB | ~$2.00 |
| Volume | 10GB | ~$1.50 |
| **Total** | | **~$3.50** |

Fly.io provides $5/month free allowance, so actual cost is near zero.

## Future: Adding n=10

To add all n=10 graphs (~12M total):

1. **Local generation:**
   ```bash
   just generate 10 10
   uv run python scripts/refresh_stats.py
   ```

2. **Export and deploy:**
   ```bash
   just deploy-db  # Without --max-n flag
   ```

3. **Possible scaling needs:**
   - Increase volume to 40GB: `fly volumes extend vol_xxx -s 40`
   - Increase RAM to 1GB in `fly.toml`
   - Monitor performance and adjust

Estimated cost with n=10:
- Compute: ~$3/month (1GB RAM)
- Volume (40GB): ~$6/month
- **Total: ~$9/month**

## Troubleshooting

### Database Upload Fails

If chunked upload fails:
```bash
# Check which chunks uploaded
fly ssh console -a smol-graphs-db -C "ls -lh /data/chunks/"

# Re-run deployment (resumes from last successful chunk)
just deploy-db --max-n 9
```

### App Won't Start

```bash
# Check logs
fly logs -a smol-graphs-db

# Verify database exists
fly ssh console -a smol-graphs-db -C "ls -lh /data/smol.db"

# Restart
fly apps restart smol-graphs-db
```

### Out of Memory

Increase VM memory in `fly.toml`:
```toml
[[vm]]
  memory = "1gb"  # or "2gb"
```

Then redeploy:
```bash
fly deploy -a smol-graphs-db
```
