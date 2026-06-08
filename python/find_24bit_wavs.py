#!/usr/bin/env python3
"""Find 24-bit WAV files under a directory.

By default this scans the current directory recursively and prints matching
paths, one per line.
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path


class WavParseError(Exception):
    pass


def read_exact(handle, size: int) -> bytes:
    data = handle.read(size)
    if len(data) != size:
        raise WavParseError("unexpected end of file")
    return data


def wav_bits(path: Path) -> tuple[int, int | None]:
    """Return (bits_per_sample, valid_bits_per_sample) for a WAV file."""
    with path.open("rb") as handle:
        header = read_exact(handle, 12)
        riff_id, _riff_size, wave_id = struct.unpack("<4sI4s", header)
        if riff_id not in (b"RIFF", b"RF64") or wave_id != b"WAVE":
            raise WavParseError("not a RIFF/RF64 WAVE file")

        while True:
            chunk_header = handle.read(8)
            if not chunk_header:
                raise WavParseError("missing fmt chunk")
            if len(chunk_header) != 8:
                raise WavParseError("truncated chunk header")

            chunk_id, chunk_size = struct.unpack("<4sI", chunk_header)
            chunk_data_start = handle.tell()

            if chunk_id == b"fmt ":
                fmt = read_exact(handle, chunk_size)
                if len(fmt) < 16:
                    raise WavParseError("fmt chunk is too short")

                audio_format, _channels, _sample_rate, _byte_rate, _block_align, bits = (
                    struct.unpack("<HHIIHH", fmt[:16])
                )

                valid_bits = None
                # WAVE_FORMAT_EXTENSIBLE stores valid bits at offset 18.
                if audio_format == 0xFFFE and len(fmt) >= 20:
                    valid_bits = struct.unpack("<H", fmt[18:20])[0]

                return bits, valid_bits

            handle.seek(chunk_data_start + chunk_size + (chunk_size % 2))


def is_24_bit_wav(path: Path) -> bool:
    bits, valid_bits = wav_bits(path)
    return bits == 24 or valid_bits == 24


def iter_wavs(root: Path):
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() == ".wav":
            yield path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find WAV files that use 24-bit sample depth."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        type=Path,
        help="directory to scan, defaults to the current directory",
    )
    parser.add_argument(
        "--absolute",
        action="store_true",
        help="print absolute paths instead of paths relative to the scan root",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="also show files that could not be parsed",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.exists():
        print(f"error: path does not exist: {root}", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"error: path is not a directory: {root}", file=sys.stderr)
        return 2

    matches = 0
    scanned = 0
    errors = 0

    for path in iter_wavs(root):
        scanned += 1
        try:
            if not is_24_bit_wav(path):
                continue
        except (OSError, WavParseError, struct.error) as exc:
            errors += 1
            if args.verbose:
                print(f"warning: skipped {path}: {exc}", file=sys.stderr)
            continue

        matches += 1
        print(path.resolve() if args.absolute else path.relative_to(root))

    print(
        f"\nScanned {scanned} WAV file(s); found {matches} 24-bit file(s).",
        file=sys.stderr,
    )
    if errors:
        print(f"Skipped {errors} unreadable or invalid WAV file(s).", file=sys.stderr)

    return 1 if matches else 0


if __name__ == "__main__":
    raise SystemExit(main())
