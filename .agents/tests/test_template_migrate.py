"""migrate-assets.sh and new-agent-prompt.sh against fixture repositories: the
project's migrate-project.rules with exact names and wildcards, its validation,
and the handoff prompt's rule about where a session keeps its own files. They
write only to temporary directories."""
from __future__ import annotations

import json
import os
import shlex
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
MIGRATE = REPOSITORY / ".agents/scripts/migrate-assets.sh"
PROMPT = REPOSITORY / ".agents/scripts/new-agent-prompt.sh"
TEARDOWN = REPOSITORY / ".agents/scripts/teardown-worktree.sh"


def verify_copy(source: str | Path, copy: str | Path) -> subprocess.CompletedProcess[str]:
    """Run the exact verifier on nodes created independently of native cp."""
    code = MIGRATE.read_text().split('<<\'PY\'\n', 1)[1].split("\nPY\n", 1)[0]
    return subprocess.run(
        [sys.executable, "-I", "-", str(source), str(copy)], input=code,
        text=True, capture_output=True, timeout=3,
    )


class MigrateRules(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp(prefix="migrate-test-"))
        self.addCleanup(shutil.rmtree, self.temp, ignore_errors=True)
        self.worktree = self.temp / "worktree"
        self.destination = self.temp / "dev"
        (self.worktree / ".agents/scripts").mkdir(parents=True)
        (self.worktree / ".project/state").mkdir(parents=True)
        (self.worktree / ".project/state/initial-prompt.md").write_text("prompt\n")
        (self.destination / ".project").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(self.worktree)], check=True)

    def project_file(self, name: str, text: str = "content\n") -> None:
        (self.worktree / ".project" / name).write_text(text)

    def rules(self, text: str) -> None:
        (self.worktree / ".agents/scripts/migrate-project.rules").write_text(text)

    def migrate(self, *extra: str, env: dict[str, str] | None = None,
                destination: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(MIGRATE), "--to", destination or str(self.destination), *extra],
            cwd=self.worktree, text=True, capture_output=True,
            timeout=10, env=env,
        )

    def copied(self) -> Path:
        (migration,) = (self.destination / ".project/migrations").iterdir()
        return migration

    def test_fifo_tree_migrates_and_verifies_links_afterward(self) -> None:
        runs = self.worktree / ".project/runs/r1"
        runs.mkdir(parents=True)
        os.mkfifo(runs / "stream.fifo")
        (runs / "regular.txt").write_text("receipt\n")
        (runs / "broken-link").symlink_to("missing")
        (runs / "pipe-link").symlink_to("stream.fifo")
        (runs / ".empty").mkdir()
        self.project_file("assets.links", "data=/srv/data\n")
        (self.worktree / "assets").mkdir()
        (self.worktree / "assets/data").symlink_to("/srv/data")

        result = self.migrate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("verified: 4 item(s) identical", result.stdout)
        self.assertIn("source was not deleted", result.stdout)
        self.assertTrue(stat.S_ISFIFO((self.copied() / "runs/r1/stream.fifo").lstat().st_mode))
        self.assertTrue(stat.S_ISFIFO((runs / "stream.fifo").lstat().st_mode))
        self.assertEqual(os.readlink(self.destination / "assets/data"), "/srv/data")
        self.assertEqual((self.destination / ".project/assets.links").read_text(), "data=/srv/data\n")

    def verification_tree(self) -> Path:
        runs = self.worktree / ".project/runs"
        runs.mkdir()
        (runs / "file").write_text("receipt\n")
        (runs / "directory").mkdir()
        (runs / "directory/.hidden").write_bytes(b"\0\xff\n")
        (runs / "empty").mkdir()
        os.mkfifo(runs / "stream\n pipe")
        (runs / "broken").symlink_to("missing\n")
        (runs / "pipe-link").symlink_to("stream\n pipe")
        return runs

    def copy_hook(self, code: str) -> dict[str, str]:
        """Alter a real cp result at the copy/verification seam."""
        bin_dir = self.temp / "bin"
        bin_dir.mkdir(exist_ok=True)
        hook = bin_dir / "after-copy.py"
        hook.write_text(
            "import os, stat, sys\nfrom pathlib import Path\n"
            "if sys.argv[-2] == '.project/runs':\n"
            "    source = Path(sys.argv[-2])\n"
            "    copy = Path(sys.argv[-1]) / 'runs'\n"
            + "".join(f"    {line}\n" for line in code.splitlines())
        )
        wrapper = bin_dir / "cp"
        wrapper.write_text(
            "#!/usr/bin/env bash\nset -e\n"
            f"{shlex.quote(shutil.which('cp'))} \"$@\"\n"
            f"{shlex.quote(sys.executable)} {shlex.quote(str(hook))} \"$@\"\n"
        )
        wrapper.chmod(0o755)
        return {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"}

    def test_fifo_and_unusual_names_verify_without_reading_streams(self) -> None:
        self.verification_tree()
        assets = self.worktree / "assets"
        assets.mkdir()
        os.mkfifo(assets / "pipe")
        result = self.migrate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        copy = self.copied() / "runs"
        self.assertEqual(os.readlink(copy / "broken"), "missing\n")
        self.assertEqual((copy / "directory/.hidden").read_bytes(), b"\0\xff\n")
        self.assertTrue((copy / "empty").is_dir())
        self.assertTrue(stat.S_ISFIFO((self.destination / "assets/pipe").lstat().st_mode))

    def test_native_socket_copy_is_verified_or_refused_when_omitted(self) -> None:
        runs = self.worktree / ".project/runs"
        runs.mkdir()
        stream = socket.socket(socket.AF_UNIX)
        self.addCleanup(stream.close)
        stream.bind(str(runs / "socket"))
        probe = self.temp / "native-copy"
        native = subprocess.run(
            ["cp", "-a", str(runs), str(probe)], text=True, capture_output=True, timeout=5,
        )
        result = self.migrate()
        if (probe / "socket").exists():
            self.assertEqual(native.returncode, 0, native.stderr)
            self.assertTrue(stat.S_ISSOCK((probe / "socket").lstat().st_mode))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(stat.S_ISSOCK((self.copied() / "runs/socket").lstat().st_mode))
        else:
            # BSD cp may warn but exit 0 after omitting sockets. Migration must
            # refuse that incomplete copy, never silently waive the missing node.
            self.assertIn("socket", native.stderr)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("verified:", result.stdout)
            if native.returncode == 0:
                self.assertIn("DIFFERS: .project/runs", result.stderr)
                self.assertIn("verification FAILED", result.stderr)
        self.assertTrue(stat.S_ISSOCK((runs / "socket").lstat().st_mode))

    def test_missing_socket_after_copy_fails_verification(self) -> None:
        runs = self.worktree / ".project/runs"
        runs.mkdir()
        stream = socket.socket(socket.AF_UNIX)
        self.addCleanup(stream.close)
        stream.bind(str(runs / "socket"))
        result = self.migrate(env=self.copy_hook("(copy / 'socket').unlink(missing_ok=True)"))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("DIFFERS: .project/runs", result.stderr)
        self.assertIn("verification FAILED", result.stderr)
        self.assertNotIn("verified:", result.stdout)

    def test_top_level_fifo_is_verified_by_type(self) -> None:
        os.mkfifo(self.worktree / ".project/runs")
        result = self.migrate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(stat.S_ISFIFO((self.copied() / "runs").lstat().st_mode))

    def test_teardown_entrypoint_finishes_with_fifo(self) -> None:
        self.verification_tree()
        for script in (MIGRATE, TEARDOWN, MIGRATE.with_name("inspect-state.sh")):
            shutil.copy2(script, self.worktree / ".agents/scripts" / script.name)
        result = subprocess.run(
            ["bash", ".agents/scripts/teardown-worktree.sh", "--migrate-to", str(self.destination)],
            cwd=self.worktree, text=True, capture_output=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ready for managed worktree removal; no source directory was deleted", result.stdout)
        self.assertTrue(stat.S_ISFIFO((self.copied() / "runs/stream\n pipe").lstat().st_mode))

    def test_regular_content_is_checked_past_first_chunk(self) -> None:
        runs = self.worktree / ".project/runs"
        runs.mkdir()
        (runs / "file").write_bytes(b"x" * (1024 * 1024) + b"end")
        result = self.migrate(env=self.copy_hook(
            "with (copy / 'file').open('r+b') as output:\n"
            "    output.seek(-1, 2)\n"
            "    output.write(b'!')"
        ))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("verification FAILED", result.stderr)

    def test_verification_does_not_depend_on_diff_options_or_diagnostics(self) -> None:
        self.verification_tree()
        bin_dir = self.temp / "no-diff"
        bin_dir.mkdir()
        diff = bin_dir / "diff"
        diff.write_text("#!/usr/bin/env bash\necho 'diff must not be invoked' >&2\nexit 2\n")
        diff.chmod(0o755)
        result = self.migrate(env={**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("diff must not be invoked", result.stderr)

    def test_migration_needs_no_gnu_realpath_and_resolves_missing_destination(self) -> None:
        runs = self.worktree / ".project/runs"
        runs.mkdir()
        os.mkfifo(runs / "stream")
        bin_dir = self.temp / "bsd-tools"
        bin_dir.mkdir()
        realpath = bin_dir / "realpath"
        realpath.write_text(
            "#!/usr/bin/env bash\necho 'realpath: illegal option -- m' >&2\nexit 1\n"
        )
        realpath.chmod(0o755)
        link = self.worktree / "destination-link"
        link.symlink_to(self.destination, target_is_directory=True)
        # Resolve relative paths from the caller, including symlink parents,
        # missing components and '..', as GNU realpath -m did.
        self.destination = link / "new canonical"
        result = self.migrate(env={**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"},
                              destination="destination-link/missing/../new canonical")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f"migrated_to={self.destination.resolve()}", result.stdout)
        self.assertTrue(stat.S_ISFIFO((self.copied() / "runs/stream").lstat().st_mode))

    def test_resolved_destination_inside_source_still_stops_before_copy(self) -> None:
        link = self.temp / "source-link"
        link.symlink_to(self.worktree, target_is_directory=True)
        result = self.migrate(destination=str(link / "missing/../nested"))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("destination must be outside this worktree", result.stderr)
        self.assertFalse((self.worktree / "nested").exists())

    def test_mismatches_are_rejected_even_with_matching_special_files(self) -> None:
        self.verification_tree()
        changes = {
            "content": "(copy / 'file').write_text('changed')",
            "missing-file": "(copy / 'file').unlink()",
            "extra-file": "(copy / 'extra').touch()",
            "missing-fifo": "(copy / 'stream\\n pipe').unlink()",
            "fifo-as-file": "(copy / 'stream\\n pipe').unlink()\n(copy / 'stream\\n pipe').touch()",
            "file-as-fifo": "(copy / 'file').unlink()\nos.mkfifo(copy / 'file')",
            "link-target": "(copy / 'pipe-link').unlink()\n(copy / 'pipe-link').symlink_to('file')",
            "broken-target-newline": "(copy / 'broken').unlink()\n(copy / 'broken').symlink_to('missing')",
            "file-as-link": "(copy / 'file').unlink()\n(copy / 'file').symlink_to(source.resolve() / 'file')",
            "directory-as-link": "(copy / 'empty').rmdir()\n(copy / 'empty').symlink_to(source.resolve() / 'empty')",
            "missing-directory": "(copy / 'empty').rmdir()",
            "extra-directory": "(copy / 'extra').mkdir()",
        }
        for name, code in changes.items():
            with self.subTest(change=name):
                self.destination = self.temp / name
                self.destination.mkdir()
                result = self.migrate(env=self.copy_hook(code))
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("DIFFERS: .project/runs", result.stderr)
                self.assertIn("verification FAILED", result.stderr)
                self.assertNotIn("verified:", result.stdout)

    @unittest.skipIf(os.geteuid() == 0, "root bypasses permission errors")
    def test_read_and_directory_traversal_errors_fail_verification(self) -> None:
        runs = self.verification_tree()
        for name, path in (("read", runs / "file"), ("traverse", runs / "directory")):
            with self.subTest(error=name):
                self.destination = self.temp / name
                self.destination.mkdir()
                mode = path.stat().st_mode
                try:
                    result = self.migrate(env=self.copy_hook(f"Path({str(path)!r}).chmod(0)"))
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertIn("verification error:", result.stderr)
                    self.assertIn("Permission denied", result.stderr)
                    self.assertIn("verification FAILED", result.stderr)
                finally:
                    path.chmod(mode)

    def test_template_rules_migrate_state_assets_and_leave_no_unique_copy(self) -> None:
        state = self.worktree / ".project/state/initial-prompt.md"
        runs = self.worktree / ".project/runs/run-1"
        artifacts = self.worktree / ".project/artifacts"
        manifest = self.worktree / ".project/manifest"
        for directory in (runs, artifacts, manifest):
            directory.mkdir(parents=True)
        (runs / "receipt.json").write_text('{"status":"done"}\n')
        (artifacts / "report.md").write_text("result\n")
        (manifest / "inputs.yaml").write_text("inputs: []\n")
        self.project_file("assets.links", "data=/srv/data\n")
        self.project_file("home", "marker\n")
        self.project_file("worktree.env", "branch=test\n")
        (self.worktree / "assets").mkdir()
        (self.worktree / "assets/data").symlink_to("/srv/data")

        result = self.migrate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("verified: 6 item(s) identical", result.stdout)
        self.assertIn("source was not deleted", result.stdout)
        migration = self.copied()
        # Every kept .project/ entry reached the migration copy byte for byte.
        for source, copy in (
            (state, migration / "state/initial-prompt.md"),
            (runs / "receipt.json", migration / "runs/run-1/receipt.json"),
            (artifacts / "report.md", migration / "artifacts/report.md"),
            (manifest / "inputs.yaml", migration / "manifest/inputs.yaml"),
        ):
            self.assertEqual(copy.read_bytes(), source.read_bytes(), copy)
        # The link mapping is merged, and the link itself lands in the destination.
        self.assertEqual((self.destination / ".project/assets.links").read_text(),
                         "data=/srv/data\n")
        destination_link = self.destination / "assets/data"
        self.assertTrue(destination_link.is_symlink())
        self.assertEqual(os.readlink(destination_link), "/srv/data")
        # Setup-owned entries are not carried as unique copies.
        self.assertFalse((migration / "home").exists())
        self.assertFalse((migration / "worktree.env").exists())

    def test_wildcard_copies_matching_files(self) -> None:
        self.project_file("plan-12.md", "plan\n")
        self.project_file("plan-12-pr1.md", "plan pr1\n")
        self.rules("plan-*.md|copy|\n")
        result = self.migrate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("rule plan-*.md", result.stdout)
        self.assertIn("verified: 3 item(s) identical", result.stdout)
        migration = self.copied()
        self.assertEqual((migration / "plan-12.md").read_text(), "plan\n")
        self.assertEqual((migration / "plan-12-pr1.md").read_text(), "plan pr1\n")

    def test_file_without_a_rule_still_stops(self) -> None:
        self.project_file("plan-12.md")
        self.project_file("msg-coord-pr7.txt")
        self.rules("plan-*.md|copy|\n")
        result = self.migrate()
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertRegex(result.stdout, r"msg-coord-pr7\.txt\s+unknown")
        self.assertIn("migration stopped before copying anything", result.stderr)
        self.assertFalse((self.destination / ".project/migrations").exists())

    def test_without_a_rules_file_a_root_file_stops(self) -> None:
        self.project_file("plan-12.md")
        self.assertEqual(self.migrate().returncode, 3)

    def test_exact_name_wins_over_wildcard(self) -> None:
        self.project_file("plan-12.md")
        self.project_file("plan-13.md")
        # The wildcard comes first in the file, the exact name still decides.
        self.rules("plan-*.md|copy|\nplan-12.md|drop|scratch plan, kept in the Issue\n")
        result = self.migrate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"plan-12\.md\s+drop\s+\S+\s+scratch plan, kept in the Issue")
        self.assertRegex(result.stdout, r"plan-13\.md\s+copy\s+\S+\s+rule plan-\*\.md")
        self.assertEqual([p.name for p in self.copied().glob("plan-*")], ["plan-13.md"])

    def test_first_matching_wildcard_wins(self) -> None:
        self.project_file("plan-12.md")
        self.rules("plan-*|drop|temporary notes\n*.md|copy|\n")
        result = self.migrate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"plan-12\.md\s+drop\s+\S+\s+rule plan-\*: temporary notes")
        self.assertFalse((self.copied() / "plan-12.md").exists())

    def test_wildcard_does_not_match_other_names(self) -> None:
        self.project_file("notes.md")
        self.rules("plan-*.md|copy|\n")
        self.assertEqual(self.migrate().returncode, 3)

    def test_exact_name_rules_behave_as_before(self) -> None:
        self.project_file("setup.log", "log\n")
        self.rules("# comment\n\nsetup.log|copy|\n")
        result = self.migrate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"setup\.log\s+copy\s+\S+\s*\n")
        self.assertNotIn("rule setup.log", result.stdout)
        self.assertEqual((self.copied() / "setup.log").read_text(), "log\n")

    def test_also_and_skip_override_a_single_file(self) -> None:
        self.project_file("plan-12.md")
        self.project_file("msg.txt")
        self.project_file("other.txt")
        self.rules("plan-*.md|copy|\n")
        result = self.migrate("--also", "msg.txt", "--skip", "other.txt=not needed")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"msg\.txt\s+copy\s+\S+\s+copied because --also")
        self.assertRegex(result.stdout, r"other\.txt\s+skip\s+\S+\s+left behind on purpose: not needed")
        # A file a wildcard already migrates cannot be skipped.
        again = self.migrate("--skip", "plan-12.md=no")
        self.assertEqual(again.returncode, 2)

    def assert_rejected(self, rules: str, line: int, message: str) -> None:
        self.rules(rules)
        result = self.migrate()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn(f"migrate-project.rules:{line}:", result.stderr)
        self.assertIn(message, result.stderr)
        self.assertFalse((self.destination / ".project/migrations").exists())

    def test_validation_rejects_slash(self) -> None:
        self.assert_rejected("ok.txt|copy|\nstate/*|copy|\n", 2, "not a plain entry name")

    def test_validation_rejects_login_wildcard(self) -> None:
        self.assert_rejected("login-*|login|\n", 1, "wildcard cannot be a login")

    def test_validation_rejects_wildcards_matching_template_entries(self) -> None:
        for pattern, entry in (("st*", "state"), ("*", "state"), ("work?ree.env", "worktree.env"),
                               ("[hc]*", "home"), ("assets.*", "assets.links"), ("cred*", "credentials")):
            with self.subTest(pattern=pattern):
                self.assert_rejected(f"# first\n{pattern}|copy|\n", 2, f"matches {entry}")

    def test_validation_keeps_the_exact_name_checks(self) -> None:
        self.assert_rejected("state|copy|\n", 1, "template already has a rule for state")
        self.assert_rejected("a.txt|copy|\na.txt|copy|\n", 2, "second rule for a.txt")
        self.assert_rejected("plan-*|drop|\n", 1, "drop needs a reason")
        self.assert_rejected("plan-*|keep|\n", 1, "unknown action")

    def test_wildcard_duplicate_is_a_second_rule(self) -> None:
        self.assert_rejected("plan-*|copy|\nplan-*|copy|\n", 2, "second rule for plan-*")


