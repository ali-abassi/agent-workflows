# Pi Graph Core

[![CI](https://github.com/ali-abassi/pi-graph-core/actions/workflows/ci.yml/badge.svg)](https://github.com/ali-abassi/pi-graph-core/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Make agent workflows fail visibly, recover safely, and leave proof.**

Pi Graph Core is a small local workflow kernel for work that may involve
nondeterministic models but still needs deterministic control. Models can work
inside nodes; code owns dependency order, routing, gates, retries, immutable
inputs, durable recovery, and run evidence.

```text
validated YAML → deterministic DAG → node output → code-owned gate
                                      ↓ fail          ↓ pass
                                 bounded retry    next eligible node
                                                       ↓
                                    state + trace + ledger + artifacts
```

Core is deliberately not another all-in-one agent platform. It is the portable
execution contract underneath one.

## Try it in two minutes

Install the `piw` command from the v0.1.0 release:

```bash
python3 -m pip install \
  "git+https://github.com/ali-abassi/pi-graph-core.git@v0.1.0"
piw doctor
```

Create and run a zero-cost workflow—no model or API key required:

```bash
piw create hello
piw validate hello --strict
piw graph hello
piw run hello --input Ada --strict --json
piw inspect hello --json
```

The run receipt includes a durable run id and every step's terminal status.
The run directory contains the frozen workflow and input, state projection,
append-only trace, ledger, artifacts, logs, and per-step Git history.

Prefer an isolated CLI install? Use
[`pipx`](https://pipx.pypa.io/stable/installation/):

```bash
pipx install "git+https://github.com/ali-abassi/pi-graph-core.git@v0.1.0"
```

For a source checkout, editable development setup, or troubleshooting, follow
the [setup guide](docs/SETUP.md).

## What it gives you

- A validated YAML DAG with explicit and inferred dependencies.
- Four node runtimes: shell command, isolated completion, allowlisted tools,
  and full agent loop.
- Typed JSON output contracts and code-owned conditional routing.
- Mechanical gates that check artifacts or side effects—not model confidence.
- Classified, bounded retries with fixed or exponential delay.
- Immutable per-run input and frozen workflow fingerprints.
- Atomic state, contiguous JSONL trace, one-writer locking, and crash recovery.
- Content-addressed cache, per-step ledger, and inspectable Git history.
- `create`, `validate`, `graph`, `run`, `inspect`, `resume`, `configure`, and
  `doctor` commands with machine-readable JSON receipts.

See the [usage guide](docs/USAGE.md), [examples](examples/README.md), and the
published [workflow schema](src/pi_graph_core/schemas/workflow.schema.json).

## Add model and agent nodes

Shell workflows work immediately. Model, tool, and agent nodes use
[Pi](https://github.com/earendil-works/pi):

```bash
npm install -g @earendil-works/pi-coding-agent
pi  # authenticate once

piw create review --template agent \
  --model openai-codex/gpt-5.6-luna
piw run review --input-file request.md --strict --json
```

Each model call is isolated and pins its model and thinking level. Agent nodes
can receive explicit tools, but tool selection is routing—not operating-system
sandboxing.

## Minimal workflow

```yaml
version: 1
workflow: uppercase
input:
  required: true
  description: One immutable string
steps:
  - id: transform
    cmd: tr '[:lower:]' '[:upper:]' < "$INPUT"
    gate: tr '[:lower:]' '[:upper:]' < "$INPUT" | cmp - "$OUT"
  - id: report
    needs: [transform]
    cmd: printf 'Result: %s\n' "$(cat "$RUN/transform.md")"
    gate: grep -q '^Result: ' "$OUT"
```

`piw validate steps.yaml --strict` checks the contract without running a model
or command. `piw graph steps.yaml` prints the exact dependency structure the
runner will use.

## Evidence, not vibes

The test suite exercises atomic-write failures, bootstrap recovery, one-writer
locking, concurrent transitions, torn traces, workflow drift, immutable input,
branch skips, SIGKILL recovery, and surgical resume. CI runs on Linux and macOS
with Python 3.10 and 3.14, builds the wheel, installs it into a clean
environment, and executes the installed command.

That evidence supports the kernel behavior tested here. It is not a claim that
arbitrary workflows are safe or that model output is deterministic.

## Deliberate boundary

Core does **not** include Studio, batch processing, evaluations, optimization,
scheduling, action catalogs, hosted workers, or the software-factory product.
Those live in the full [Pi Graph](https://github.com/ali-abassi/pi-graph)
platform.

Core currently supports macOS and Linux with Python 3.10+. It is alpha software
and executes workflow commands with the invoking user's permissions. Review
third-party workflows and use a container or isolated account when filesystem,
process, network, or credential isolation matters.

Read [SECURITY.md](SECURITY.md) before running untrusted workflows. Never place
credentials in workflow files, prompts, command arguments, or committed run
artifacts.

## Project

- [Setup](docs/SETUP.md)
- [Usage](docs/USAGE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Examples](examples/README.md)
- [Changelog](CHANGELOG.md)
- [Security policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [MIT license](LICENSE)

Pi Graph Core is the reduced, public kernel of
[ali-abassi/pi-graph](https://github.com/ali-abassi/pi-graph). The projects
share the same control-flow philosophy: models do work; code decides whether
the work may advance.
