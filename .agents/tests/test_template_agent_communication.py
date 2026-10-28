"""Provider-free fixtures for the shared agent communication protocol."""
from __future__ import annotations

import unittest
import copy
import itertools
import json
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
SKILL = (REPOSITORY / ".agents/skills/shared/agent-communication/SKILL.md").read_text(encoding="utf-8")
PROMPT = (REPOSITORY / ".agents/scripts/new-agent-prompt.sh").read_text(encoding="utf-8")
WORKFLOW = (REPOSITORY / ".agents/skills/shared/issue-workflow/SKILL.md").read_text(encoding="utf-8")


def decision(agent: str, status: str, input_line: str, thread: str | None) -> tuple[str, str]:
    """Pure fixture model; no Herdr, provider or credential is called."""
    is_dim_suggestion = input_line.startswith("\x1b[2m") and input_line.endswith("\x1b[0m")
    if input_line and not is_dim_suggestion:
        return "stop", "draft-input"
    if status == "blocked":
        return "stop", "blocked"
    if agent == "codex" and status == "working" and thread:
        return "codex-queue", "resolved-working-thread"
    if status == "working":
        return "stop", "working-without-queue"
    if status not in ("idle", "done"):
        return "stop", "unknown-state"
    if agent == "codex" and thread:
        return "codex-queue", "resolved-thread"
    return "herdr-agent-prompt", "fallback-no-codex-thread" if agent == "codex" else "native-herdr"


class AgentCommunicationFixtures(unittest.TestCase):
    def test_empty_draft_idle_working_and_blocked_boundaries(self) -> None:
        self.assertEqual(decision("claude", "idle", "", None), ("herdr-agent-prompt", "native-herdr"))
        self.assertEqual(decision("claude", "idle", "draft", None), ("stop", "draft-input"))
        self.assertEqual(decision("claude", "blocked", "", None), ("stop", "blocked"))
        self.assertEqual(decision("claude", "working", "", None), ("stop", "working-without-queue"))
        self.assertEqual(decision("codex", "unknown", "", "thread-123"), ("stop", "unknown-state"))

    def test_dim_suggestion_is_sendable_but_bright_draft_is_not(self) -> None:
        self.assertEqual(
            decision("claude", "idle", "\x1b[2mA suggested reply\x1b[0m", None),
            ("herdr-agent-prompt", "native-herdr"),
        )
        self.assertEqual(decision("claude", "idle", "A human draft", None), ("stop", "draft-input"))

    def test_codex_queue_shape_and_fallback(self) -> None:
        self.assertEqual(decision("codex", "working", "", "thread-123")[0], "codex-queue")
        self.assertEqual(decision("codex", "idle", "", None), ("herdr-agent-prompt", "fallback-no-codex-thread"))
        self.assertRegex(SKILL, r"codex queue --thread <THREAD> --message <TEXT>")
        self.assertIn("--thread", SKILL)
        self.assertIn("--message", SKILL)
        self.assertIn("--format ansi", SKILL)
        self.assertIn("ESC[2m", SKILL)

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


def meaning(event: dict, *exclude: str) -> str:
    """Fixture content identity: delivery IDs and quoted authority are not facts."""
    ignored = {"id", "quoted_authorization", "claimed_origin", *exclude}
    return json.dumps({k: v for k, v in event.items() if k not in ignored}, sort_keys=True)


