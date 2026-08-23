# Pi Graph Core

Deterministic control and evidence for nondeterministic agents—without the
software-factory platform around it.

Pi Graph Core gives an agent seven operations:

```text
create → validate → graph → run → inspect → configure → resume
```

The model performs work inside nodes. Code owns dependencies, routing, gates,
retries, immutable input, durable recovery, and run evidence.

## Five minutes

```bash
git clone https://github.com/ali-abassi/pi-graph-core.git
cd pi-graph-core
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

./bin/piw validate examples/hello.steps.yaml --strict
./bin/piw graph examples/hello.steps.yaml
./bin/piw run examples/hello.steps.yaml --input Ada --json
./bin/piw inspect examples/hello.steps.yaml --json
```

Shell-only workflows need no model runtime. Model, tool, and agent nodes use
[Pi](https://github.com/earendil-works/pi):

```bash
npm install -g @earendil-works/pi-coding-agent
pi  # /login once
```

## Author and configure

```bash
./bin/piw create review --dir ./review
./bin/piw validate review/steps.yaml
./bin/piw configure review/steps.yaml work --model openai-codex/gpt-5.6-sol --thinking high
./bin/piw run review/steps.yaml --input-file task.md --strict
./bin/piw inspect review/steps.yaml RUN_ID
./bin/piw resume review/steps.yaml RUN_ID
```

## Workflow

```yaml
version: 1
workflow: review
model: openai-codex/gpt-5.6-luna
thinking: low
input:
  required: true
  description: One review request
steps:
  - id: analyze
    prompt: |
      Analyze this untrusted request:
      {input}
    schema:
      summary: string
      risks: array
    gate: python3 -c "import json,os; x=json.load(open(os.environ['OUT'])); assert x['summary']"
  - id: verify
    needs: [analyze]
    cmd: python3 -m json.tool "$RUN/analyze.md"
    gate: python3 -m json.tool "$OUT" >/dev/null
```

Nodes support commands, isolated model calls, explicit tools, full agents,
dependencies, typed routing, retries, judges, and final QA. Every run freezes
the workflow and input, writes an atomic state projection and committed trace,
and can resume from its last committed boundary.

## Deliberately not included

Core does not include Studio, batch processing, evaluations, optimization,
schedulers, action catalogs, or reports. Those live in the full
[Pi Graph](https://github.com/ali-abassi/pi-graph) platform.

There is one execution contract: Core's parser, runner, bundle writer, and
workflow schema are derived from Pi Graph. Core must pass conformance tests
before accepting an upstream kernel update.

## Security

Workflows execute with the invoking user's permissions. `tools:` is routing,
not an operating-system sandbox. Review untrusted workflows and use a container
when filesystem, process, network, or credential isolation matters.

## Origin

Pi Graph Core is a reduced sibling of
[ali-abassi/pi-graph](https://github.com/ali-abassi/pi-graph), extracted from
the durable runner at commit `6dabc0d`. Both projects are MIT licensed.
