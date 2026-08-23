# Usage

Agent Workflows runs inspectable YAML workflows. Models may generate content
inside nodes; deterministic code owns dependencies, conditions, gates, retries,
durable state, and evidence.

Every command supports `--help`. Commands that produce receipts accept
`--json` for one machine-readable JSON document.

## 1. Check the runtime

```bash
piw --version
piw doctor
piw doctor --json
```

`shell-ready` means command workflows can run. `agent-ready` additionally means
the optional Pi executable is available.

## 2. Create a workflow

The default template is deterministic and zero-cost:

```bash
piw create uppercase
piw validate uppercase --strict
piw run uppercase --input hello --strict --json
```

Create a model-backed template explicitly:

```bash
piw create review --template agent \
  --model openai-codex/gpt-5.6-luna
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
    gate: tr '[:lower:]' '[:upper:]' < "$INPUT" | cmp - "$OUT"
```

An `input:` block must declare both `required` and `description`—the
description is the contract a calling agent reads, so validation rejects an
input without one.

## 3. Validate and inspect the graph

```bash
piw validate review/steps.yaml --strict
piw graph review/steps.yaml
piw graph review/steps.yaml --json
```

Validation never runs a node. Strict validation rejects weak gates on
nondeterministic work, including gates that only check that output exists.

## 4. Configure one node

```bash
piw configure review/steps.yaml work \
  --model openai-codex/gpt-5.6-sol --thinking high
```

Configure changes only the requested node fields, preserves YAML comments, and
revalidates the workflow.

## 5. Run

```bash
piw run review/steps.yaml --input "Review this change" --strict --json
piw run review/steps.yaml --input-file request.md --strict --json
```

Each run lands in `runs/<workflow>-<YYYYMMDD-HHMMSS>/` beside `steps.yaml`.
The receipt's `run` field is that directory's name and is the `RUN_ID`
accepted by `inspect` and `resume`.

Dependency-ready nodes run **concurrently**—top-level `workers:` bounds the
pool (default 4, maximum 16). `needs:` is the only serialization guarantee:
nodes that must not overlap (for example commands mutating the same file) must
be ordered with explicit dependencies.

The input is copied into the run and fingerprinted. Each run freezes the
workflow and records:

- `workflow.yaml` and `input.txt`—immutable execution boundary;
- `manifest.json` and `state.json`—durable contract and current projection;
- `trace.jsonl`—contiguous committed events;
- `ledger.json`—model, time, token, and cost usage when reported;
- `<step>.md` and `<step>.stderr`—artifacts and diagnostics;
- `produced/`—files declared by `produces:`; and
- local Git history—diffable step transitions unless explicitly disabled.

## 6. Inspect evidence

```bash
piw inspect review/steps.yaml --json
piw inspect review/steps.yaml RUN_ID --json
```

Do not infer success from a model's last sentence. Check state, artifacts, gate
results, trace, and ledger.

## 7. Resume safely

```bash
piw resume review/steps.yaml RUN_ID --json
```

Resume verifies the frozen workflow and immutable input and continues from the
committed unfinished boundary. A changed source workflow fails closed:

```bash
piw resume review/steps.yaml RUN_ID --force-drift --json
```

Use `--force-drift` only after reviewing the exact change. The original frozen
workflow remains in the run bundle. Input drift cannot be forced.

See [the recovery example](../examples/README.md#recovery-stop-approve-resume)
for a file-backed human checkpoint.

## Dependencies and placeholders

`needs: [step-id]` declares dependencies explicitly. Without `needs`, a node
depends on the previous listed node. References also create dependencies:

- `{input}`—immutable run input;
- `{prev}`—previous listed step artifact;
- `{step.id}`—named prior artifact; and
- `{run}`—run directory.

Command nodes receive `$INPUT`, `$OUT`, `$RUN`, `$STEP`, and `$WORKFLOW_DIR`.

## Typed routing

Use JSON output plus `schema` and `when` for deterministic decisions:

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
    gate: python3 -m json.tool "$OUT" >/dev/null
```

Code evaluates `when`; the model cannot choose which node the runner dispatches.

## Retries and timeouts

```yaml
retries: 2
retry_on: [model_error, schema_failed, gate_failed]
retry_delay_seconds: 1
retry_backoff: exponential
retry_jitter: 0.2            # deterministic ±20% spread per step id + attempt
retry_max_delay_seconds: 60  # backoff cap (default 300)
timeout: 900
```

Retry only declared failure classes. Commands and their child process groups
are terminated when their timeout expires. Jitter is derived from the step id
and attempt number, so a replayed run computes the same delays.

## Judged improvement loops

A step may attach an LLM judge that scores each candidate and iterates until a
target score or the attempt budget is reached:

```yaml
  - id: draft
    prompt: Write the release announcement for {input}.
    gate: test -s "$OUT"
    judge:
      prompt: >-
        Score this draft 0-10 for clarity.
        Return JSON: {"score": N}. Candidate: {out}
      score: 8         # minimum passing score (default 8)
      max_iters: 3     # attempt budget (supersedes retries when larger)
      keep_best: false # true keeps the highest-scoring rejected candidate
```

The judge must return JSON containing a numeric `"score"`; each verdict is
stored as `<step>.judge<N>.md`. A judge never replaces the mechanical `gate`—
the gate still runs on every attempt—and a below-target score is an ordinary
retryable failure class (`judge_below_target`). Judge and schema settings are
part of the cache key, so tightening either invalidates cached artifacts.

## Final QA review

A top-level `qa:` block runs one independent model review over all artifacts
after every step has passed (and again during verification):

```yaml
qa:
  prompt: >-
    Review these artifacts for contradictions.
    Return JSON: {"verdict": "pass"} or {"verdict": "fail"}.
    {artifacts}
```

The report is written to `qa.md`; a `fail` verdict fails the run even though
every individual gate passed.

## Other schema keys

- `workers:` (top-level, default 4, maximum 16)—concurrent dependency-ready
  nodes; see [section 5](#5-run).
- `cwd:` (top-level, default `.`)—execution directory for command nodes,
  resolved relative to `steps.yaml`.
- `preview:` (step)—declarative image paths for visual tooling; never affects
  execution.

## Runtime choices

Use the weakest runtime that can complete the node:

1. `cmd:`—deterministic code, no model;
2. `prompt:`—one isolated completion;
3. `prompt:` plus `tools:`—explicit Pi tool allowlist; or
4. `prompt:` plus `agent: true`—full Pi tool loop.

`tools:` controls what Pi exposes to a model. It does not sandbox the shell,
filesystem, process, network, or inherited environment.

The complete authoring contract is
[`src/agent_workflows/schemas/workflow.schema.json`](../src/agent_workflows/schemas/workflow.schema.json).
Runnable examples are indexed in [`examples/README.md`](../examples/README.md).
