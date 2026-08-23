# Usage

Pi Graph Core runs inspectable YAML workflows. Models generate content inside
nodes; deterministic code owns dependencies, conditions, gates, retries,
durable state, and evidence.

## 1. Create a workflow

```bash
./bin/piw create review --dir ./review
```

Or write `steps.yaml` directly:

```yaml
version: 1
workflow: uppercase
input:
  required: true
  description: One string
steps:
  - id: transform
    cmd: tr '[:lower:]' '[:upper:]' < "$INPUT"
    gate: grep -q '[A-Z]' "$OUT"
```

## 2. Validate before running

```bash
./bin/piw validate review/steps.yaml --strict
./bin/piw graph review/steps.yaml
```

Strict validation rejects weak existence-only gates on nondeterministic nodes.

## 3. Configure an agent node

```bash
./bin/piw configure review/steps.yaml work \
  --model openai-codex/gpt-5.6-sol --thinking high
```

Workflow nodes may declare an isolated completion, an explicit tool allowlist,
or `agent: true`. Tool selection is not an operating-system sandbox.

## 4. Run

```bash
./bin/piw run review/steps.yaml --input "Review this change" --strict --json
./bin/piw run review/steps.yaml --input-file request.md --strict --json
```

Each run freezes the workflow and input. Artifacts, state, trace, ledger, and
per-step Git history live under the workflow's `runs/` directory.

## 5. Inspect evidence

```bash
./bin/piw inspect review/steps.yaml --json
./bin/piw inspect review/steps.yaml RUN_ID --json
```

Do not infer success from the final model sentence. Inspect the step artifact,
gate result, trace, and ledger.

## 6. Resume an interrupted run

```bash
./bin/piw resume review/steps.yaml RUN_ID
```

Resume verifies the frozen workflow and input and continues from the committed
unfinished boundary. If the source workflow changed, it fails closed. Use
`--force-drift` only after reviewing the change; the original snapshot remains
in the run bundle.

## Conditions and repairs

Use typed JSON output and `when` for deterministic routing:

```yaml
  - id: decide
    prompt: Return JSON with verdict pass or repair.
    schema:
      verdict:
        type: string
        enum: [pass, repair]
    gate: python3 -m json.tool "$OUT" >/dev/null
  - id: repair
    needs: [decide]
    from: decide
    when:
      op: equals
      path: /verdict
      value: repair
    prompt: Repair the reported issue from {step.decide}.
    gate: test -s "$OUT"
```

See [`schemas/workflow.schema.json`](../schemas/workflow.schema.json) for the
complete contract and [`examples/hello.steps.yaml`](../examples/hello.steps.yaml)
for a zero-cost executable example.
