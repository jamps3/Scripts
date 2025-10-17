#!/usr/bin/env python3
import argparse
import re
import subprocess
from collections import defaultdict
from datetime import datetime


def log(msg):
    now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"🧹 [{now}] {msg}")


# ---------------- FD-based cleanup ----------------


def parse_lsof_line(line):
    match = re.match(
        r"^\S+\s+(\d+)\s+\S+\s+(\d+)[rwu]?\s+\S+\s+(\d+)\s+(\d+)\s+(.* \(deleted\))$",
        line,
    )
    if match:
        pid, fd, size, inode, path = match.groups()
        return {"pid": pid, "fd": fd, "size": int(size), "inode": inode, "path": path}
    return None


def get_deleted_fd_files():
    try:
        output = subprocess.check_output(["sudo", "lsof", "+L1", "/tmp"], text=True)
    except subprocess.CalledProcessError:
        log("Failed to run lsof. Are you root?")
        return []

    files = []
    for line in output.splitlines()[1:]:
        if "(deleted)" not in line:
            continue
        parsed = parse_lsof_line(line)
        if parsed:
            files.append(parsed)
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


# ---------------- Memory-mapped cleanup ----------------


def get_mapped_deleted_files(regex):
    mapped = []
    try:
        pid_dirs = [
            d
            for d in subprocess.run(
                ["ls", "/proc"], capture_output=True, text=True
            ).stdout.splitlines()
            if d.isdigit()
        ]
    except Exception:
        return mapped

    for pid in pid_dirs:
        maps_path = f"/proc/{pid}/maps"
        try:
            with open(maps_path, "r") as f:
                for line in f:
                    if "(deleted)" in line and "/tmp/" in line:
                        parts = line.strip().split()
                        addr_range = parts[0]
                        path = " ".join(parts[5:])
                        if re.search(regex, path):
                            start, end = addr_range.split("-")
                            mapped.append(
                                {"pid": pid, "start": start, "end": end, "path": path}
                            )
        except Exception:
            continue
    return mapped


def truncate_mapped_file(entry, dry_run=False):
    map_path = f"/proc/{entry['pid']}/map_files/{entry['start']}-{entry['end']}"
    if dry_run:
        log(f"🧪 Dry-run: would truncate {map_path} → {entry['path']}")
        return
    try:
        subprocess.run(["sudo", "truncate", "-s", "0", map_path], check=True)
        log(f"✅ Truncated {map_path} → {entry['path']}")
    except subprocess.CalledProcessError:
        log(f"❌ Failed to truncate {map_path}")


# ---------------- Main logic ----------------


def run_fd_cleanup(regex, dry_run):
    files = get_deleted_fd_files()
    filtered = [f for f in files if re.search(regex, f["path"])]
    if not filtered:
        log("No matching deleted files held by FDs.")
        return

    total = sum(f["size"] for f in filtered)
    inode_map = group_by_inode(filtered)
    log(
        f"FD mode: {len(filtered)} files across {len(inode_map)} inodes → {total / (1024**2):.2f} MB"
    )

    for i, (inode, group) in enumerate(inode_map.items(), 1):
        size = sum(f["size"] for f in group)
        paths = sorted(set(f["path"] for f in group))
        log(f"{i}. Inode {inode} → {size / (1024**2):.2f} MB across {len(group)} FDs")
        for p in paths:
            print(f"   📄 {p}")

    confirm = input("Truncate FD-held files? (y/N): ").strip().lower()
    if confirm == "y":
        for inode, group in inode_map.items():
            truncate_inode_group(inode, group, dry_run=dry_run)
    else:
        log("Skipped FD truncation.")


def run_map_cleanup(regex, dry_run):
    mapped_files = get_mapped_deleted_files(regex)
    if not mapped_files:
        log("No matching memory-mapped deleted files.")
        return

    log(f"Map mode: {len(mapped_files)} memory-mapped deleted files")
    for entry in mapped_files:
        print(f"   🧠 {entry['path']} (PID {entry['pid']})")

    confirm = input("Truncate memory-mapped files? (y/N): ").strip().lower()
    if confirm == "y":
        for entry in mapped_files:
            truncate_mapped_file(entry, dry_run=dry_run)
    else:
        log("Skipped memory-mapped truncation.")


def main():
    parser = argparse.ArgumentParser(
        description="Inspect and truncate deleted-but-open files in /tmp"
    )
    parser.add_argument(
        "--mode",
        choices=["fds", "maps", "all"],
        default="all",
        help="Which cleanup mode to run",
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

    log(f"Starting tmp_inspector in mode: {args.mode}")
    if args.mode in ["fds", "all"]:
        run_fd_cleanup(args.regex, args.dry_run)
    if args.mode in ["maps", "all"]:
        run_map_cleanup(args.regex, args.dry_run)


if __name__ == "__main__":
    main()
