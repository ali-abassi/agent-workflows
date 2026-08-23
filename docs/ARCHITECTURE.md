# Architecture

Agent Workflows separates nondeterministic work from deterministic control.

```text
steps.yaml
    │ validate + parse
    ▼
dependency graph ──► runner ──► command or isolated Pi call
                        │                    │
                        │                    ▼
                        │              candidate artifact
                        │                    │
                        └──── code gate ◄────┘
                                 │
                         state + trace + ledger
```

## Components

### `agent_workflows.cli`

The public `piw` command. It resolves workflows and runs, validates before
dispatch, emits human-readable or JSON receipts, and delegates execution to the
runner in the same Python environment.

### `agent_workflows.graph`

Parses node dependencies and typed conditions into an inspectable DAG. Its
dependency rules mirror the runner: explicit `needs`, artifact references,
`from`, `{prev}`, and the implicit previous-step rule.

### `agent_workflows.run_steps`

Owns execution. It selects eligible nodes and dispatches dependency-ready
nodes concurrently on a bounded pool (top-level `workers:`, default 4),
invokes the weakest configured runtime, validates schemas, runs gates,
classifies failure, applies bounded retry policy, evaluates conditions, and
records artifacts and ledger entries. Declared dependencies are the only
serialization guarantee between nodes.

### `agent_workflows.run_bundle`

Owns the durable boundary. It is the sole writer of manifest, state, trace, and
lock metadata.

## Run-bundle invariants

- One process holds the advisory writer lock.
- The exact workflow and input are fingerprinted and frozen.
- Input drift is never forceable.
- Trace sequence numbers are contiguous.
- State is the committed trace boundary.
- An uncommitted or torn trace tail may be truncated during recovery.
- Corruption before the committed boundary fails closed.
- State and manifest replacements are atomic.
- Resume dispatches only unfinished work and invalidated descendants.

Compatibility projections such as `ledger.json`, `log.md`, and `<step>.md`
remain easy to read without a database.

## Determinism boundary

For the same validated prior artifacts, code decides dependencies, branch
eligibility, gate success, retry limits, and terminal state. Live model calls
can still produce different content, latency, usage, and failures. Pin models,
use typed output, require mechanical gates, and retain run evidence instead of
claiming identical LLM execution.

## Trust boundary

Core is not a sandbox. Command nodes and agent tools inherit the invoking
user's operating-system permissions and environment. The Pi tool allowlist
limits model routing but does not isolate the filesystem, child processes,
network, or credentials. Put untrusted workflows inside a container or another
restricted execution environment.
