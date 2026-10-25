"""Provider-free fixtures for the shared agent communication protocol."""
from __future__ import annotations

import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
SKILL = (REPOSITORY / ".agents/skills/shared/agent-communication/SKILL.md").read_text(encoding="utf-8")
PROMPT = (REPOSITORY / ".agents/scripts/new-agent-prompt.sh").read_text(encoding="utf-8")
WORKFLOW = (REPOSITORY / ".agents/skills/shared/issue-workflow/SKILL.md").read_text(encoding="utf-8")


def decision(agent: str, status: str, input_line: str, thread: str | None) -> tuple[str, str]:
    """Pure fixture model; no Herdr, provider or credential is called."""
    if input_line:
        return "stop", "draft-input"
    if status == "blocked":
        return "stop", "blocked"
    if agent == "codex" and status == "working" and thread:
        return "codex-queue", "resolved-working-thread"
    if status == "working":
        return "stop", "working-without-queue"
    if agent == "codex" and thread:
        return "codex-queue", "resolved-thread"
    return "herdr-agent-prompt", "fallback-no-codex-thread" if agent == "codex" else "native-herdr"


class AgentCommunicationFixtures(unittest.TestCase):
    def test_empty_draft_idle_working_and_blocked_boundaries(self) -> None:
        self.assertEqual(decision("claude", "idle", "", None), ("herdr-agent-prompt", "native-herdr"))
        self.assertEqual(decision("claude", "idle", "draft", None), ("stop", "draft-input"))
        self.assertEqual(decision("claude", "blocked", "", None), ("stop", "blocked"))
        self.assertEqual(decision("claude", "working", "", None), ("stop", "working-without-queue"))

    def test_codex_queue_shape_and_fallback(self) -> None:
        self.assertEqual(decision("codex", "working", "", "thread-123")[0], "codex-queue")
        self.assertEqual(decision("codex", "idle", "", None), ("herdr-agent-prompt", "fallback-no-codex-thread"))
        self.assertRegex(SKILL, r"codex queue --thread <THREAD> --message <TEXT>")
        self.assertIn("--thread", SKILL)
        self.assertIn("--message", SKILL)

    def test_stalled_send_requires_inspection_and_persistence(self) -> None:
        self.assertIn("do not resend blindly", SKILL)
        self.assertIn("herdr agent get", SKILL)
        self.assertIn("herdr agent read <TARGET> --source visible", SKILL)
        self.assertIn("persist the exact failure", SKILL)

    def test_all_agents_have_transport_and_confirmation_rules(self) -> None:
        for agent in ("Codex", "Claude Code", "Pi"):
            with self.subTest(agent=agent):
                self.assertIn(agent, SKILL)
        self.assertIn("Confirmation means", SKILL)
        self.assertIn("transport", SKILL)
        self.assertIn("target", SKILL)
        self.assertIn("status-before", SKILL)
        self.assertIn("status-after", SKILL)

    def test_handoff_and_workflow_link_the_same_protocol(self) -> None:
        self.assertIn("agent-communication/SKILL.md", PROMPT)
        self.assertIn("transport, target session/thread and confirmation result", PROMPT)
        self.assertIn("agent-communication", WORKFLOW)
        self.assertIn("Do not blind-retry a stall", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
