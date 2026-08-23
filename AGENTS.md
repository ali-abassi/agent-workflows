# Pi Graph Core

This repository is the minimal agent-facing distribution of Pi Graph. Keep the
public surface limited to create, validate, graph, run, resume, inspect, and
configure. Do not add Studio, batch, evaluation, optimization, scheduling,
action catalogs, or reporting here.

The workflow schema, parser, runner, and durable bundle writer are the kernel.
Changes to them must remain compatible with the full Pi Graph project and need
behavioral tests. Models do work inside nodes; code owns control flow, gates,
recovery, and evidence.

Verify with:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/*.py
./bin/piw validate examples/hello.steps.yaml --strict
./bin/piw run examples/hello.steps.yaml --input Ada --strict --json
```