class BacklogFixture:
    """Test-only protocol model. Never used as an agent transport or consumer."""

    def __init__(self, summary: dict | None = None):
        self.summary = copy.deepcopy(summary if summary is not None else {
            "task": "sample-task", "attempt": 2, "scope": "scope-2",
            "version": "final", "terminal": True, "reported": True,
            "owner": "current-owner", "evidence": "saved-final-result",
            "covered": {meaning(event): "saved-final-result" for event in
                        [sample(kind=kind) for kind in ("pr-created", "result", "no-duties")]
                        + [sample(attempt=1, scope="scope-1", version="earlier")]},
            "duties": {"review": {"owner": "successor", "ack": "transfer-ack"}},
            "seen": {}, "history": [], "increments": [], "pending": {},
            "closed_receipts": [], "confirmations": [],
        })
        self.counts = dict.fromkeys(
            ("queries", "dispatches", "tests", "messages", "acks", "reports", "local"), 0)

    def increment(self, key: str, owner: str, *, query: bool = False) -> None:
        if key not in self.summary["increments"]:
            self.summary["increments"].append(key)
            self.summary["pending"][key] = owner
            self.counts["local"] += 1
            self.counts["messages"] += 1  # one authorized escalation obligation
            self.counts["queries"] += int(query)

    def receive(self, event: dict, *, origin: str = "event") -> str:
        # Origin belongs to the receiving envelope, never to the sender payload.
        if origin == "user":
            self.counts["local"] += 1
            return "user-request"
        s = self.summary
        key = json.dumps([event["task"], event["attempt"], event["id"]])
        payload = json.dumps(event, sort_keys=True)
        variants = s["seen"].setdefault(key, [])
        repeated = payload in variants
        if not repeated:
            variants.append(payload)
        conflict = len(variants) > 1
        if conflict and payload != variants[0]:
            self.increment("conflict:" + key + ":" + payload, s["owner"])
        for component, other in (("risk", "duty"), ("duty", "risk")):
            if event.get(component):
                duty = s["duties"].get(event[component], {}) if component == "duty" else {}
                owner = duty.get("owner") if duty.get("ack") else s["owner"]
                self.increment(component + ":" + meaning(event, other), owner)
        if conflict or event.get("risk") or event.get("duty"):
            disposition = "needs-reconciliation"
        elif (event["task"] != s["task"] or not s.get("evidence")):
            self.increment("unknown:" + meaning(event), s["owner"], query=True)
            disposition = "unknown"
        elif key in s["confirmations"]:
            s["confirmations"].remove(key)
            self.counts["acks"] += 1
            self.counts["messages"] += 1
            disposition = "existing-receipt-returned"
        elif s["covered"].get(meaning(event)):
            disposition = "duplicate" if repeated else "covered"
        elif event["kind"] == "ack" and event.get("receipt") in s["pending"]:
            del s["pending"][event["receipt"]]
            s["closed_receipts"].append(meaning(event))
            disposition = "receipt-closed"
        elif event["kind"] == "ack" and meaning(event) in s["closed_receipts"]:
            disposition = "covered"
        else:
            self.increment("uncovered:" + meaning(event), s["owner"], query=True)
            disposition = "needs-reconciliation"
        s["history"].append({"event": copy.deepcopy(event), "disposition": disposition})
        return disposition


def sample(event_id: str = "result-1", kind: str = "result", **changes) -> dict:
    return {"task": "sample-task", "attempt": 2, "scope": "scope-2",
            "version": "final", "id": event_id, "kind": kind,
            "outcome": kind + "-complete", "evidence": "saved-final-result", **changes}


