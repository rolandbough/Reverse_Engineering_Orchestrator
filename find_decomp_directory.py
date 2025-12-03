#!/usr/bin/env python3
"""Helper script to find decompiled code directories"""

import sys
from pathlib import Path

def find_decomp_dirs(start_path: Path = Path("."), max_depth: int = 3) -> list[Path]:
    """Find directories that might contain decompiled code"""
    candidates = []
    
    # Common names for decompiled code directories
    names = ["decomp", "decompiled", "export", "exports", "c", "cpp", "src_decomp"]
    
    for depth in range(max_depth + 1):
        for name in names:
            pattern = "*/" * depth + name
            matches = list(start_path.glob(pattern))
            candidates.extend(matches)
    
    # Also check for directories with .c or .cpp files
    for path in start_path.rglob("*"):
        if path.is_dir() and depth <= max_depth:
            c_files = list(path.glob("*.c")) + list(path.glob("*.cpp"))
            if len(c_files) > 5:  # Has multiple C/C++ files
                candidates.append(path)
    
    return list(set(candidates))  # Remove duplicates

if __name__ == "__main__":
    print("Searching for decompiled code directories...")
    dirs = find_decomp_dirs()
    
    if dirs:
        print(f"\nFound {len(dirs)} potential directories:")
        for d in dirs:
            print(f"  - {d}")
    else:
        print("\nNo decompiled code directories found.")
        print("\nPlease specify the directory containing your decompiled code:")
        print("  python locate_addresses_from_decomp.py <decomp_dir>")

