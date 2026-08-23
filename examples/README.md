# Examples

All examples are ordinary `steps.yaml` files. Read them before running them;
command nodes execute with your user permissions. Runs are written to
`examples/runs/`, which is gitignored—the demos never dirty the clone.

## Hello: zero-cost linear workflow

```bash
piw run examples/hello.steps.yaml --input Ada --strict --json
```

## Branching: typed routing in code

```bash
piw graph examples/branching.steps.yaml
piw run examples/branching.steps.yaml --input '! investigate outage' --strict --json
piw run examples/branching.steps.yaml --input 'write documentation' --strict --json
```

The urgent input runs `escalate`; the normal input records it as skipped.

## Recovery: stop, approve, resume

The first run intentionally fails at a file-backed human checkpoint:

```bash
piw run examples/recovery.steps.yaml --input release --strict --json
mkdir -p examples/approvals
touch examples/approvals/continue.ok
piw resume examples/recovery.steps.yaml RUN_ID --json
```

Replace `RUN_ID` with the run id from the first receipt. Remove the approval
file before repeating the demonstration. Both `examples/runs/` and
`examples/approvals/*.ok` are gitignored, so the checkpoint demo leaves no
tracked changes behind.

## Any agent: Claude Code and Codex as gated nodes

Requires the `claude` and `codex` CLIs authenticated on PATH; both nodes may
incur provider cost:

```bash
piw run examples/any-agent.steps.yaml --input 'deterministic workflows' --strict --json
```

Each agent writes one sentence; deterministic gates check both outputs, and a
final command node combines them. Swap in any non-interactive agent CLI the
same way.

## Agent review: isolated model node

This example requires Pi authentication and may incur provider cost:

```bash
piw run examples/agent-review.steps.yaml \
  --input 'Review whether this migration has a rollback plan.' --strict --json
```
