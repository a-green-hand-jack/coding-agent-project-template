"""Provider-free decision scenarios; no daemon, Herdr or live-delivery proof."""
from __future__ import annotations

import unittest
from dataclasses import dataclass, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = (ROOT / ".agents/skills/shared/issue-workflow/SKILL.md").read_text()
COMMUNICATION = (ROOT / ".agents/skills/shared/agent-communication/SKILL.md").read_text()
PROMPT = (ROOT / ".agents/scripts/shared/new-agent-prompt.sh").read_text()


@dataclass(frozen=True)
class Context:
    """Synthetic evidence, never a runtime identity resolver."""

    env: tuple[str, ...] = ("1", "fixture-w", "fixture-t", "fixture-p")
    returned: tuple[str, ...] = ("1", "fixture-w", "fixture-t", "fixture-p")
    live: bool = True
    repository_matches: bool = True
    thread_matches: bool = True
    diagnostic_authorization: bool = False
    visible_current_activity: bool = False
    returned_ownership: bool = False
    supports_isolation: bool = True
    proven_alternative: bool = False


def caller_action(c: Context) -> str:
    complete = (len(c.returned) == 4 and c.returned[0] == "1"
                and all(field.strip() for field in c.returned))
    resolved = complete and c.live and c.repository_matches and c.thread_matches
    exact = resolved and c.env == c.returned
    recovered = (resolved and c.diagnostic_authorization
                 and c.visible_current_activity and c.returned_ownership)
    if not (exact or recovered):
        return "diagnose-read-only" if c.diagnostic_authorization else "stop-unresolved"
    if not (c.supports_isolation or c.proven_alternative):
        return "stop-capability-gap"
    return "verify-worker-and-ack" if exact else "explicit-verified-ids"


def recovery_result(request: bool, old_exited: bool, corrected: bool, ack: bool) -> str:
    if old_exited and corrected and ack:
        return "verified"
    return "request-only" if request else "unresolved"


def restart_action(affected: set[str], approved_owners: set[str], authorized: bool) -> str:
    if not authorized or not affected.issubset(approved_owners):
        return "diagnose-only"
    return "request-then-verify"


def queue_result(thread: bool, submitted: bool, ack: bool,
                 status: str, draft: bool) -> str:
    if thread and submitted and ack:
        return "acknowledged"
    if thread and submitted:
        return "pending-inspect-before-fallback"
    if status in ("idle", "done") and not draft:
        return "record-gap-preflight-fallback"
    return "pending-no-safe-fallback"


