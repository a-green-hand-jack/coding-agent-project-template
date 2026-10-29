"""Provider-free fixtures for hook, delivery-gate and Herdr close-out rules."""
from __future__ import annotations

import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[3]
WORKFLOW = (REPOSITORY / ".agents/skills/shared/issue-workflow/SKILL.md").read_text(encoding="utf-8")
LIFECYCLE = (REPOSITORY / ".agents/skills/shared/worktree-lifecycle/SKILL.md").read_text(encoding="utf-8")
PROMPT = (REPOSITORY / ".agents/scripts/shared/new-agent-prompt.sh").read_text(encoding="utf-8")


def hook_decision(*, source_known: bool, necessary: bool, inspectable: bool) -> str:
    """Pure review fixture; it never invokes Herdr or a provider."""
    if not inspectable or not source_known or not necessary:
        return "stop-maintainer"
    return "approve"


class GovernanceProtocol(unittest.TestCase):
    def test_hook_review_is_per_hook_and_unknown_hooks_stop(self) -> None:
        self.assertEqual(hook_decision(source_known=True, necessary=True, inspectable=True), "approve")
        self.assertEqual(hook_decision(source_known=False, necessary=True, inspectable=True), "stop-maintainer")
        self.assertEqual(hook_decision(source_known=True, necessary=False, inspectable=True), "stop-maintainer")
        self.assertEqual(hook_decision(source_known=True, necessary=True, inspectable=False), "stop-maintainer")
        for text in (WORKFLOW, PROMPT):
            self.assertIn("SessionStart", text)
            self.assertIn("blanket", text)
            self.assertIn(".project/state/", text)
        self.assertIn("unknown", WORKFLOW)
        self.assertIn("inspection command/output", WORKFLOW)

    def test_implementation_and_delivery_are_distinct(self) -> None:
        self.assertIn("Separate implementation from delivery", WORKFLOW)
        for evidence in ("named commit", "pushed", "remote head", "PR targets", "review approval", "close-out"):
            self.assertIn(evidence, WORKFLOW)
        self.assertIn("PR readiness gate", WORKFLOW)
        self.assertIn("stale check", WORKFLOW)

    def test_closed_workspace_recovery_keeps_herdr_as_the_manager(self) -> None:
        self.assertIn("empty `open_workspace_id`", LIFECYCLE)
        self.assertIn("herdr worktree open", LIFECYCLE)
        self.assertIn("herdr worktree remove --workspace <reopened-workspace>", LIFECYCLE)
        self.assertIn("git worktree prune", LIFECYCLE)
        self.assertIn("no unique copy remains", LIFECYCLE)
        self.assertIn("stop and preserve the exact Herdr/Git output", LIFECYCLE)


if __name__ == "__main__":
    unittest.main()
