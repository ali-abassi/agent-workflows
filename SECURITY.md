# Security policy

## Supported version

Security fixes are applied to the latest commit on `main`.

## Reporting a vulnerability

Do not open a public issue for a vulnerability. Use GitHub's private
vulnerability reporting for this repository:

1. Open the repository's **Security** tab.
2. Choose **Advisories**.
3. Choose **Report a vulnerability**.

Include the affected command or workflow, impact, reproduction steps, and any
suggested mitigation. Please avoid accessing data or systems you do not own.

## Execution boundary

Pi Graph Core executes workflow commands with the permissions and environment
of the invoking user. It is an orchestration and evidence layer, not a sandbox.

- Treat third-party `steps.yaml`, prompts, retrieved text, and tool output as
  untrusted.
- Run untrusted workflows inside a container or similarly isolated account.
- Give agent nodes the smallest practical tool allowlist.
- Keep credentials out of workflow files, prompts, command arguments, logs,
  artifacts, and committed run bundles.
- Review effectful commands before execution.

`tools:` restricts what Pi exposes to a model. It does not restrict shell
commands, filesystem access, child processes, network access, or inherited
credentials at the operating-system level.
