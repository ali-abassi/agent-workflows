# Examples

All examples are ordinary `steps.yaml` files. Read them before running them;
command nodes execute with your user permissions.

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
file before repeating the demonstration.

## Agent review: isolated model node

This example requires Pi authentication and may incur provider cost:

```bash
piw run examples/agent-review.steps.yaml \
  --input 'Review whether this migration has a rollback plan.' --strict --json
```