class SpecialFileVerification(unittest.TestCase):
    """Verify independently created sockets and existing safe device nodes."""

    def test_socket_pairs_and_mismatched_or_missing_nodes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="socket-verify-") as temp:
            source, copy = Path(temp) / "source", Path(temp) / "copy"
            source.mkdir()
            copy.mkdir()
            with socket.socket(socket.AF_UNIX) as left, socket.socket(socket.AF_UNIX) as right:
                left.bind(str(source / "socket"))
                right.bind(str(copy / "socket"))
                result = verify_copy(source, copy)
                self.assertEqual(result.returncode, 0, result.stderr)
                (copy / "socket").unlink()
                os.mkfifo(copy / "socket")
                self.assertEqual(verify_copy(source, copy).returncode, 1)
                (copy / "socket").unlink()
                self.assertEqual(verify_copy(source, copy).returncode, 1)

    def test_character_devices_match_by_type_without_reading(self) -> None:
        if not all(Path(path).exists() and stat.S_ISCHR(os.lstat(path).st_mode)
                   for path in ("/dev/null", "/dev/zero")):
            self.skipTest("safe character-device fixtures unavailable")
        result = verify_copy("/dev/zero", "/dev/zero")
        self.assertEqual(result.returncode, 0, result.stderr)
        result = verify_copy("/dev/null", "/dev/zero")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_block_devices_match_by_type_and_reject_character_device(self) -> None:
        candidates = ("/dev/loop0", "/dev/sda", "/dev/disk0")
        devices = [path for path in candidates
                   if Path(path).exists() and stat.S_ISBLK(os.lstat(path).st_mode)]
        if not devices:
            self.skipTest("block-device nodes unavailable; never create privileged devices")
        result = verify_copy(devices[0], devices[-1])
        self.assertEqual(result.returncode, 0, result.stderr)
        if Path("/dev/null").exists():
            result = verify_copy(devices[0], "/dev/null")
            self.assertEqual(result.returncode, 1, result.stderr)


