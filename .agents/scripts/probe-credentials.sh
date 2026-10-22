#!/usr/bin/env bash
# Check and probe credentials by name, never printing a value (llm-credentials):
#
#   probe-credentials.sh [--check] [--shared-file PATH] [--all | VARIABLE...]
#
# The project's credentials.yaml names the inventory rows it needs and the link
# to the device's shared credential file (shared_file); the device's
# inventory.yaml sits beside the file the link resolves to. --shared-file PATH
# names the shared file directly, for checking a device without a project.
#
# --check reads no network. It checks the inventory against the shared file
# (every variable has a row, an empty variable is marked empty-placeholder,
# field values are valid) and the project's rows (each exists, is not an
# empty placeholder or retired, and is set in the shared file), and prints
# `ok`, `warn` or `error` lines. A row the project marks `required: false`
# only warns. Exit 1 on an error.
#
# Without --check it runs each row's read-only probe and prints one line per
# credential: `credential <VARIABLE>: ok | failed | not-probed (<detail>)`,
# the detail starting with `required` or `optional` for a project row. The
# value is read in this process and sent only in the probe request; it never
# reaches a command line, an output line or a file. Rows come from
# credentials.yaml, the named variables, or with --all the whole inventory.
# Exit 1 when a required credential, or one named or listed with --all, failed.
#
# Exit 2: wrong arguments or a file this script cannot read.
set -euo pipefail
root=$(git rev-parse --show-toplevel)
cd "$root"
exec python3 -I - "$@" <<'PY'
import json
import os
import re
import stat
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PROJECT_FILE = "credentials.yaml"
KINDS = ("api-key", "oauth-token", "subscription-key", "repo-token")
STATUSES = ("active", "empty-placeholder", "retired", "rotate")
REQUIRED_FIELDS = ("variable", "service", "kind", "status")
NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
TIMEOUT = 10


class Failure(Exception):
    pass


def scalar(text: str) -> str:
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "'\"":
        return text[1:-1]
    return re.sub(r"\s+#.*$", "", text)


def read_rows(path: Path) -> tuple[dict, list[dict]]:
    """The YAML subset both files use: top-level `key: value` lines and one
    `credentials:` list of flat mappings, one `key: value` per line."""
    top: dict = {}
    rows: list[dict] = []
    in_list = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        item = re.match(r"^\s+- ([A-Za-z_][\w-]*):(?:\s+(.*))?$", line)
        more = re.match(r"^\s+([A-Za-z_][\w-]*):(?:\s+(.*))?$", line)
        key = re.match(r"^([A-Za-z_][\w-]*):(?:\s+(.*))?$", line)
        if key:
            in_list = key.group(1) == "credentials" and not key.group(2)
            if not in_list:
                top[key.group(1)] = scalar(key.group(2) or "")
        elif in_list and item:
            rows.append({item.group(1): scalar(item.group(2) or ""), "_line": number})
        elif in_list and more and rows:
            rows[-1][more.group(1)] = scalar(more.group(2) or "")
        else:
            raise Failure(f"{path.name}:{number}: not a line of the supported format"
                          " (top-level `key: value` and a `credentials:` list of flat mappings)")
    return top, rows


