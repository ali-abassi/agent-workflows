from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "piw.py"


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args, "--json"],
        cwd=cwd, capture_output=True, text=True, timeout=60, check=False,
    )


class CoreContractTests(unittest.TestCase):
    def test_inspect_without_runs_has_a_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            workflow = Path(raw) / "steps.yaml"
            workflow.write_text(yaml.safe_dump({
                "version": 1, "workflow": "empty",
                "steps": [{"id": "one", "cmd": "true"}],
            }), encoding="utf-8")
            inspected = run("inspect", str(workflow))
            self.assertNotEqual(inspected.returncode, 0)
            self.assertIn("no runs found", inspected.stderr)

    def test_create_emits_a_strictly_valid_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "created"
            created = run("create", "created", "--dir", str(target))
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            checked = run("validate", str(target / "steps.yaml"), "--strict")
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)

    def test_shell_workflow_validates_runs_and_is_inspectable(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            workflow = root / "steps.yaml"
            workflow.write_text(yaml.safe_dump({
                "version": 1,
                "workflow": "journey",
                "input": {"required": True, "description": "one value"},
                "steps": [
                    {"id": "copy", "cmd": 'cat "$INPUT"',
                     "gate": 'cmp "$INPUT" "$OUT"'},
                    {"id": "verify", "needs": ["copy"],
                     "cmd": 'cp "$RUN/copy.md" "$OUT"',
                     "gate": 'cmp "$RUN/copy.md" "$OUT"'},
                ],
            }, sort_keys=False), encoding="utf-8")
            checked = run("validate", str(workflow), "--strict")
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            executed = run("run", str(workflow), "--input", "durable", "--strict")
            self.assertEqual(executed.returncode, 0, executed.stdout + executed.stderr)
            receipt = json.loads(executed.stdout)
            self.assertEqual(receipt["status"], "completed")
            self.assertEqual(receipt["steps"], {"copy": "passed", "verify": "passed"})
            inspected = run("inspect", str(workflow), receipt["run"])
            self.assertEqual(inspected.returncode, 0, inspected.stdout + inspected.stderr)
            evidence = json.loads(inspected.stdout)
            self.assertIn("trace.jsonl", os.listdir(evidence["run_dir"]))
            self.assertEqual(len(evidence["ledger"]), 2)

    def test_strict_validation_rejects_an_existence_only_gate(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            workflow = Path(raw) / "steps.yaml"
            workflow.write_text(yaml.safe_dump({
                "version": 1, "workflow": "weak",
                "steps": [{"id": "draft", "prompt": "Draft", "gate": 'test -s "$OUT"'}],
            }, sort_keys=False), encoding="utf-8")
            normal = run("validate", str(workflow))
            strict = run("validate", str(workflow), "--strict")
            self.assertEqual(normal.returncode, 0)
            self.assertEqual(strict.returncode, 1)
            self.assertIn("only that output exists", strict.stdout)

    def test_configure_preserves_comments_and_revalidates(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            workflow = Path(raw) / "steps.yaml"
            workflow.write_text(
                "version: 1\nworkflow: configured\nsteps:\n"
                "  # retained comment\n"
                "  - id: draft\n    prompt: Draft\n    gate: grep -q . \"$OUT\"\n",
                encoding="utf-8",
            )
            changed = run("configure", str(workflow), "draft", "--thinking", "high")
            self.assertEqual(changed.returncode, 0, changed.stdout + changed.stderr)
            self.assertIn("# retained comment", workflow.read_text(encoding="utf-8"))
            self.assertEqual(yaml.safe_load(workflow.read_text())["steps"][0]["thinking"], "high")


if __name__ == "__main__":
    unittest.main()
