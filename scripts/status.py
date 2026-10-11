#!/usr/bin/env python3
"""status.py — read, check, and update a task workspace's STATUS.md.

STATUS.md is the resume point every stage depends on. Reading it by eye lets a
gate check pass on a misread line; editing it by hand lets a log entry or a
stage line get lost. This tool makes both deterministic: skills call it to
CHECK a gate (non-zero exit = do not proceed) and to RECORD a transition
(atomic rewrite, log line appended automatically).

Usage:
    status.py show     <ws>                          fields, stages, next action (no log)
    status.py get      <ws> <field-or-stage>         one value; repos-analyzed prints one path per line
    status.py require  <ws> <stage>=<state>[,<state>...] ...
                                                     exit 3 unless every stage is in an allowed state
    status.py set      <ws> <stage>=<state> [--next TEXT] [--log TEXT]
    status.py field    <ws> <name> <value> [--log TEXT]
                                                     set a header field (branch.<repo>, current-step, ...)
    status.py next     <ws> TEXT                     replace the Next action paragraph
    status.py log      <ws> TEXT                     append a timestamped log line
    status.py validate <ws> [--structure-only]       check structure; exit 1 on problems
                                                     (--structure-only: skip path existence, for
                                                     illustrative workspaces like examples/)

<ws> is the task workspace directory (work/<task-id>) or its STATUS.md.

States: pending | in-progress | done | approved | waived. In `require`,
`done` is also satisfied by `approved` (an approved stage is finished), so
`require ws research=done` accepts either; `approved` and `waived` match only
themselves. Unknown stage names are an error, never a silent pass.

Exit codes: 0 ok, 1 usage/parse error, 3 gate not met.
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
from datetime import datetime, timezone

STATES = ("pending", "in-progress", "done", "approved", "waived")
FIELD_RE = re.compile(r"^- ([A-Za-z0-9][A-Za-z0-9._-]*): ?(.*)$")
STAGE_RE = re.compile(r"^([a-z][a-z0-9-]*): ?(.*)$")
GATE_NOT_MET = 3


class StatusError(Exception):
    pass


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve(ws: str) -> str:
    path = os.path.join(ws, "STATUS.md") if os.path.isdir(ws) else ws
    if not os.path.isfile(path):
        raise StatusError(f"no STATUS.md at {path}")
    return path


class Status:
    """STATUS.md as an ordered list of lines plus indexes into it.

    Edits replace or insert individual lines, so anything the parser does not
    understand (extra prose, hand-added sections) survives a rewrite untouched.
    """

    def __init__(self, path: str):
        self.path = path
        with open(path, encoding="utf-8") as f:
            self.lines = f.read().splitlines()
        self._index()

    def _index(self) -> None:
        self.fields: dict[str, int] = {}
        self.stages: dict[str, int] = {}
        self.sections: dict[str, int] = {}
        section = None
        for i, line in enumerate(self.lines):
            if line.startswith("## "):
                section = line[3:].strip().lower()
                self.sections[section] = i
                continue
            if section is None:
                m = FIELD_RE.match(line)
                if m:
                    self.fields[m.group(1)] = i
            elif section == "stage gates":
                m = STAGE_RE.match(line)
                if m and not line.startswith("Legend"):
                    self.stages[m.group(1)] = i

    def section_end(self, name: str) -> int:
        start = self.sections[name]
        later = [i for i in self.sections.values() if i > start]
        return min(later) if later else len(self.lines)

    # --- reads ---------------------------------------------------------------

    def field(self, name: str) -> str:
        return FIELD_RE.match(self.lines[self.fields[name]]).group(2).strip()

    def stage(self, name: str) -> str:
        return STAGE_RE.match(self.lines[self.stages[name]]).group(2).strip()

    def stage_state(self, name: str) -> str:
        # "waived by user (2026-08-01)" -> "waived"; free text after the state is a note
        raw = self.stage(name)
        return raw.split()[0] if raw else ""

    def repos_analyzed(self) -> list[str]:
        if "repos analyzed" not in self.sections:
            return []
        out = []
        for line in self.lines[self.sections["repos analyzed"] + 1:self.section_end("repos analyzed")]:
            m = re.match(r"^\s*- (/.*)$", line)
            if m:
                out.append(m.group(1).strip())
        return out

    def next_action(self) -> str:
        if "next action" not in self.sections:
            return ""
        body = self.lines[self.sections["next action"] + 1:self.section_end("next action")]
        return "\n".join(body).strip()

    # --- writes --------------------------------------------------------------

    def set_stage(self, name: str, value: str) -> None:
        if name not in self.stages:
            raise StatusError(f"unknown stage '{name}' (stages: {', '.join(self.stages)})")
        self.lines[self.stages[name]] = f"{name}: {value}"

    def set_field(self, name: str, value: str) -> None:
        if not FIELD_RE.match(f"- {name}: x"):
            raise StatusError(f"invalid field name '{name}'")
        line = f"- {name}: {value}"
        if name in self.fields:
            self.lines[self.fields[name]] = line
        else:
            # append after the last header field so the header stays one block
            at = max(self.fields.values()) + 1 if self.fields else 1
            self.lines.insert(at, line)
        self._index()

    def set_next(self, text: str) -> None:
        if "next action" not in self.sections:
            raise StatusError("STATUS.md has no '## Next action' section")
        start, end = self.sections["next action"] + 1, self.section_end("next action")
        self.lines[start:end] = ["", text.strip(), ""]
        self._index()

    def append_log(self, text: str) -> None:
        if "log" not in self.sections:
            self.lines += ["", "## Log", ""]
            self._index()
        end = self.section_end("log")
        while end > self.sections["log"] + 1 and not self.lines[end - 1].strip():
            end -= 1
        self.lines.insert(end, f"- {now()} {' '.join(text.split())}")
        self._index()

    def save(self) -> None:
        # atomic: a crash mid-write leaves the previous STATUS.md, never half of one
        d = os.path.dirname(os.path.abspath(self.path))
        fd, tmp = tempfile.mkstemp(dir=d, prefix=".STATUS.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write("\n".join(self.lines).rstrip("\n") + "\n")
            os.replace(tmp, self.path)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    # --- checks --------------------------------------------------------------

    def problems(self, check_paths: bool = True) -> list[str]:
        out = []
        for f in ("task-id", "pipeline", "work-repo", "workspace-root"):
            if f not in self.fields:
                out.append(f"missing header field '{f}'")
        for f in ("work-repo", "workspace-root") if check_paths else ():
            if f in self.fields:
                v = self.field(f)
                if not os.path.isabs(v):
                    out.append(f"{f} is not an absolute path: {v}")
                elif not os.path.isdir(v):
                    out.append(f"{f} does not exist: {v}")
        for s in ("stage gates", "next action", "log"):
            if s not in self.sections:
                out.append(f"missing section '## {s.capitalize()}'")
        if not self.stages:
            out.append("no stages under '## Stage gates'")
        for name in self.stages:
            st = self.stage_state(name)
            if st not in STATES:
                out.append(f"stage '{name}' has unknown state '{self.stage(name)}' (expected one of {', '.join(STATES)})")
        # a finished stage after an unstarted one means a gate was skipped
        order = list(self.stages)
        for i, name in enumerate(order):
            if self.stage_state(name) in ("done", "approved"):
                for prev in order[:i]:
                    if self.stage_state(prev) == "pending":
                        out.append(f"stage '{name}' is {self.stage_state(name)} but earlier stage '{prev}' is pending")
        return out


def parse_pair(arg: str) -> tuple[str, str]:
    if "=" not in arg:
        raise StatusError(f"expected <stage>=<state>, got '{arg}'")
    k, v = arg.split("=", 1)
    return k.strip(), v.strip()


def satisfied(actual: str, allowed: list[str]) -> bool:
    if actual in allowed:
        return True
    return actual == "approved" and "done" in allowed


def take_opt(argv: list[str], name: str) -> str | None:
    if name in argv:
        i = argv.index(name)
        if i + 1 >= len(argv):
            raise StatusError(f"{name} needs a value")
        val = argv[i + 1]
        del argv[i:i + 2]
        return val
    return None


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv and argv[0] in ("-h", "--help") else 1
    cmd, ws, rest = argv[0], argv[1], argv[2:]
    st = Status(resolve(ws))

    if cmd == "show":
        for f in st.fields:
            print(f"{f}: {st.field(f)}")
        repos = st.repos_analyzed()
        if repos:
            print("repos-analyzed:")
            for r in repos:
                print(f"  - {r}")
        print("stages:")
        for s in st.stages:
            print(f"  {s}: {st.stage(s)}")
        print(f"next: {st.next_action()}")
        return 0

    if cmd == "get":
        if len(rest) != 1:
            raise StatusError("usage: get <ws> <field-or-stage>")
        key = rest[0]
        if key == "repos-analyzed":
            print("\n".join(st.repos_analyzed()))
        elif key == "next":
            print(st.next_action())
        elif key in st.fields:
            print(st.field(key))
        elif key in st.stages:
            print(st.stage(key))
        else:
            raise StatusError(f"no field or stage '{key}'")
        return 0

    if cmd == "require":
        if not rest:
            raise StatusError("usage: require <ws> <stage>=<state>[,<state>] ...")
        failed = []
        for arg in rest:
            name, want = parse_pair(arg)
            allowed = [w.strip() for w in want.split(",") if w.strip()]
            bad = [w for w in allowed if w not in STATES]
            if bad:
                raise StatusError(f"unknown state(s) {bad} in '{arg}'")
            if name not in st.stages:
                raise StatusError(f"unknown stage '{name}' for pipeline "
                                  f"'{st.field('pipeline') if 'pipeline' in st.fields else '?'}' "
                                  f"(stages: {', '.join(st.stages)})")
            actual = st.stage_state(name)
            if not satisfied(actual, allowed):
                failed.append(f"{name} is '{st.stage(name)}', need {' or '.join(allowed)}")
        if failed:
            print("GATE NOT MET: " + "; ".join(failed), file=sys.stderr)
            print(f"next action recorded: {st.next_action()}", file=sys.stderr)
            return GATE_NOT_MET
        print("gate ok: " + ", ".join(rest))
        return 0

    if cmd == "set":
        nxt = take_opt(rest, "--next")
        log = take_opt(rest, "--log")
        if len(rest) != 1:
            raise StatusError("usage: set <ws> <stage>=<state> [--next TEXT] [--log TEXT]")
        name, value = parse_pair(rest[0])
        if not value or value.split()[0] not in STATES:
            raise StatusError(f"state must start with one of {', '.join(STATES)}; got '{value}'")
        old = st.stage(name) if name in st.stages else None
        st.set_stage(name, value)
        if nxt:
            st.set_next(nxt)
        st.append_log(log or f"{name}: {old} -> {value}")
        st.save()
        print(f"{name}: {value}")
        return 0

    if cmd == "field":
        log = take_opt(rest, "--log")
        if len(rest) != 2:
            raise StatusError("usage: field <ws> <name> <value> [--log TEXT]")
        st.set_field(rest[0], rest[1])
        if log:
            st.append_log(log)
        st.save()
        print(f"{rest[0]}: {rest[1]}")
        return 0

    if cmd == "next":
        if len(rest) != 1:
            raise StatusError("usage: next <ws> TEXT")
        st.set_next(rest[0])
        st.save()
        return 0

    if cmd == "log":
        if len(rest) != 1:
            raise StatusError("usage: log <ws> TEXT")
        st.append_log(rest[0])
        st.save()
        return 0

    if cmd == "validate":
        if rest not in ([], ["--structure-only"]):
            raise StatusError("usage: validate <ws> [--structure-only]")
        probs = st.problems(check_paths=not rest)
        for p in probs:
            print(f"problem: {p}", file=sys.stderr)
        if not probs:
            print("STATUS.md ok")
        return 1 if probs else 0

    raise StatusError(f"unknown command '{cmd}'")


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except StatusError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
