# KSH default standards

> Framework defaults; `.conventions.md` and the surrounding script win.

## Structure

- Shebang `#!/bin/ksh` (or the repo's interpreter path); header block: purpose,
  usage line, parameters, exit codes, change history.
- Functions for any logic used twice or longer than a screen; `main`-style
  bottom section calling them.
- Configuration (paths, thresholds) at the top or sourced from the repo's env
  file — never scattered mid-script.

## Robustness

- Check every critical command's exit status; propagate failures — a batch
  script must not exit 0 after an internal failure.
- Beware pipelines: exit status is the LAST command's. Test intermediate
  failures explicitly (or use the repo's established pattern).
- `trap` cleanup for temp files and locks on EXIT/INT/TERM.
- Quote all variable expansions holding paths/user data: `"$var"`.
- Temp files via `mktemp` (or repo-standard temp dir + PID), never fixed names
  in /tmp.

## Logging & exit codes

- Log to the repo's standard log location with timestamps; echo a start line
  (script, args, pid) and a completion line (status, duration).
- Documented exit codes: 0 success; distinct non-zero codes for distinct
  failure classes, listed in the header.

## Oracle interaction

- `sqlplus -s` with heredoc; `WHENEVER SQLERROR EXIT FAILURE` and
  `WHENEVER OSERROR EXIT FAILURE` in every block; check sqlplus's exit code.
- Credentials from wallet/env/secure config — never inline in the script.

## Testing

- Support a dry-run/no-op mode where feasible for batch scripts.
- `ksh -n` clean; shellcheck advisory findings triaged.
