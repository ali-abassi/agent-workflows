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
    def test_every_command_has_help_without_traceback(self) -> None:
        commands = ["create", "validate", "graph", "run", "resume", "inspect",
                    "configure", "doctor"]
        for command in commands:
            with self.subTest(command=command):
                result = subprocess.run([sys.executable, str(CLI), command, "--help"],
                                        capture_output=True, text=True, check=False)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("usage:", result.stdout)
                self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_expected_failure_is_one_json_document(self) -> None:
        missing = run("validate", "/definitely/not/a/workflow.yaml")
        self.assertEqual(missing.returncode, 2)
        payload = json.loads(missing.stdout)
        self.assertFalse(payload["ok"])
        self.assertIn("workflow not found", payload["error"])
        self.assertEqual(missing.stderr, "")

    def test_all_published_examples_validate_strictly(self) -> None:
        examples = sorted((ROOT / "examples").glob("*.steps.yaml"))
        self.assertGreaterEqual(len(examples), 4)
        for example in examples:
            with self.subTest(example=example.name):
                checked = run("validate", str(example), "--strict")
                self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)

    def test_branching_example_records_run_and_skip_paths(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            workflow = Path(raw) / "steps.yaml"
            workflow.write_text((ROOT / "examples" / "branching.steps.yaml").read_text())
            urgent = run("run", str(workflow), "--input", "! outage", "--strict")
            self.assertEqual(urgent.returncode, 0, urgent.stdout + urgent.stderr)
            self.assertEqual(json.loads(urgent.stdout)["steps"]["escalate"], "passed")
            normal = run("run", str(workflow), "--input", "docs", "--strict")
            self.assertEqual(normal.returncode, 0, normal.stdout + normal.stderr)
            self.assertEqual(json.loads(normal.stdout)["steps"]["escalate"], "skipped")

    def test_recovery_example_resumes_after_human_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            workflow = root / "steps.yaml"
            workflow.write_text((ROOT / "examples" / "recovery.steps.yaml").read_text())
            first = run("run", str(workflow), "--input", "release", "--strict")
            self.assertNotEqual(first.returncode, 0)
            receipt = json.loads(first.stdout)
            self.assertEqual(receipt["steps"]["checkpoint"], "failed")
            approvals = root / "approvals"
            approvals.mkdir()
            (approvals / "continue.ok").write_text("approved\n")
            resumed = run("resume", str(workflow), receipt["run"])
            self.assertEqual(resumed.returncode, 0, resumed.stdout + resumed.stderr)
            self.assertEqual(json.loads(resumed.stdout)["status"], "completed")

    def test_version_and_doctor_are_machine_readable(self) -> None:
        version = subprocess.run([sys.executable, str(CLI), "--version"],
                                 capture_output=True, text=True, check=False)
        self.assertEqual(version.returncode, 0, version.stderr)
        self.assertRegex(version.stdout.strip(), r"^piw \d+\.\d+\.\d+$")
        doctor = run("doctor")
        self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)
        payload = json.loads(doctor.stdout)
        self.assertTrue(payload["ok"])
        self.assertIn(payload["mode"], {"shell-ready", "agent-ready"})

    def test_malformed_yaml_is_concise_and_has_no_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            workflow = Path(raw) / "steps.yaml"
            workflow.write_text("version: [\n", encoding="utf-8")
            result = run("validate", str(workflow))
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertIn("invalid YAML", payload["error"])
            self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_inspect_without_runs_has_a_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            workflow = Path(raw) / "steps.yaml"
            workflow.write_text(yaml.safe_dump({
                "version": 1, "workflow": "empty",
                "steps": [{"id": "one", "cmd": "true"}],
            }), encoding="utf-8")
            inspected = run("inspect", str(workflow))
            self.assertNotEqual(inspected.returncode, 0)
            self.assertIn("no runs found", json.loads(inspected.stdout)["error"])

    def test_create_emits_a_strictly_valid_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "created"
            created = run("create", "created", "--dir", str(target))
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            checked = run("validate", str(target / "steps.yaml"), "--strict")
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            spec = yaml.safe_load((target / "steps.yaml").read_text())
            self.assertNotIn("model", spec)
            executed = run("run", str(target), "--input", "hello", "--strict")
            self.assertEqual(executed.returncode, 0, executed.stdout + executed.stderr)

    def test_create_agent_template_is_explicit_and_valid(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "agent"
            created = run("create", "agent", "--dir", str(target),
                          "--template", "agent", "--model", "provider/model")
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            spec = yaml.safe_load((target / "steps.yaml").read_text())
            self.assertEqual(spec["model"], "provider/model")
            checked = run("validate", str(target), "--strict")
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

    def test_human_run_path_is_ascii_and_append_only(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            workflow = Path(raw) / "steps.yaml"
            workflow.write_text((ROOT / "examples" / "hello.steps.yaml").read_text())
            environment = {**os.environ, "TERM": "dumb", "NO_COLOR": "1", "COLUMNS": "40"}
            executed = subprocess.run(
                [sys.executable, str(CLI), "run", str(workflow),
                 "--input", "Ada", "--strict"],
                capture_output=True, text=True, timeout=60, check=False, env=environment,
            )
            self.assertEqual(executed.returncode, 0, executed.stdout + executed.stderr)
            executed.stdout.encode("ascii")
            executed.stderr.encode("ascii")
            self.assertNotIn("\x1b", executed.stdout + executed.stderr)
            self.assertIn("run complete |", executed.stdout)

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
