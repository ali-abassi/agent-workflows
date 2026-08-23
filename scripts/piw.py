#!/usr/bin/env python3
"""Small agent-facing CLI for the Pi Graph deterministic workflow kernel."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

import graph as workflow_graph


ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "scripts" / "run_steps.py"
SCHEMA = ROOT / "schemas" / "workflow.schema.json"


def emit(value: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, separators=(",", ":")))
    elif isinstance(value, str):
        print(value)
    else:
        print(json.dumps(value, indent=2))


def workflow_path(raw: str) -> Path:
    candidate = Path(raw).expanduser().resolve()
    if candidate.is_dir():
        candidate = candidate / "steps.yaml"
    if not candidate.is_file():
        raise SystemExit(f"workflow not found: {candidate}")
    return candidate


def load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise SystemExit("workflow root must be a mapping")
    return value


def validate(path: Path, strict: bool) -> dict[str, Any]:
    spec = load(path)
    contract = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(contract).iter_errors(spec),
        key=lambda error: [str(part) for part in error.absolute_path],
    )
    findings = [{
        "path": ".".join(str(part) for part in error.absolute_path) or "<root>",
        "message": error.message,
    } for error in errors]
    try:
        graph = workflow_graph.parse_steps(path)
    except workflow_graph.WorkflowParseError as error:
        findings.append({"path": "graph", "message": str(error)})
        graph = {"nodes": []}

    weak: list[dict[str, str]] = []
    for node in [item for item in graph.get("nodes", []) if not item.get("synthetic")]:
        gate = str(node.get("gate") or "").strip()
        compact = " ".join(gate.split()).rstrip(";")
        if node.get("kind") in {"completion", "tooled", "agent"} and not gate:
            weak.append({"step": node["id"], "message": "model-backed step has no gate"})
        elif compact in {":", "true", "exit 0", "/bin/true"}:
            weak.append({"step": node["id"], "message": "gate always succeeds"})
        elif compact in {'test -s "$OUT"', "test -s $OUT", "[ -s \"$OUT\" ]"}:
            weak.append({"step": node["id"], "message": "gate checks only that output exists"})
        elif node.get("kind") == "agent" and "$OUT" in gate and not any(
            marker in gate for marker in ("git ", "$RUN", "$INPUT", "./", "npm ", "pytest")
        ):
            weak.append({"step": node["id"], "message": "agent gate checks only its transcript"})
    return {
        "ok": not findings and (not strict or not weak),
        "workflow": spec.get("workflow", path.stem),
        "steps": len([node for node in graph.get("nodes", []) if not node.get("synthetic")]),
        "strict": strict,
        "errors": findings,
        "advice": weak,
    }


def unique_run_dir(path: Path, workflow: str) -> Path:
    base = path.parent / "runs" / f"{workflow}-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    candidate = base
    suffix = 2
    while candidate.exists():
        candidate = Path(f"{base}-{suffix}")
        suffix += 1
    return candidate


def run_summary(run_dir: Path, returncode: int) -> dict[str, Any]:
    state_path = run_dir / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.is_file() else {}
    steps = state.get("steps", {})
    return {
        "ok": returncode == 0,
        "run": run_dir.name,
        "run_dir": str(run_dir),
        "status": state.get("status", "unknown"),
        "steps": {key: value.get("status") for key, value in steps.items()},
    }


def execute_runner(path: Path, run_dir: Path, extra: list[str], as_json: bool) -> int:
    command = [sys.executable, str(RUNNER), str(path), "--run-dir", str(run_dir), *extra]
    result = subprocess.run(command, text=True, capture_output=as_json, check=False)
    if as_json:
        payload = run_summary(run_dir, result.returncode)
        if result.returncode and result.stderr:
            payload["error"] = result.stderr.strip()[-2000:]
        emit(payload, True)
    return result.returncode


def cmd_create(args: argparse.Namespace) -> int:
    directory = Path(args.dir or args.name).expanduser().resolve()
    path = directory / "steps.yaml"
    if path.exists():
        raise SystemExit(f"refusing to overwrite {path}")
    directory.mkdir(parents=True, exist_ok=True)
    spec = {
        "version": 1,
        "workflow": args.name,
        "model": args.model,
        "thinking": "low",
        "input": {"required": True, "description": "One immutable work item"},
        "steps": [
            {"id": "work",
             "prompt": "Complete this work item. Return JSON only: "
                       '{"result":"requested artifact","evidence":["observable support"]}'
                       "\n\n{input}",
             "schema": {"result": "string", "evidence": "array"},
             "gate": "python3 -c \"import json,os; x=json.load(open(os.environ['OUT'])); "
                     "assert x['result'].strip() and x['evidence']\"",
             "retries": 1},
            {"id": "verify", "needs": ["work"],
             "cmd": 'python3 -m json.tool "$RUN/work.md"',
             "gate": 'python3 -m json.tool "$OUT" >/dev/null'},
        ],
    }
    path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")
    emit({"ok": True, "path": str(path), "next": f"piw validate {path}"}, args.json)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    result = validate(workflow_path(args.workflow), args.strict)
    emit(result, args.json)
    return 0 if result["ok"] else 1


def cmd_graph(args: argparse.Namespace) -> int:
    graph = workflow_graph.parse_steps(workflow_path(args.workflow))
    if args.json:
        emit({"nodes": graph["nodes"], "edges": graph["edges"]}, True)
    else:
        for node in graph["nodes"]:
            if not node.get("synthetic"):
                deps = [edge["source"] for edge in graph["edges"] if edge["target"] == node["id"]]
                print(f"{node['id']} [{node['kind']}]" + (f" <- {', '.join(deps)}" if deps else ""))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    path = workflow_path(args.workflow)
    checked = validate(path, args.strict)
    if not checked["ok"]:
        emit(checked, args.json)
        return 1
    spec = load(path)
    run_dir = unique_run_dir(path, str(spec.get("workflow", path.stem)))
    extra = ["--no-cache"] if args.no_cache else []
    if args.input is not None:
        extra.extend(["--input", args.input])
    elif args.input_file:
        extra.extend(["--input-file", str(Path(args.input_file).expanduser().resolve())])
    return execute_runner(path, run_dir, extra, args.json)


def resolve_run(path: Path, raw: str) -> Path:
    direct = Path(raw).expanduser()
    if direct.is_dir():
        return direct.resolve()
    runs = path.parent / "runs"
    matches = [item for item in runs.iterdir() if item.is_dir() and raw in item.name] if runs.is_dir() else []
    if len(matches) != 1:
        raise SystemExit(f"run must match exactly one directory: {raw}")
    return matches[0].resolve()


def cmd_resume(args: argparse.Namespace) -> int:
    path = workflow_path(args.workflow)
    run_dir = resolve_run(path, args.run)
    extra = ["--resume"] + (["--force-drift"] if args.force_drift else [])
    return execute_runner(path, run_dir, extra, args.json)


def cmd_inspect(args: argparse.Namespace) -> int:
    path = workflow_path(args.workflow)
    run_dir = resolve_run(path, args.run) if args.run else sorted(
        [item for item in (path.parent / "runs").iterdir() if item.is_dir()],
        key=lambda item: item.stat().st_mtime,
    )[-1]
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    ledger = json.loads((run_dir / "ledger.json").read_text(encoding="utf-8"))
    artifacts = sorted(item.name for item in run_dir.glob("*.md"))
    payload = {"run": run_dir.name, "run_dir": str(run_dir), "state": state,
               "ledger": ledger, "artifacts": artifacts}
    emit(payload, args.json)
    return 0 if state.get("status") == "completed" else 1


def cmd_configure(args: argparse.Namespace) -> int:
    path = workflow_path(args.workflow)
    changes = {key: value for key, value in {
        "model": args.model, "thinking": args.thinking, "gate": args.gate,
        "tools": args.tools, "prompt": args.prompt,
    }.items() if value is not None}
    if not changes:
        raise SystemExit("configure requires at least one setting")
    result = workflow_graph.update_step(path, args.step, changes)
    checked = validate(path, False)
    emit({"ok": checked["ok"], **result, "validation": checked}, args.json)
    return 0 if checked["ok"] else 1


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="piw", description="Deterministic workflows for agents")
    root.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    commands = root.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create", help="create a small valid workflow")
    create.add_argument("name")
    create.add_argument("--dir")
    create.add_argument("--model", default="openai-codex/gpt-5.6-luna")
    validate_parser = commands.add_parser("validate", help="validate without spending")
    validate_parser.add_argument("workflow")
    validate_parser.add_argument("--strict", action="store_true")
    graph_parser = commands.add_parser("graph", help="show nodes and dependencies")
    graph_parser.add_argument("workflow")
    run = commands.add_parser("run", help="run a validated workflow")
    run.add_argument("workflow")
    inputs = run.add_mutually_exclusive_group()
    inputs.add_argument("--input")
    inputs.add_argument("--input-file")
    run.add_argument("--strict", action="store_true")
    run.add_argument("--no-cache", action="store_true")
    resume = commands.add_parser("resume", help="resume an interrupted durable run")
    resume.add_argument("workflow")
    resume.add_argument("run")
    resume.add_argument("--force-drift", action="store_true")
    inspect = commands.add_parser("inspect", help="inspect durable run evidence")
    inspect.add_argument("workflow")
    inspect.add_argument("run", nargs="?")
    configure = commands.add_parser("configure", help="change one node configuration")
    configure.add_argument("workflow")
    configure.add_argument("step")
    configure.add_argument("--model")
    configure.add_argument("--thinking", choices=["off", "minimal", "low", "medium", "high", "xhigh", "max"])
    configure.add_argument("--gate")
    configure.add_argument("--tools")
    configure.add_argument("--prompt")
    for command in commands.choices.values():
        command.add_argument("--json", action="store_true")
    return root


COMMANDS = {"create": cmd_create, "validate": cmd_validate, "graph": cmd_graph,
            "run": cmd_run, "resume": cmd_resume, "inspect": cmd_inspect,
            "configure": cmd_configure}


def main() -> int:
    args = parser().parse_args()
    return COMMANDS[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
