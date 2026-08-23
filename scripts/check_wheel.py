"""Fail CI when the built wheel omits the executable kernel."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path


wheel = Path(sys.argv[1])
names = set(zipfile.ZipFile(wheel).namelist())
required_suffixes = {
    "data/scripts/piw.py",
    "data/scripts/run_steps.py",
    "data/scripts/run_bundle.py",
    "data/scripts/graph.py",
    "data/schemas/workflow.schema.json",
    "data/scripts/piw",
}
missing = sorted(suffix for suffix in required_suffixes
                 if not any(name.endswith(suffix) for name in names))
if missing:
    raise SystemExit(f"wheel is missing runtime files: {missing}")
print(f"wheel contains the executable kernel ({len(names)} files)")
