"""Dispatch records: three fixtures that cover the mechanical, routine and hard
tiers and the Pi, Claude Code and Codex agent kinds, checked against the record
shape issue-workflow documents. They are data in this file; no agent is started
and no provider is called."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
SKILL = (REPOSITORY / ".agents/skills/shared/issue-workflow/SKILL.md").read_text(encoding="utf-8")
TIERS = ("mechanical", "routine", "hard", "hardest")

FIXTURES = (
    {
        "tier": "mechanical",
        "kind": "pi",
        "text": """## Dispatch

- coordinator: `tpl-coord-1`
- agent: Pi coding agent
- provider: `cheap-relay`
- model: `deepseek-v4.1-flash-1017`; effort: `low`
- reason: mechanical: sync two indexes and a skill note; no design
- session: `tpl-issue-120`, branch `docs/issue-120-indexes`
""",
    },
    {
        "tier": "routine",
        "kind": "claude",
        "text": """## Dispatch

- coordinator: `tpl-coord-2`
- agent: Claude Code
- provider: `anthropic`
- model: `sonnet`; effort: `high`
- reason: routine: several files inside the existing design, acceptance already clear
- session: `tpl-issue-121`, branch `fix/issue-121-worktree-hook`
""",
    },
    {
        "tier": "hard",
        "kind": "codex",
        "text": """## Dispatch

- coordinator: `tpl-coord-3`
- agent: Codex
- provider: `openai`
- model: `gpt-5`; effort: `xhigh`
- reason: hard: process and container lifecycle across worktrees, real runs needed
- session: `tpl-issue-122`, branch `feat/issue-122-close-out`
- re-dispatched: `pi`, `cheap-relay`, `deepseek-v4.1-flash-1017`, `medium` → `codex`, `openai`, `gpt-5`, `xhigh`: the Issue needs isolation and container checks, not text edits
""",
    },
)
AGENT_FAMILIES = {
    "pi": ("deepseek",),
    "claude": ("claude", "sonnet", "haiku", "opus"),
    "codex": ("gpt", "o1", "o3", "o4"),
}


def quoted(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text)
    return match.group(1) if match else None


def parse(text: str) -> dict[str, object]:
    """The values issue-workflow's Dispatch section must carry, plus the
    re-dispatch history lines, from one record. Model and effort may share a
    line as the skill shows, or stand on their own as an older record does."""
    fields: dict[str, str] = {}
    history = []
    for line in text.splitlines():
        if line.startswith("- re-dispatched: "):
            history.append(line)
            continue
        match = re.match(r"- ([a-z][a-z-]*): (.*)$", line)
        if match:
            fields.setdefault(match.group(1), match.group(2))
    model_line = fields.get("model", "")
    return {
        "fields": fields,
        "provider": quoted(r"`([^`]+)`", fields.get("provider", "")),
        "model": quoted(r"`([^`]+)`", model_line),
        "effort": quoted(r"`([^`]+)`", fields.get("effort", ""))
                  or quoted(r"effort: `([^`]+)`", model_line),
        "history": history,
    }


class DispatchRecords(unittest.TestCase):
    def test_three_fixtures_cover_the_tiers_and_agent_kinds(self) -> None:
        tiers = {fixture["tier"] for fixture in FIXTURES}
        kinds = {fixture["kind"] for fixture in FIXTURES}
        self.assertEqual(tiers, {"mechanical", "routine", "hard"})
        self.assertEqual(kinds, {"pi", "claude", "codex"})

    def test_each_fixture_has_the_documented_fields(self) -> None:
        for fixture in FIXTURES:
            with self.subTest(tier=fixture["tier"]):
                record = parse(fixture["text"])
                for field in ("coordinator", "agent", "reason", "session"):
                    self.assertTrue(record["fields"].get(field), f"missing {field}")
                # Provider, model and effort are always explicit, never a default.
                self.assertTrue(record["provider"])
                self.assertTrue(record["model"])
                self.assertIn(record["effort"], ("low", "medium", "high", "xhigh", "max"))

    def test_the_reason_starts_with_the_tier(self) -> None:
        for fixture in FIXTURES:
            with self.subTest(tier=fixture["tier"]):
                reason = parse(fixture["text"])["fields"]["reason"]
                tier, _, why = reason.partition(": ")
                self.assertIn(tier, TIERS)
                self.assertEqual(tier, fixture["tier"])
                self.assertTrue(why)

    def test_the_agent_runs_only_its_own_model_family(self) -> None:
        for fixture in FIXTURES:
            with self.subTest(tier=fixture["tier"]):
                model = parse(fixture["text"])["model"].lower()
                family = AGENT_FAMILIES[fixture["kind"]]
                self.assertTrue(model.startswith(family), f"{model} is not {fixture['kind']}'s family")

    def test_a_re_dispatch_keeps_the_previous_values(self) -> None:
        record = parse(FIXTURES[-1]["text"])
        (line,) = record["history"]
        previous, _, rest = line.partition(" → ")
        self.assertIn("`pi`", previous)
        self.assertIn("`deepseek-v4.1-flash-1017`", previous)
        self.assertIn("`codex`", rest)
        self.assertIn(": ", rest)

    def test_an_older_record_with_separate_lines_still_parses(self) -> None:
        record = parse("""## Dispatch

- coordinator: `tpl-coord-4`
- agent: Pi coding agent
- provider: `cheap-relay`
- model: `deepseek-v4.1-flash-1017`
- effort: `high`
- reason: hard: cross-file routing and worktree lifecycle
- session: `tpl-issue-123`, branch `feat/issue-123-x`
""")
        self.assertEqual(record["provider"], "cheap-relay")
        self.assertEqual(record["model"], "deepseek-v4.1-flash-1017")
        self.assertEqual(record["effort"], "high")

    def test_the_skill_documents_this_shape(self) -> None:
        section = SKILL.split("### Agent, provider, model and effort", 1)[1]
        example = re.search(r"```markdown\n## Dispatch\n(.*?)```", section, re.S)
        self.assertIsNotNone(example, "issue-workflow has no Dispatch record example")
        text = example.group(1)
        lines = {line.split(":", 1)[0].lstrip("- "): line.split(":", 1)[1].strip()
                 for line in text.splitlines() if line.startswith("- ")}
        for field in ("coordinator", "agent", "provider", "model", "reason", "session"):
            self.assertIn(field, lines, f"the Dispatch example lacks {field}")
        self.assertIn("effort:", lines["model"], "the model line no longer carries the effort")
        self.assertIn("- re-dispatched: <previous agent, provider, model, effort>",
                      section, "the re-dispatch line no longer keeps provider and model")
        self.assertIn("<MODEL_SELECTION>", section, "the skill no longer resolves a series at dispatch time")


if __name__ == "__main__":
    unittest.main()
