# Setup

## Requirements

- macOS or Linux
- Python 3.10 or newer
- Bash for command steps and gates
- Git for installation from GitHub and optional per-step history
- Pi only for model, tool, or agent nodes

Shell-only workflows require no API key or model provider.

## Install the released command

Use an isolated [`pipx`](https://pipx.pypa.io/stable/installation/) environment
when available:

```bash
pipx install "git+https://github.com/ali-abassi/agent-workflows.git@v0.2.0"
piw doctor
```

Or install into your current Python environment:

```bash
python3 -m pip install \
  "git+https://github.com/ali-abassi/agent-workflows.git@v0.2.0"
piw doctor
```

Uninstall with the same package manager:

```bash
pipx uninstall agent-workflows
# or: python3 -m pip uninstall agent-workflows
```

## Work from a source checkout

```bash
git clone https://github.com/ali-abassi/agent-workflows.git
cd agent-workflows
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[dev]"
./bin/piw doctor
./bin/piw validate examples/hello.steps.yaml --strict
./bin/piw run examples/hello.steps.yaml --input Ada --strict --json
```

`./bin/piw` automatically selects the checkout's `.venv`. Override it only when
you intentionally installed the package into another interpreter:

```bash
AGENT_WORKFLOWS_PYTHON=/path/to/python ./bin/piw doctor
```

If the wrapper reports that Core is not installed, run the editable-install
command shown above. It does not silently fall back to an unrelated system
installation.

## Enable model workflows

Install and authenticate Pi separately:

```bash
npm install -g @earendil-works/pi-coding-agent
pi
piw doctor
```

`piw doctor` reports `agent-ready` when Pi is available and `shell-ready` when
only the deterministic command runtime is available. A missing Pi installation
does not block shell workflows.

Agent Workflows does not read provider credentials directly. Pi owns provider
authentication. Do not put credentials in `steps.yaml`, prompts, command
arguments, committed run bundles, or repository files.

## Verify a source checkout

```bash
.venv/bin/ruff check src scripts tests
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q src scripts
./bin/piw doctor
for workflow in examples/*.steps.yaml; do
  ./bin/piw validate "$workflow" --strict
done
./bin/piw run examples/hello.steps.yaml --input Ada --strict --json
```

## Common problems

### `piw: command not found`

The environment's executable directory is not on `PATH`, or the package is not
installed there. Run `python3 -m pip show agent-workflows` with the same Python you
used during installation. `pipx ensurepath` configures the common pipx path.

### `pi` is optional or missing

Shell workflows still work. Install Pi only when the workflow contains prompt,
tool, or agent nodes.

### A workflow fails strict validation

Read both `errors` and `advice`. Strict mode rejects model-backed nodes with no
meaningful gate and gates that merely assert a transcript exists. Fix the
contract rather than disabling strict mode for unattended work.

### A run refuses to resume

Resume verifies the frozen workflow and immutable input. Review source drift
before using `--force-drift`; input drift is never forceable. Inspect the run
first with `piw inspect WORKFLOW RUN_ID --json`.
