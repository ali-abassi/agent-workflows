# Agent Workflows

[![CI](https://github.com/ali-abassi/agent-workflows/actions/workflows/ci.yml/badge.svg)](https://github.com/ali-abassi/agent-workflows/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Make agent workflows fail visibly, recover safely, and leave proof.**

Agent Workflows is a small local workflow kernel for work that may involve
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

## In plain words

- **What it does.** You write your steps in one small text file
  (`steps.yaml`)—a numbered checklist. `piw` runs the steps in the right
  order, tests each step's output before moving on, retries what failed, and
  stops where a human must decide. If it stops, `piw resume` picks up exactly
  where it left off.
- **Why that matters for AI work.** Agents sometimes skip steps or declare
  unfinished work done. Here a model may *write* a step's content, but plain
  code decides what runs next, and a real test (the `gate`) decides pass or
  fail—a model cannot talk its way past it.
- **What you get afterwards.** Every run is an ordinary folder holding the
  exact input, every step's output, what each step cost, and a full timeline.
  No server, no database, no dashboard.

## Which command, when

| You want to | Run |
|---|---|
| Start a new workflow file | `piw create NAME` |
| Check the file is valid (free, nothing executes) | `piw validate NAME --strict` |
| See the step order before running | `piw graph NAME` |
| Execute the workflow | `piw run NAME --input "..." --strict --json` |
| See what a run did, produced, and cost | `piw inspect NAME --json` |
| Continue a stopped or failed run | `piw resume NAME RUN_ID --json` |
| Check your machine is ready | `piw doctor` |

## Try it in two minutes

Install `piw` (the **p**i **w**orkflow command) from the v0.2.0 release:

```bash
python3 -m pip install \
  "git+https://github.com/ali-abassi/agent-workflows.git@v0.2.0"
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
Every run lands in `runs/<workflow>-<timestamp>/` next to `steps.yaml` — an
ordinary directory, readable without a database:

```text
$ ls hello/runs/hello-20260823-232621/
input.txt     log.md         normalize.md    result.md  state.json   workflow.yaml
ledger.json   manifest.json  run-owner.json  run.lock   trace.jsonl  .git/
```

It holds the frozen workflow and input, the state projection, an append-only
trace, per-step artifacts, diffable Git history, and a ledger that records what
each node actually cost:

```json
{"id": "analyze", "model": "openai-codex/gpt-5.6-luna", "attempts": 1,
 "passed": true, "seconds": 8.3, "input": 5288, "output": 168, "cost": 0.0012592}
```

Prefer an isolated CLI install? Use
[`pipx`](https://pipx.pypa.io/stable/installation/):

```bash
pipx install "git+https://github.com/ali-abassi/agent-workflows.git@v0.2.0"
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
- Concurrent dispatch of dependency-ready nodes (`workers:`, default 4);
  `needs:` is the serialization guarantee.
- Immutable per-run input and frozen workflow fingerprints.
- Atomic state, contiguous JSONL trace, one-writer locking, and crash recovery.
- Content-addressed cache, per-step ledger, and inspectable Git history.
- `create`, `validate`, `graph`, `run`, `inspect`, `resume`, `configure`, and
  `doctor` commands with machine-readable JSON receipts.

See the [usage guide](docs/USAGE.md), [examples](examples/README.md), and the
published [workflow schema](src/agent_workflows/schemas/workflow.schema.json).

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

## Why not LangGraph, Temporal, or Make?

| If you need | Use |
|---|---|
| Org-wide orchestration with a server, database, and durable timers | Temporal, Prefect, Dagster |
| Graphs wired in Python around one agent framework | LangGraph |
| File-timestamp incremental builds | Make |
| A local, auditable run contract for agent work | **Agent Workflows** |

Core's bet is auditability over throughput: gates are shell commands, state is
a readable directory, resume is fingerprint-verified, and there is no server,
daemon, or database — a run is a directory you can `ls`, `diff`, and commit.

## Deliberate boundary

Core does **not** include Studio, batch processing, evaluations, optimization,
scheduling, action catalogs, hosted worker fleets, or the software-factory
product.
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

Agent Workflows is the reduced, public kernel of
[ali-abassi/pi-graph](https://github.com/ali-abassi/pi-graph). The projects
share the same control-flow philosophy: models do work; code decides whether
the work may advance.