class HandoffPrompt(unittest.TestCase):
    def prompt(self, body: str, *arguments: str, coordinator: str | None = None) -> str:
        with tempfile.TemporaryDirectory(prefix="prompt-test-") as temp:
            payload = Path(temp) / "issue.json"
            payload.write_text(json.dumps({
                "number": 7, "title": "A title", "body": body,
                "url": "https://example.test/7",
            }), encoding="utf-8")
            gh = Path(temp) / "gh"
            gh.write_text(f"#!/usr/bin/env bash\ncat {shlex.quote(str(payload))}\n")
            gh.chmod(gh.stat().st_mode | stat.S_IXUSR)
            env = {**os.environ, "PATH": f"{temp}:{os.environ['PATH']}"}
            if coordinator is not None:
                mapping = Path(temp) / "coordinator mapping.md"
                mapping.write_text(coordinator, encoding="utf-8")
                arguments = (*arguments, str(mapping))
            result = subprocess.run(
                ["bash", str(PROMPT), "7", *arguments], cwd=REPOSITORY, env=env, text=True, capture_output=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_local_coordinator_mapping_is_literal_and_does_not_change_target(self) -> None:
        mapping = (
            "Coordinator: tpl-coord-1; pane fixture:p1; thread fixture-thread\n"
            "Identity: tpl-issue-7 implement attempt 2\n"
            "Reporting authorization: scoped events only; no commit/push/PR/merge/release\n"
            "Recovery: .project/state/events.md; owner tpl-issue-7; next active checkpoint\n"
            "Literal: $(exit 97) `exit 98`\n"
        )
        result = self.prompt("## Dispatch\n- coordinator: `tpl-coord-1`\n",
                             "feat/issue-7", "integration/issue-6", coordinator=mapping)
        self.assertIn(mapping, result)
        self.assertIn("PR target: integration/issue-6", result)
        self.assertNotIn("Before dispatch, append the local coordinator", result)
        for event in ("PR-created", "head-updated", "acceptance failures", "close-out changes"):
            self.assertIn(event, result)
        self.assertIn("Missing ACK stays pending", result)
        self.assertIn("ACK this handoff's scope", result)
        # The generated handoff must carry the shared-input gate and cadence,
        # not only delivery reporting; these checks do not prove live receipt.
        flat = " ".join(result.split())
        for boundary in ("Require explicit pause ACKs before starting",
                         "explicit return before resuming writes",
                         "allowed outputs", "independently immutable snapshot",
                         "keep routine progress local", "ACKs need no ACK",
                         "no fixed-time polling or heartbeats"):
            self.assertIn(boundary, flat)

    def test_missing_mapping_is_visible_and_bad_explicit_file_fails(self) -> None:
        result = self.prompt("")
        self.assertIn("Before dispatch, append the local coordinator mapping", result)
        self.assertIn("Do not infer cross-session authorization", result)
        with tempfile.TemporaryDirectory(prefix="prompt-mapping-test-") as temp:
            empty = Path(temp) / "empty.md"
            empty.touch()
            for path in (empty, Path(temp) / "missing.md", Path(temp)):
                with self.subTest(path=path.name):
                    failed = subprocess.run(
                        ["bash", str(PROMPT), "7", "feat/issue-7", "dev", str(path)],
                        cwd=REPOSITORY, text=True, capture_output=True,
                    )
                    self.assertEqual(failed.returncode, 2)
                    self.assertEqual(failed.stdout, "")
                    self.assertIn("readable, nonempty local file", failed.stderr)

    def test_prompt_uses_declared_parent_target_without_changing_the_default(self) -> None:
        default = self.prompt("")
        self.assertIn("PR target: dev", default)
        declared = self.prompt("", "feat/issue-7-child", "integration/issue-6")
        self.assertIn("Branch: feat/issue-7-child (create it from integration/issue-6", declared)
        self.assertIn("PR target: integration/issue-6", declared)
        self.assertNotIn("create it from dev", declared)

    def test_prompt_tells_the_session_where_its_files_go(self) -> None:
        flat = " ".join(self.prompt("").split())
        self.assertIn("plans, PR body drafts and messages to the coordinator", flat)
        self.assertIn(".project/state/", flat)
        self.assertIn("not in the root of .project/", flat)

    def test_prompt_carries_the_cost_and_dispatch_rules(self) -> None:
        flat = " ".join(self.prompt("").split())
        self.assertIn("cheapest token source", flat)
        self.assertIn("agent, provider, model and effort", flat)
        self.assertIn("re-dispatched", flat)
        self.assertIn("no Dispatch section yet", flat)
        for boundary in ("your own allowlisted HERDR identity variables",
                         "repository/common Git dir and native thread",
                         "supported --no-daemon isolation",
                         "only authorized read-only diagnosis",
                         "never fake variables or restart shared services",
                         "including after bootstrap"):
            self.assertIn(boundary, flat)

    def test_prompt_carries_the_issues_dispatch_record(self) -> None:
        body = (
            "## 最终目标\n\n做点事。\n\n## Dispatch\n\n"
            "- coordinator: `tpl-coord-1`\n"
            "- agent: Pi coding agent\n"
            "- provider: `cheap-relay`; model: `deepseek-v4.1-flash-1017`; effort: `high`\n"
            "- reason: hard: several planes\n"
            "- session: `tpl-issue-7`, branch `feat/issue-7-x`\n\n## 验收\n\n通过。\n"
        )
        flat = " ".join(self.prompt(body).split())
        self.assertIn(
            "- provider: `cheap-relay`; model: `deepseek-v4.1-flash-1017`; effort: `high`", flat)
        self.assertNotIn("no Dispatch section yet", flat)
        self.assertNotIn("## 验收", flat)


if __name__ == "__main__":
    unittest.main()