class CodexContextScenarios(unittest.TestCase):
    def test_stale_live_wrong_and_missing_context(self) -> None:
        good = Context()
        cases = [
            (good, "verify-worker-and-ack"),
            (replace(good, live=False), "stop-unresolved"),
            (replace(good, env=("1", "old-w", "old-t", "old-p")), "stop-unresolved"),
            (replace(good, repository_matches=False), "stop-unresolved"),
            (replace(good, thread_matches=False), "stop-unresolved"),
            (replace(good, env=()), "stop-unresolved"),
            (replace(good, env=(), diagnostic_authorization=True), "diagnose-read-only"),
            (replace(good, env=(), diagnostic_authorization=True,
                     visible_current_activity=True, returned_ownership=True), "explicit-verified-ids"),
        ]
        for evidence, expected in cases:
            with self.subTest(evidence=evidence):
                self.assertEqual(caller_action(evidence), expected)

    def test_cwd_or_title_alone_cannot_recover(self) -> None:
        candidate = Context(env=(), diagnostic_authorization=True, returned_ownership=True)
        self.assertEqual(caller_action(candidate), "diagnose-read-only")
        self.assertIn("Cwd/title alone is insufficient", WORKFLOW)
        self.assertIn("Never export invented", WORKFLOW)

    def test_exact_identity_requires_all_four_nonempty_fields(self) -> None:
        invalid = ((), ("1",), ("1", "fixture-w", "fixture-t"),
                   ("0", "fixture-w", "fixture-t", "fixture-p"),
                   ("1", "fixture-w", "fixture-t", "fixture-p", "extra"))
        invalid += tuple(
            tuple(blank if index == missing else value
                  for index, value in enumerate(Context().env))
            for missing in range(4) for blank in ("", " ")
        )
        for identity in invalid:
            with self.subTest(identity=identity):
                self.assertEqual(caller_action(Context(env=identity, returned=identity)),
                                 "stop-unresolved")

    def test_recovery_requires_complete_live_resolved_target(self) -> None:
        recovery = Context(env=(), diagnostic_authorization=True,
                           visible_current_activity=True, returned_ownership=True)
        self.assertEqual(caller_action(recovery), "explicit-verified-ids")
        invalid = (replace(recovery, live=False), replace(recovery, returned=()),
                   replace(recovery, returned=("1", "fixture-w", "", "fixture-p")),
                   replace(recovery, returned=("0", "fixture-w", "fixture-t", "fixture-p")),
                   replace(recovery, repository_matches=False),
                   replace(recovery, thread_matches=False))
        for evidence in invalid:
            with self.subTest(evidence=evidence):
                self.assertEqual(caller_action(evidence), "diagnose-read-only")

    def test_unsupported_flag_does_not_silently_drop_isolation(self) -> None:
        old_cli = Context(supports_isolation=False)
        self.assertEqual(caller_action(old_cli), "stop-capability-gap")
        self.assertEqual(caller_action(replace(old_cli, proven_alternative=True)), "verify-worker-and-ack")
        self.assertIn("never silently omit", WORKFLOW)
        self.assertIn("version-specific evidence and authorization", WORKFLOW)

    def test_other_sessions_do_not_authorize_restart(self) -> None:
        self.assertEqual(restart_action({"owned"}, {"owned"}, False), "diagnose-only")
        self.assertEqual(restart_action({"owned", "other"}, {"owned"}, True), "diagnose-only")
        self.assertEqual(restart_action({"owned", "other"}, {"owned", "other"}, True),
                         "request-then-verify")
        self.assertIn("Before\nany shared daemon restart", WORKFLOW)
        self.assertIn("affected sessions, owners", WORKFLOW)
        self.assertIn("Existing sessions are not bulk-migrated", WORKFLOW)

    def test_shutdown_request_is_not_exit_environment_or_ack(self) -> None:
        for old_exited, corrected, ack in ((False, False, False), (True, False, False),
                                          (True, True, False), (False, True, True)):
            self.assertEqual(recovery_result(True, old_exited, corrected, ack), "request-only")
        self.assertEqual(recovery_result(True, True, True, True), "verified")
        self.assertIn("shutdown_requested", WORKFLOW)

    def test_missing_thread_failed_queue_and_post_bootstrap_receipts(self) -> None:
        scenarios = [
            (False, False, False, "idle", False, "record-gap-preflight-fallback"),
            (True, False, False, "done", False, "record-gap-preflight-fallback"),
            (True, False, False, "working", False, "pending-no-safe-fallback"),
            (False, False, False, "idle", True, "pending-no-safe-fallback"),
            (True, False, False, "blocked", False, "pending-no-safe-fallback"),
            (True, True, False, "idle", False, "pending-inspect-before-fallback"),
            (True, True, True, "done", False, "acknowledged"),
        ]
        for *inputs, expected in scenarios:
            with self.subTest(inputs=inputs):
                self.assertEqual(queue_result(*inputs), expected)
        self.assertIn("including after its first turn", COMMUNICATION)
        self.assertIn("reconcile the same event ID", COMMUNICATION)

    def test_generated_handoff_and_dispatch_share_boundary(self) -> None:
        for text in (WORKFLOW, PROMPT):
            for marker in ("--no-daemon", "native thread", "allowlisted", "read-only diagnosis"):
                self.assertIn(marker, text)
        self.assertIn("--timeout 60000 -- --no-daemon --model", WORKFLOW)
        self.assertIn("#codex-caller-identity-and-isolation", COMMUNICATION)
        project_dispatch = (ROOT / ".agents/memory/project/template-work-runs-on-codex.md").read_text()
        for marker in ("--no-daemon", "model_reasoning_effort", "model_provider",
                       "#codex-caller-identity-and-isolation"):
            self.assertIn(marker, project_dispatch)
        self.assertNotIn("--reasoning-effort", project_dispatch)


if __name__ == "__main__":
    unittest.main()
