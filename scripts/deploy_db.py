#!/usr/bin/env python3
"""Deploy PostgreSQL database to Fly.io as SQLite.

Exports local PostgreSQL to SQLite, splits into chunks, uploads via fly sftp,
and reassembles on the remote server. Resumable - tracks uploaded chunks.

Usage:
    python scripts/deploy_db.py [--chunk-size MB] [--reset]
    just deploy-db
"""

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

CHUNK_SIZE_MB = 50  # Default chunk size
REMOTE_DATA_DIR = "/data"
REMOTE_DB_PATH = f"{REMOTE_DATA_DIR}/smol.db"
MANIFEST_FILE = ".deploy_manifest.json"


def run(cmd: list[str], check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    """Run a command with output."""
    if capture:
        return subprocess.run(cmd, check=check, capture_output=True, text=True)
    return subprocess.run(cmd, check=check)


def get_file_hash(path: Path, chunk_size: int = 8192) -> str:
    """Compute MD5 hash of a file."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def export_to_sqlite(sqlite_path: Path, max_n: int = 10) -> None:
    """Export PostgreSQL database to SQLite using export_to_sqlite.py."""
    print(f"Exporting PostgreSQL to SQLite (max_n={max_n})...")

    result = run(
        ["uv", "run", "python", "scripts/export_to_sqlite.py",
         "--output", str(sqlite_path), "--max-n", str(max_n)],
        check=False,
    )

    if result.returncode != 0:
        print("Export failed!")
        sys.exit(1)

    print(f"  Size: {sqlite_path.stat().st_size / (1024*1024):.1f} MB")


def split_file(source: Path, chunk_dir: Path, chunk_size_mb: int) -> list[dict]:
    """Split a file into chunks and return manifest."""
    chunk_size = chunk_size_mb * 1024 * 1024
    chunks = []

    file_size = source.stat().st_size
    total_chunks = (file_size + chunk_size - 1) // chunk_size

    print(f"Splitting {source.name} into {total_chunks} chunks of {chunk_size_mb}MB...")

    chunk_dir.mkdir(parents=True, exist_ok=True)

    with open(source, "rb") as f:
        chunk_num = 0
        while True:
            data = f.read(chunk_size)
            if not data:
                break

            chunk_name = f"chunk_{chunk_num:04d}"
            chunk_path = chunk_dir / chunk_name

            with open(chunk_path, "wb") as cf:
                cf.write(data)

            chunk_hash = hashlib.md5(data).hexdigest()
            chunks.append({
                "name": chunk_name,
                "size": len(data),
                "hash": chunk_hash,
                "uploaded": False,
            })

            chunk_num += 1
            progress = (chunk_num / total_chunks) * 100
            print(f"  Split chunk {chunk_num}/{total_chunks} ({progress:.0f}%)", end="\r")

    print()
    return chunks


def load_manifest(manifest_path: Path) -> dict | None:
    """Load existing manifest for resumability."""
    if manifest_path.exists():
        with open(manifest_path) as f:
            return json.load(f)
    return None


def save_manifest(manifest_path: Path, manifest: dict) -> None:
    """Save manifest for resumability."""
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)


def upload_chunk(chunk_path: Path, remote_dir: str) -> bool:
    """Upload a single chunk via fly sftp."""
    remote_path = f"{remote_dir}/{chunk_path.name}"

    # Use fly sftp shell with heredoc
    sftp_commands = f"put {chunk_path} {remote_path}\n"

    result = subprocess.run(
        ["fly", "sftp", "shell"],
        input=sftp_commands,
        capture_output=True,
        text=True,
    )

    return result.returncode == 0


def check_remote_chunk(chunk_name: str, remote_dir: str, expected_size: int) -> bool:
    """Check if a chunk exists on remote with correct size."""
    result = subprocess.run(
        ["fly", "ssh", "console", "-C", f"stat -c %s {remote_dir}/{chunk_name} 2>/dev/null || echo 0"],
        capture_output=True,
        text=True,
    )

    try:
        remote_size = int(result.stdout.strip())
        return remote_size == expected_size
    except ValueError:
        return False


def upload_chunks(chunk_dir: Path, manifest: dict, manifest_path: Path, workers: int = 4) -> None:
    """Upload all chunks with progress tracking (parallel)."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading

    chunks = manifest["chunks"]
    remote_dir = f"{REMOTE_DATA_DIR}/chunks"

    # Create remote chunk directory
    run(["fly", "ssh", "console", "-C", f"mkdir -p {remote_dir}"], check=False)

    total = len(chunks)
    pending = [(i, c) for i, c in enumerate(chunks) if not c["uploaded"]]
    done = total - len(pending)

    print(f"Uploading {len(pending)} chunks ({done} already done) with {workers} workers...", flush=True)

    if not pending:
        return

    start_time = time.time()
    lock = threading.Lock()
    completed = [0]
    bytes_uploaded = [0]

    def upload_one(idx_chunk):
        idx, chunk = idx_chunk
        chunk_path = chunk_dir / chunk["name"]

        # Check if already exists on remote
        if check_remote_chunk(chunk["name"], remote_dir, chunk["size"]):
            return idx, True, chunk["size"], "exists"

        success = upload_chunk(chunk_path, remote_dir)
        return idx, success, chunk["size"] if success else 0, "uploaded" if success else "failed"

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(upload_one, ic): ic for ic in pending}

        for future in as_completed(futures):
            idx, success, size, status = future.result()
            chunk = chunks[idx]

            with lock:
                if success:
                    chunk["uploaded"] = True
                    completed[0] += 1
                    bytes_uploaded[0] += size
                    save_manifest(manifest_path, manifest)

                elapsed = time.time() - start_time
                rate = bytes_uploaded[0] / elapsed / (1024 * 1024) if elapsed > 0 else 0
                pct = 100 * (done + completed[0]) / total

                print(f"  {done + completed[0]}/{total} ({pct:.0f}%) - {chunk['name']}: {status} - {rate:.1f} MB/s", flush=True)

    # Verify all uploaded
    failed = [c for c in chunks if not c["uploaded"]]
    if failed:
        print(f"\nWarning: {len(failed)} chunks failed to upload. Run again to retry.", flush=True)
        sys.exit(1)