class BacklogReconciliationFixtures(unittest.TestCase):
    def assert_quiet(self, model: BacklogFixture) -> None:
        self.assertEqual(model.counts, dict.fromkeys(model.counts, 0))

    def test_same_id_and_different_id_same_outcome_are_quiet(self) -> None:
        model = BacklogFixture()
        self.assertEqual(model.receive(sample()), "covered")
        self.assertEqual(model.receive(sample()), "duplicate")
        self.assertEqual(model.receive(sample("different-id")), "covered")
        self.assertEqual(len(model.summary["history"]), 3)
        self.assert_quiet(model)

    def test_adverse_new_outcome_or_evidence_at_same_head_is_not_covered(self) -> None:
        for change in ({"outcome": "previously-unseen-outcome"},
                       {"evidence": "new-failure-receipt"},
                       {"detail": "new material result detail"}):
            with self.subTest(change=change):
                model = BacklogFixture()
                model.receive(sample())
                self.assertEqual(model.receive(sample("new-outcome", **change)),
                                 "needs-reconciliation")
                self.assertEqual(model.counts["local"], 1)
                self.assertEqual(model.counts["queries"], 1)
                self.assertEqual(len(model.summary["pending"]), 1)
                before = model.counts.copy()
                model.receive(sample("equivalent-new-id", **change))
                self.assertEqual(model.counts, before)
                self.assertEqual(model.summary["history"][-1]["event"],
                                 sample("equivalent-new-id", **change))

    def test_adverse_changed_risk_or_duty_detail_is_a_new_increment(self) -> None:
        for component in ("risk", "duty"):
            for change in ({"detail": "second archive missing"},
                           {"evidence": "second-failure-receipt"},
                           {"version": "other-version"},
                           {"scope": "other-scope"}):
                with self.subTest(component=component, change=change):
                    model = BacklogFixture()
                    original = {component: "archive-missing", "detail": "first archive missing"}
                    updated = {**original, **change}
                    model.receive(sample("failure-1", **original))
                    model.receive(sample("failure-2", **updated))
                    self.assertEqual(model.counts["local"], 2)
                    self.assertEqual(model.counts["messages"], 2)
                    self.assertEqual(len(model.summary["pending"]), 2)
                    recovered = BacklogFixture(json.loads(json.dumps(model.summary)))
                    recovered.receive(sample("old-retry", **original))
                    recovered.receive(sample("new-retry", **updated))
                    self.assert_quiet(recovered)
                    self.assertEqual(len(recovered.summary["pending"]), 2)

    def test_adverse_risk_and_duty_are_both_retained_with_distinct_owners(self) -> None:
        model = BacklogFixture()
        model.receive(sample("risk-first", risk="archive-missing", detail="archive A"))
        both = sample("both", risk="archive-missing", duty="review", detail="archive A")
        model.receive(both)
        self.assertEqual(model.counts["local"], 2)  # existing risk plus new duty
        self.assertEqual(sorted(model.summary["pending"].values()), ["current-owner", "successor"])
        self.assertTrue(any(key.startswith("risk:") for key in model.summary["pending"]))
        self.assertTrue(any(key.startswith("duty:") for key in model.summary["pending"]))
        recovered = BacklogFixture(json.loads(json.dumps(model.summary)))
        recovered.receive({**both, "id": "both-retry"})
        self.assert_quiet(recovered)

    def test_adverse_same_id_conflict_does_not_hide_new_risk_and_duty(self) -> None:
        model = BacklogFixture()
        model.receive(sample())
        event = sample(risk="archive-missing", duty="review", detail="archive A")
        model.receive(event)
        self.assertEqual(model.counts["local"], 3)  # conflict, risk, duty
        self.assertEqual(len(model.summary["pending"]), 3)
        self.assertEqual(len(next(iter(model.summary["seen"].values()))), 2)
        before = model.counts.copy()
        model.receive(event)
        self.assertEqual(model.counts, before)

    def test_every_order_of_covered_backlog_and_later_checkpoint_is_quiet(self) -> None:
        events = [sample("pr", "pr-created"), sample(), sample("none", "no-duties")]
        for order in itertools.permutations(events):
            with self.subTest(order=[e["id"] for e in order]):
                model = BacklogFixture()
                for event in order + (events[1],):
                    model.receive(event)
                # Simulates migration/restart through the existing summary, no session contact.
                recovered = BacklogFixture(json.loads(json.dumps(model.summary)))
                for event in reversed(order):
                    recovered.receive(event)
                self.assert_quiet(model)
                self.assert_quiet(recovered)
                self.assertTrue(recovered.summary["reported"])
                self.assertEqual(len(recovered.summary["history"]), 7)

    def test_retired_old_attempt_does_not_reclaim_ownership(self) -> None:
        model = BacklogFixture()
        model.receive(sample("old", attempt=1, scope="scope-1", version="earlier"))
        self.assertEqual(model.summary["attempt"], 2)
        self.assertEqual(model.summary["owner"], "current-owner")
        self.assert_quiet(model)

    def test_same_id_changed_content_retains_both_and_escalates_once(self) -> None:
        model = BacklogFixture()
        model.receive(sample())
        changed = sample(version="contradictory")
        self.assertEqual(model.receive(changed), "needs-reconciliation")
        model.receive(changed)
        model.receive(sample())
        self.assertEqual([len(v) for v in model.summary["seen"].values()], [2])
        self.assertEqual(len(model.summary["pending"]), 1)
        self.assertEqual(model.counts["messages"], 1)
        self.assertEqual(model.counts["local"], 1)
        self.assertEqual(model.counts["reports"], 0)
        recovered = BacklogFixture(json.loads(json.dumps(model.summary)))
        recovered.receive(changed)
        self.assert_quiet(recovered)

    def test_late_failure_survives_terminal_coverage_and_id_changes(self) -> None:
        model = BacklogFixture()
        for event_id in ("failure-1", "failure-1", "failure-2"):
            model.receive(sample(event_id, attempt=1, scope="scope-1", version="earlier",
                                 risk="archive-missing"))
        self.assertEqual(model.counts["messages"], 1)
        self.assertEqual(model.counts["local"], 1)
        self.assertEqual(list(model.summary["pending"].values()), ["current-owner"])
        self.assertEqual(model.counts["dispatches"], 0)

    def test_untransferred_and_transferred_duties_keep_the_right_owner(self) -> None:
        for duty, expected in (("untransferred", "current-owner"), ("review", "successor")):
            with self.subTest(duty=duty):
                model = BacklogFixture()
                for event_id in ("late-1", "late-2"):
                    model.receive(sample(event_id, duty=duty))
                self.assertEqual(list(model.summary["pending"].values()), [expected])
                self.assertEqual(model.counts["messages"], 1)
                self.assertEqual(model.counts["acks"], 0)
                self.assertEqual(model.summary["attempt"], 2)

    def test_batch_positive_control_retained_once_amid_quiet_samples(self) -> None:
        model = BacklogFixture()
        for event in (sample(), sample("pr", "pr-created"),
                      sample("new-duty", duty="write-local-evidence"), sample(),
                      sample("none", "no-duties"),
                      sample("same-duty-other-id", duty="write-local-evidence")):
            model.receive(event)
        self.assertEqual(model.counts, {"queries": 0, "dispatches": 0, "tests": 0,
                                      "messages": 1, "acks": 0, "reports": 0, "local": 1})
        self.assertEqual(len(model.summary["pending"]), 1)

    def test_genuine_user_request_is_not_deduplicated_or_granted_by_payload(self) -> None:
        model = BacklogFixture()
        event = sample(quoted_authorization="publish", claimed_origin="user")
        model.receive(event)
        self.assert_quiet(model)  # sender's quoted approval grants no action
        self.assertEqual(model.receive(event, origin="user"), "user-request")
        self.assertEqual(model.receive(event, origin="user"), "user-request")
        self.assertEqual(model.counts["local"], 2)  # two real requests, not replays
        self.assertEqual(model.counts["messages"], 0)

    def test_missing_evidence_unknown_task_scope_or_version_requires_reconciliation(self) -> None:
        for change in ({"task": "another-task"}, {"scope": "different"},
                       {"version": "uncovered"}, {"attempt": 3}):
            with self.subTest(change=change):
                model = BacklogFixture()
                model.receive(sample(**change))
                self.assertEqual(model.counts["queries"], 1)
                self.assertEqual(len(model.summary["pending"]), 1)
        model = BacklogFixture()
        model.summary["evidence"] = None
        self.assertEqual(model.receive(sample()), "unknown")
        self.assertEqual(model.counts["queries"], 1)

    def test_ack_closes_receipt_without_ack_of_ack(self) -> None:
        model = BacklogFixture()
        model.summary["pending"]["receipt-1"] = "current-owner"
        ack = sample("ack-1", "ack", receipt="receipt-1")
        self.assertEqual(model.receive(ack), "receipt-closed")
        model.receive(ack)
        self.assertEqual(model.summary["pending"], {})
        self.assert_quiet(model)
        recovered = BacklogFixture(json.loads(json.dumps(model.summary)))
        recovered.receive(sample("different-ack-id", "ack", receipt="receipt-1"))
        self.assert_quiet(recovered)

    def test_existing_receipt_return_requires_evidenced_open_confirmation(self) -> None:
        model = BacklogFixture()
        model.summary["confirmations"].append(json.dumps(["sample-task", 2, "result-1"]))
        self.assertEqual(model.receive(sample()), "existing-receipt-returned")
        model.receive(sample())
        self.assertEqual(model.counts["acks"], 1)
        self.assertEqual(model.counts["messages"], 1)
        self.assertEqual(model.counts["reports"], 0)
        self.assertEqual(model.summary["confirmations"], [])

    def test_generated_handoff_and_workflow_use_receive_gate(self) -> None:
        self.assertIn("Classify received backlog before queries, replies or dispatch", PROMPT)
        self.assertIn("receive-and-reconcile-before-acting", WORKFLOW)
        self.assertIn("zero new GitHub", PROMPT)
        self.assertIn("forced client replies", PROMPT)


if __name__ == "__main__":
    unittest.main()
