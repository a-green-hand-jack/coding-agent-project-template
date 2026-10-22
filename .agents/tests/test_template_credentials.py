"""probe-credentials.sh, setup-worktree.sh and diagnose-environment.sh against a
fixture shared credential file, a fixture inventory and a local HTTP server
standing in for the providers. No value may appear in any output."""
from __future__ import annotations

import http.server
import json
import os
import shutil
import subprocess
import tempfile
import threading
import unittest
import urllib.parse
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
VALUES = {
    "OPENAI_API_KEY": "sk-fixture-good-0001",
    "EXPIRED_API_KEY": "sk-fixture-expired-0002",
    "GEMINI_KEY": "AIza-fixture-0003",
    "UNLISTED_TOKEN": "ghp-fixture-0004",
    "NOPROBE_API_KEY": "sk-fixture-noprobe-0005",
    "PLACEHOLDER_API_KEY": "",
    "UNMARKED_API_KEY": "",
}
INVENTORY = """# Fixture inventory: names only.
credentials:
  - variable: OPENAI_API_KEY
    service: openai
    kind: api-key
    purpose: evaluation judge
    endpoint: {endpoint}/v1
    auth: bearer
    status: active
    probe: GET /models
  - variable: EXPIRED_API_KEY
    service: relay
    kind: subscription-key
    endpoint: {endpoint}/v1
    auth: header:x-api-key
    status: active
    notes: when the plan's budget is used up the relay answers 401 api_key_expired
    probe: GET /models anthropic-version=2023-06-01
  - variable: GEMINI_KEY
    service: gemini
    kind: api-key
    endpoint: {endpoint}
    auth: query:key
    status: active
    probe: GET /v1beta/models
  - variable: NOPROBE_API_KEY
    service: other
    kind: api-key
    status: active
  - variable: PLACEHOLDER_API_KEY
    service: vendor
    kind: api-key
    purpose: reached through another channel
    status: empty-placeholder
  - variable: UNMARKED_API_KEY
    service: vendor
    kind: api-key
    status: active
"""
PROJECT = """# Fixture credentials.yaml: the rows this project needs, by name.
shared_file: .project/credentials/shared.env
credentials:
  - variable: OPENAI_API_KEY
    consumer: evaluation judge
    required: true
  - variable: EXPIRED_API_KEY
    consumer: nightly relay runs
    required: false
  - variable: GEMINI_KEY
    exposed_as: GEMINI_API_KEY
    consumer: gemini CLI in the sandbox runner
  - variable: NOPROBE_API_KEY
    required: false
  - variable: PLACEHOLDER_API_KEY
    required: true
  - variable: MISSING_API_KEY
    required: true
"""


class Provider(http.server.BaseHTTPRequestHandler):
    seen: list[tuple[str, str]] = []

    def do_GET(self) -> None:  # noqa: N802
        url = urllib.parse.urlsplit(self.path)
        key = (self.headers.get("Authorization", "").removeprefix("Bearer ") or self.headers.get("x-api-key", "")
               or dict(urllib.parse.parse_qsl(url.query)).get("key", ""))
        Provider.seen.append((url.path, key))
        if key == VALUES["EXPIRED_API_KEY"]:
            body = {"error": {"code": "api_key_expired", "message": f"key {key} expired"}}
            self.send_response(401)
        elif key in (VALUES["OPENAI_API_KEY"], VALUES["GEMINI_KEY"]):
            body = {"data": []}
            self.send_response(200)
        else:
            body = {"error": {"type": "invalid_key", "message": f"no such key {key}"}}
            self.send_response(401)
        data = json.dumps(body).encode()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args) -> None:
        pass


class CredentialTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory(prefix="probe-fixture-")
        self.addCleanup(directory.cleanup)
        base = Path(directory.name)
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Provider)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        Provider.seen = []

        device = base / "device"
        device.mkdir(mode=0o700)
        self.shared = device / "shared.env"
        self.shared.write_text("".join(f"{name}={value}\n" for name, value in VALUES.items()), encoding="utf-8")
        self.inventory = device / "inventory.yaml"
        self.inventory.write_text(INVENTORY.format(endpoint=f"http://127.0.0.1:{server.server_port}"),
                                  encoding="utf-8")
        for path in (self.shared, self.inventory):
            path.chmod(0o600)

        self.root = base / "project"
        (self.root / ".agents").mkdir(parents=True)
        shutil.copytree(REPOSITORY / ".agents/scripts", self.root / ".agents/scripts")
        (self.root / "credentials.yaml").write_text(PROJECT, encoding="utf-8")
        (self.root / ".project/credentials").mkdir(parents=True)
        (self.root / ".project/credentials/shared.env").symlink_to(self.shared)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)

    def run_script(self, name: str, *arguments: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(["bash", f".agents/scripts/{name}", *arguments], cwd=self.root,
                                capture_output=True, text=True, check=False)
        for value in filter(None, VALUES.values()):
            self.assertNotIn(value, result.stdout + result.stderr)
        return result

    def test_check_marks_placeholders_and_missing_rows(self) -> None:
        result = self.run_script("probe-credentials.sh", "--check")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        for line in ("error inventory: no row for UNLISTED_TOKEN, which the shared file sets",
                     "error inventory UNMARKED_API_KEY: empty in the shared file but marked `active`;"
                     " mark it empty-placeholder",
                     "error credential PLACEHOLDER_API_KEY: the inventory marks it empty-placeholder",
                     "error credential MISSING_API_KEY: no inventory row",
                     "ok    credential OPENAI_API_KEY: present",
                     "ok    credential GEMINI_KEY: present"):
            self.assertIn(line, result.stdout)
        self.assertNotIn("PLACEHOLDER_API_KEY: empty in the shared file", result.stdout)
        self.assertEqual(Provider.seen, [], "--check must not reach the network")

    def test_setup_reports_missing_rows_and_placeholders_and_passes_once_fixed(self) -> None:
        result = self.run_script("setup-worktree.sh")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("error credential PLACEHOLDER_API_KEY: the inventory marks it empty-placeholder", result.stdout)
        self.assertIn("error credential MISSING_API_KEY: no inventory row", result.stdout)
        self.assertIn("worktree initialized", result.stdout)

        # The device inventory complete, and the project needing only usable rows.
        self.inventory.write_text(self.inventory.read_text(encoding="utf-8").replace(
            "  - variable: UNMARKED_API_KEY\n    service: vendor\n    kind: api-key\n    status: active\n",
            "  - variable: UNMARKED_API_KEY\n    service: vendor\n    kind: api-key\n    status: empty-placeholder\n"
            "  - variable: UNLISTED_TOKEN\n    service: github\n    kind: repo-token\n    status: active\n"),
            encoding="utf-8")
        project = self.root / "credentials.yaml"
        project.write_text(PROJECT.split("  - variable: PLACEHOLDER_API_KEY")[0], encoding="utf-8")
        result = self.run_script("setup-worktree.sh")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("error", result.stdout)

    def test_probes_print_status_lines_only(self) -> None:
        result = self.run_script("probe-credentials.sh")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            "credential OPENAI_API_KEY: ok (required; GET /models: 200)",
            "credential EXPIRED_API_KEY: failed (optional; GET /models: 401 api_key_expired)",
            "credential GEMINI_KEY: ok (required; GET /v1beta/models: 200)",
            "credential NOPROBE_API_KEY: not-probed (optional; no probe in the inventory row)",
            "credential PLACEHOLDER_API_KEY: failed (required; the inventory marks it empty-placeholder)",
            "credential MISSING_API_KEY: failed (required; no inventory row)",
        ])
        # The values were read in the probe's process and sent only in the requests.
        self.assertEqual(sorted(Provider.seen), sorted([
            ("/v1/models", VALUES["OPENAI_API_KEY"]), ("/v1/models", VALUES["EXPIRED_API_KEY"]),
            ("/v1beta/models", VALUES["GEMINI_KEY"])]))

    def test_diagnose_gives_each_credential_its_status(self) -> None:
        result = self.run_script("diagnose-environment.sh")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        for line in ("ok   credential OPENAI_API_KEY: ok (required; GET /models: 200)",
                     "warn credential EXPIRED_API_KEY: failed (optional; GET /models: 401 api_key_expired)",
                     "ok   credential GEMINI_KEY: ok (required; GET /v1beta/models: 200)",
                     "skip credential NOPROBE_API_KEY: not-probed (optional; no probe in the inventory row)",
                     "FAIL credential PLACEHOLDER_API_KEY: failed (required; the inventory marks it"
                     " empty-placeholder)",
                     "FAIL credential MISSING_API_KEY: failed (required; no inventory row)"):
            self.assertIn(line, result.stdout)

    def test_a_device_without_the_shared_file_only_skips(self) -> None:
        (self.root / ".project/credentials/shared.env").unlink()
        result = self.run_script("probe-credentials.sh", "--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("skip  credentials: no shared credential file", result.stdout)
        result = self.run_script("probe-credentials.sh")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("credential OPENAI_API_KEY: not-probed (no shared credential file on this device)",
                      result.stdout)
        self.assertEqual(self.run_script("setup-worktree.sh").returncode, 0)

    def test_a_project_without_credentials_yaml_is_unchanged(self) -> None:
        (self.root / "credentials.yaml").unlink()
        result = self.run_script("setup-worktree.sh")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("credential", result.stdout)
        result = self.run_script("diagnose-environment.sh")
        self.assertIn("skip credentials: no credentials.yaml (llm-credentials)", result.stdout)
        self.assertNotIn("credential ", result.stdout.replace("skip credentials:", ""))
        self.assertEqual(Provider.seen, [])

    def test_the_device_inventory_can_be_checked_without_a_project(self) -> None:
        (self.root / "credentials.yaml").unlink()
        result = self.run_script("probe-credentials.sh", "--check", "--shared-file", str(self.shared))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("error inventory: no row for UNLISTED_TOKEN", result.stdout)
        self.shared.chmod(0o644)
        self.assertIn("warn  credentials: shared.env is readable by others",
                      self.run_script("probe-credentials.sh", "--check", "--shared-file", str(self.shared)).stdout)


if __name__ == "__main__":
    unittest.main()
