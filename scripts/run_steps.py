#!/usr/bin/env python3
"""Source-checkout compatibility wrapper for the packaged runner."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pi_graph_core.run_steps import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
