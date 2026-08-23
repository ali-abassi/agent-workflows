# Contributing

Issues and focused pull requests are welcome. Pi Graph Core deliberately keeps
only the deterministic workflow kernel; Studio, batch execution, evaluation,
optimization, scheduling, and software-factory features belong in the full Pi
Graph repository.

Before submitting a change:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/ruff check src scripts tests
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q src scripts
./bin/piw doctor
./bin/piw validate examples/hello.steps.yaml --strict
./bin/piw run examples/hello.steps.yaml --input Ada --strict --json
```

Changes to the parser, runner, workflow schema, durable state, or trace contract
need behavioral tests. Keep gates deterministic and never rely on a model's
claim that a side effect or check succeeded.

`main` is protected. Open a focused pull request and let every Linux/macOS,
Python 3.10/3.14, wheel, and clean-install check pass before merging.