def reassemble_remote(manifest: dict) -> None:
    """Reassemble chunks on the remote server."""
    print("Reassembling database on remote server...")

    chunks = manifest["chunks"]
    remote_dir = f"{REMOTE_DATA_DIR}/chunks"
    temp_db = f"{REMOTE_DATA_DIR}/smol_new.db"

    # Build cat command for all chunks in order
    chunk_files = " ".join(f"{remote_dir}/{c['name']}" for c in chunks)

    # Reassemble and swap
    commands = f"""
        echo "Concatenating chunks..."
        cat {chunk_files} > {temp_db}

        echo "Checking file size..."
        ls -lh {temp_db}

        echo "Swapping database files..."
        mv {REMOTE_DB_PATH} {REMOTE_DB_PATH}.bak 2>/dev/null || true
        mv {temp_db} {REMOTE_DB_PATH}

        echo "Cleaning up chunks..."
        rm -rf {remote_dir}
        rm -f {REMOTE_DB_PATH}.bak

        echo "Done!"
    """

    result = run(["fly", "ssh", "console", "-C", f"bash -c '{commands}'"], check=False)

    if result.returncode != 0:
        print("Remote reassembly failed!")
        sys.exit(1)

    print("Database deployed successfully!")


def cleanup_local(chunk_dir: Path, manifest_path: Path) -> None:
    """Clean up local temporary files."""
    print("Cleaning up local files...")

    if chunk_dir.exists():
        for f in chunk_dir.iterdir():
            f.unlink()
        chunk_dir.rmdir()

    if manifest_path.exists():
        manifest_path.unlink()


def main():
    parser = argparse.ArgumentParser(description="Deploy database to Fly.io")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE_MB,
                        help=f"Chunk size in MB (default: {CHUNK_SIZE_MB})")
    parser.add_argument("--max-n", type=int, default=10,
                        help="Maximum n to export (default: 10)")
    parser.add_argument("--reset", action="store_true",
                        help="Reset and start fresh (ignore previous progress)")
    parser.add_argument("--skip-export", action="store_true",
                        help="Skip PostgreSQL export (use existing smol.db)")
    parser.add_argument("--sqlite-path", type=str, default="smol.db",
                        help="Path to SQLite file (default: smol.db)")
    args = parser.parse_args()

    sqlite_path = Path(args.sqlite_path)
    chunk_dir = Path(".deploy_chunks")
    manifest_path = Path(MANIFEST_FILE)

    # Reset if requested
    if args.reset:
        cleanup_local(chunk_dir, manifest_path)

    # Check for existing manifest (resumability)
    manifest = load_manifest(manifest_path)

    if manifest and not args.reset:
        print("Resuming previous deployment...")
        print(f"  Source: {manifest['source']}")
        print(f"  Chunks: {sum(1 for c in manifest['chunks'] if c['uploaded'])}/{len(manifest['chunks'])} uploaded")
    else:
        # Fresh start
        if not args.skip_export:
            export_to_sqlite(sqlite_path, args.max_n)

        if not sqlite_path.exists():
            print(f"Error: SQLite file not found at {sqlite_path}")
            sys.exit(1)

        # Split into chunks
        chunks = split_file(sqlite_path, chunk_dir, args.chunk_size)

        manifest = {
            "source": str(sqlite_path),
            "source_hash": get_file_hash(sqlite_path),
            "source_size": sqlite_path.stat().st_size,
            "chunk_size_mb": args.chunk_size,
            "chunks": chunks,
        }
        save_manifest(manifest_path, manifest)

    # Upload chunks
    upload_chunks(chunk_dir, manifest, manifest_path)

    # Reassemble on remote
    reassemble_remote(manifest)

    # Cleanup
    cleanup_local(chunk_dir, manifest_path)

    print("\nDeployment complete!")
    print(f"  Database size: {manifest['source_size'] / (1024*1024):.1f} MB")
    print(f"  Remote path: {REMOTE_DB_PATH}")


if __name__ == "__main__":
    main()
