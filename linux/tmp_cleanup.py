#!/usr/bin/env python3
import subprocess
import re
import argparse
from collections import defaultdict
from datetime import datetime

def log(msg):
    now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"🧹 [{now}] {msg}")

def parse_lsof_line(line):
    # Match lines with deleted files and extract key fields
    match = re.match(
        r"^\S+\s+(\d+)\s+\S+\s+(\d+)[rwu]?\s+\S+\s+(\d+)\s+(\d+)\s+(.* \(deleted\))$",
        line
    )
    if match:
        pid, fd, size, inode, path = match.groups()
        return {
            'pid': pid,
            'fd': fd,
            'size': int(size),
            'inode': inode,
            'path': path
        }
    return None

def get_deleted_tmp_files():
    try:
        output = subprocess.check_output(['sudo', 'lsof', '+L1', '/tmp'], text=True)
    except subprocess.CalledProcessError:
        log("Failed to run lsof. Are you root?")
        return []

    files = []
    for line in output.splitlines()[1:]:
        if '(deleted)' not in line:
            continue
        parsed = parse_lsof_line(line)
        if parsed:
            files.append(parsed)
    return files

def group_by_inode(files):
    inode_map = defaultdict(list)
    for f in files:
        inode_map[f['inode']].append(f)
    return inode_map

def truncate_inode_group(inode, group, dry_run=False):
    f = group[0]
    proc_path = f"/proc/{f['pid']}/fd/{f['fd']}"
    if dry_run:
        log(f"🧪 Dry-run: would truncate inode {inode} → {f['path']}")
        return
    try:
        subprocess.run(['sudo', 'truncate', '-s', '0', proc_path], check=True)
        log(f"✅ Truncated inode {inode} → {f['path']}")
    except subprocess.CalledProcessError:
        log(f"❌ Failed to truncate inode {inode} at {proc_path}")

def main():
    parser = argparse.ArgumentParser(description="Truncate deleted-but-open files in /tmp")
    parser.add_argument('--regex', type=str,
        default=r"/tmp/\.org\.chromium\.Chromium\.[^ ]*(/[^ ]*)*( \(deleted\))?",
        help="Regex to match file paths (Python-style)"
    )
    parser.add_argument('--dry-run', action='store_true',
        help="Preview actions without truncating"
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

    total = sum(f['size'] for f in filtered)
    inode_map = group_by_inode(filtered)

    log(f"Matched {len(filtered)} files across {len(inode_map)} inodes → {total / (1024**2):.2f} MB")
    log("Matched paths:")
    for f in filtered:
        print(f"   📄", f['inode'], f['path'])

    confirm = input("Proceed with truncation? (y/N): ").strip().lower()
    if confirm == 'y':
        for inode, group in inode_map.items():
            truncate_inode_group(inode, group, dry_run=args.dry_run)
    else:
        log("Aborted. No files truncated.")

if __name__ == "__main__":
    main()