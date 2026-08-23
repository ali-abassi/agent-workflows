"""Fail CI when the built wheel omits the executable kernel."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

wheel = Path(sys.argv[1])
names = set(zipfile.ZipFile(wheel).namelist())
required_suffixes = {
    "agent_workflows/cli.py",
    "agent_workflows/run_steps.py",
    "agent_workflows/run_bundle.py",
    "agent_workflows/graph.py",
    "agent_workflows/schemas/workflow.schema.json",
    ".dist-info/entry_points.txt",
}
missing = sorted(suffix for suffix in required_suffixes
                 if not any(name.endswith(suffix) for name in names))
if missing:
    raise SystemExit(f"wheel is missing runtime files: {missing}")
print(f"wheel contains the executable kernel ({len(names)} files)")
