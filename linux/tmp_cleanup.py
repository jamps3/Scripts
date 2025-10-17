#!/usr/bin/env python3
import argparse
import re
import subprocess
from collections import defaultdict
from datetime import datetime


def log(msg):
    now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"🧹 [{now}] {msg}")


def get_deleted_tmp_files():
    try:
        output = subprocess.check_output(["sudo", "lsof", "+L1", "/tmp"], text=True)
    except subprocess.CalledProcessError:
        log("Failed to run lsof. Are you root?")
        return []

    files = []
    for line in output.splitlines()[1:]:
        parts = re.split(r"\s+", line)
        if len(parts) < 9:
            continue
        pid = parts[1]
        fd = re.sub(r'[^\d]', '', parts[3])
        size = parts[6]
        inode = parts[7]
        path = " ".join(parts[8:])
        if "(deleted)" in line and not fd.startswith("txt"):
            files.append(
                {"pid": pid, "fd": fd, "size": int(size), "inode": inode, "path": path}
            )
    return files


def group_by_inode(files):
    inode_map = defaultdict(list)
    for f in files:
        inode_map[f["inode"]].append(f)
    return inode_map


def truncate_inode_group(inode, group, dry_run=False):
    f = group[0]
    proc_path = f"/proc/{f['pid']}/fd/{f['fd']}"
    if dry_run:
        log(f"🧪 Dry-run: would truncate inode {inode} → {f['path']}")
        return
    try:
        subprocess.run(["sudo", "truncate", "-s", "0", proc_path], check=True)
        log(f"✅ Truncated inode {inode} → {f['path']}")
    except subprocess.CalledProcessError:
        log(f"❌ Failed to truncate inode {inode} at {proc_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Truncate deleted-but-open files in /tmp"
    )
    parser.add_argument(
        "--regex",
        type=str,
        default=r"/tmp/\.org\.chromium\.Chromium\.[^ ]*(/[^ ]*)*( \(deleted\))?",
        help="Regex to match file paths (Python-style)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview actions without truncating"
    )
    args = parser.parse_args()

    log("Scanning for deleted-but-open files in /tmp…")
    files = get_deleted_tmp_files()
    if not files:
        log("No deleted files found.")
        return

    filtered = [f for f in files if re.search(args.regex, f['path'])]
    if not filtered:
        log(f"No files matched regex: {args.regex}")
        return

    total = sum(f["size"] for f in filtered)
    inode_map = group_by_inode(filtered)

    log(
        f"Matched {len(filtered)} files across {len(inode_map)} inodes → {total / (1024**2):.2f} MB"
    )

    for i, (inode, group) in enumerate(inode_map.items(), 1):
        size = sum(f["size"] for f in group)
        paths = sorted(set(f["path"] for f in group))
        log(f"{i}. Inode {inode} → {size / (1024**2):.2f} MB across {len(group)} FDs")
        for p in paths:
            print(f"   📄 {p}")

    confirm = input("Proceed with truncation? (y/N): ").strip().lower()
    if confirm == "y":
        for inode, group in inode_map.items():
            truncate_inode_group(inode, group, dry_run=args.dry_run)
    else:
        log("Aborted. No files truncated.")


if __name__ == "__main__":
    main()
