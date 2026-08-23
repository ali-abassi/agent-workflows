# Agent Workflows

This repository is the minimal agent-facing distribution of Pi Graph. Keep the
public surface limited to create, validate, graph, run, resume, inspect, and
configure. Do not add Studio, batch, evaluation, optimization, scheduling,
action catalogs, or reporting here.

The workflow schema, parser, runner, and durable bundle writer under
`src/agent_workflows/` are the kernel.
Changes to them must remain compatible with the full Pi Graph project and need
behavioral tests. Models do work inside nodes; code owns control flow, gates,
recovery, and evidence.

Verify with:

```bash
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/ruff check src scripts tests
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q src scripts
./bin/piw doctor
./bin/piw validate examples/hello.steps.yaml --strict
./bin/piw run examples/hello.steps.yaml --input Ada --strict --json
```