def read_shared(path: Path) -> dict[str, str]:
    """KEY=value lines; the values stay in this process."""
    values: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.match(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$", line)
        if not match:
            raise Failure(f"the shared credential file, line {number}: not a KEY=value line")
        values[match.group(1)] = scalar(match.group(2))
    return values


class Output:
    def __init__(self, secrets: list[str]) -> None:
        self.secrets = [value for value in secrets if len(value) >= 4]
        self.errors = 0

    def line(self, text: str) -> None:
        if any(value in text for value in self.secrets):
            text = text.split(":", 1)[0] + ": (line withheld: it contained a credential value)"
        print(text, flush=True)

    def check(self, level: str, text: str) -> None:
        self.errors += level == "error"
        self.line(f"{level:<5} {text}")


def private(path: Path) -> bool:
    return not stat.S_IMODE(path.stat().st_mode) & 0o077


def check_inventory(rows: list[dict], values: dict[str, str], out: Output) -> None:
    by_name: dict[str, dict] = {}
    for row in rows:
        name = row.get("variable", "")
        missing = [field for field in REQUIRED_FIELDS if not row.get(field)]
        if missing:
            out.check("error", f"inventory row at line {row['_line']}: missing {', '.join(missing)}")
        if name and not NAME.match(name):
            out.check("error", f"inventory row at line {row['_line']}: `{name}` is not a variable name")
        if row.get("kind") and row["kind"] not in KINDS:
            out.check("error", f"inventory {name}: kind `{row['kind']}` is not one of {', '.join(KINDS)}")
        if row.get("status") and row["status"] not in STATUSES:
            out.check("error", f"inventory {name}: status `{row['status']}` is not one of {', '.join(STATUSES)}")
        if name in by_name:
            out.check("error", f"inventory {name}: a second row")
        by_name.setdefault(name, row)
    for name in values:
        if name not in by_name:
            out.check("error", f"inventory: no row for {name}, which the shared file sets")
    for name, row in by_name.items():
        if not name:
            continue
        status, value = row.get("status"), values.get(name)
        if value == "" and status != "empty-placeholder":
            out.check("error", f"inventory {name}: empty in the shared file but marked `{status}`;"
                               " mark it empty-placeholder")
        elif value and status == "empty-placeholder":
            out.check("warn", f"inventory {name}: marked empty-placeholder but set in the shared file")
        elif value is None and status in ("active", "rotate"):
            out.check("error", f"inventory {name}: marked `{status}` but not in the shared file")
    out.check("ok", f"inventory: {len(by_name)} rows for {len(values)} variables")


def project_row_problem(need: dict, row: dict | None, values: dict[str, str] | None) -> str:
    name = need["variable"]
    if row is None:
        return "no inventory row"
    if row.get("status") in ("empty-placeholder", "retired"):
        return f"the inventory marks it {row['status']}"
    if values is not None and not values.get(name):
        return "not set in the shared file"
    return ""


def probe(row: dict, value: str) -> tuple[str, str]:
    spec = row.get("probe", "").split()
    if not spec:
        return "not-probed", "no probe in the inventory row"
    if spec[0] != "GET" or len(spec) < 2:
        return "not-probed", "unsupported probe; write `GET <path or URL> [Header=value]...`"
    target = spec[1]
    url = target if re.match(r"https?://", target) else row.get("endpoint", "").rstrip("/") + "/" + target.lstrip("/")
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost")):
        return "not-probed", f"GET {target}: the probe needs an https endpoint"
    headers = dict(header.split("=", 1) for header in spec[2:] if "=" in header)
    auth = row.get("auth", "")
    if auth == "bearer":
        headers["Authorization"] = f"Bearer {value}"
    elif auth.startswith("header:") and auth[7:]:
        headers[auth[7:]] = value
    elif auth.startswith("query:") and auth[6:]:
        query = urllib.parse.urlencode({auth[6:]: value})
        url = urllib.parse.urlunsplit(parsed._replace(query=f"{parsed.query}&{query}" if parsed.query else query))
    else:
        return "not-probed", "the row's auth is not bearer, header:<Name> or query:<name>"

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(urllib.request.Request(url, headers=headers, method="GET"), timeout=TIMEOUT) as response:
            code, body = response.status, b""
    except urllib.error.HTTPError as error:
        code, body = error.code, error.read(65536)
    except (urllib.error.URLError, OSError) as error:
        return "failed", f"GET {target}: no response ({type(getattr(error, 'reason', error)).__name__})"
    if 200 <= code < 300:
        return "ok", f"GET {target}: {code}"
    detail = ""
    try:
        data = json.loads(body.decode("utf-8", errors="replace"))
        error = data.get("error", data) if isinstance(data, dict) else {}
        error = error if isinstance(error, dict) else {"code": error}
        detail = next((str(error[key]) for key in ("code", "type", "status")
                       if isinstance(error.get(key), (str, int))
                       and re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", str(error[key]))), "")
    except ValueError:
        pass
    return "failed", f"GET {target}: {code}{' ' + detail if detail else ''}"


def main(arguments: list[str]) -> int:
    check, everything, shared_arg, names = False, False, None, []
    while arguments:
        argument = arguments.pop(0)
        if argument == "--check":
            check = True
        elif argument == "--all":
            everything = True
        elif argument == "--shared-file" and arguments:
            shared_arg = arguments.pop(0)
        elif argument.startswith("-") or not NAME.match(argument):
            print("usage: probe-credentials.sh [--check] [--shared-file PATH] [--all | VARIABLE...]", file=sys.stderr)
            return 2
        else:
            names.append(argument)
    project = Path(PROJECT_FILE)
    top, needs = read_rows(project) if project.is_file() else ({}, [])
    for need in needs:
        if not NAME.match(need.get("variable", "")):
            raise Failure(f"{PROJECT_FILE}:{need['_line']}: each row needs a `variable:` name")
        need["required"] = need.get("required", "true") != "false"
    if shared_arg is None and not project.is_file():
        print(f"skip  credentials: no {PROJECT_FILE} (llm-credentials)")
        return 0
    shared = Path(shared_arg or top.get("shared_file", ""))
    if not str(shared) or str(shared) == ".":
        raise Failure(f"{PROJECT_FILE} has no `shared_file:` (the link to the shared credential file)")
    if names:
        needs = [next((need for need in needs if need["variable"] == name), {"variable": name}) for name in names]

    out = Output([])
    if not shared.exists():
        if check:
            out.check("skip", f"credentials: no shared credential file at {shared} on this device")
        else:
            for need in needs:
                out.line(f"credential {need['variable']}: not-probed (no shared credential file on this device)")
        return 0
    real = shared.resolve()
    values = read_shared(real)
    out = Output(list(values.values()))
    inventory_path = real.parent / "inventory.yaml"
    rows = read_rows(inventory_path)[1] if inventory_path.is_file() else None
    by_name = {row.get("variable"): row for row in rows or []}
    if everything:
        needs = [{"variable": row["variable"]} for row in rows or [] if row.get("variable")]

    def level(need: dict) -> str:
        return "error" if need.get("required", True) else "warn"

    def label(need: dict) -> str:
        return "" if "required" not in need else ("required; " if need["required"] else "optional; ")

    if check:
        for path in (real, inventory_path):
            if path.is_file() and not private(path):
                out.check("warn", f"credentials: {path.name} is readable by others; chmod 0600 it")
        if rows is None:
            out.check("warn", "credentials: no inventory.yaml beside the shared credential file (llm-credentials)")
        else:
            check_inventory(rows, values, out)
        for need in needs:
            name = need["variable"]
            problem = project_row_problem(need, by_name.get(name) if rows is not None else {}, values)
            if problem:
                out.check(level(need), f"credential {name}: {problem}")
            else:
                status = by_name.get(name, {}).get("status")
                out.check("warn" if status == "rotate" else "ok",
                          f"credential {name}: {'marked rotate' if status == 'rotate' else 'present'}")
            for override in filter(None, re.split(r"[,\s]+", need.get("overrides", ""))):
                overrides = shared.parent / "overrides.env"
                if not overrides.is_file() or override not in read_shared(overrides):
                    out.check("warn", f"credential {name}: override {override} is not in {overrides}")
        return 1 if out.errors else 0

    failed_required = False
    for need in needs:
        name = need["variable"]
        if rows is None:
            out.line(f"credential {name}: not-probed ({label(need)}no inventory.yaml beside the shared file)")
            continue
        problem = project_row_problem(need, by_name.get(name), values)
        if problem:
            status, detail = "failed", problem
        else:
            status, detail = probe(by_name[name], values[name])
        failed_required |= status == "failed" and need.get("required", True)
        out.line(f"credential {name}: {status} ({label(need)}{detail})")
    return 1 if failed_required else 0


try:
    sys.exit(main(sys.argv[1:]))
except (Failure, OSError, UnicodeDecodeError) as failure:
    print(f"probe-credentials: {failure}", file=sys.stderr)
    sys.exit(2)
PY
