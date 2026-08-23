# Setup

## Requirements

- macOS or Linux
- Python 3.10 or newer
- Git, for per-step run history
- Bash, for command steps and gates
- Pi only when a workflow uses model, tool, or agent nodes

Shell-only workflows do not require an API key or model provider.

## Repository installation

```bash
git clone https://github.com/ali-abassi/pi-graph-core.git
cd pi-graph-core
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
./bin/piw validate examples/hello.steps.yaml --strict
./bin/piw run examples/hello.steps.yaml --input Ada --strict --json
```

The repository wrapper automatically selects `.venv/bin/python`. Override it
when needed:

```bash
PI_GRAPH_CORE_PYTHON=/path/to/python ./bin/piw --help
```

## Installed command

```bash
python3 -m pip install .
piw --help
```

## Model workflows

Install and authenticate Pi separately:

```bash
npm install -g @earendil-works/pi-coding-agent
pi
```

Pi Graph Core does not read provider keys itself. Pi handles provider
authentication. Do not place credentials in `steps.yaml`, prompts, command
arguments, committed run bundles, or repository files.

## Verify the checkout

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m py_compile scripts/*.py
./bin/piw validate examples/hello.steps.yaml --strict
./bin/piw run examples/hello.steps.yaml --input Ada --strict --json
```

If `yaml` or `jsonschema` cannot be imported, dependencies were installed into
a different interpreter. Use the repository wrapper or set
`PI_GRAPH_CORE_PYTHON` explicitly.
