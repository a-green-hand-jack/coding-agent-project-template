"""Provider-free fixtures for hook, delivery-gate and Herdr close-out rules."""
from __future__ import annotations

import unittest
import hashlib
import json
import locale
import os
import subprocess
import sys
import tempfile
from unittest.mock import patch
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
    def test_fake_guard_records_even_when_product_catches_exception(self):
        attempts = []
        def guard(command):
            attempts.append(command)
            raise RuntimeError('unexpected boundary')
        def product():
            try:
                subprocess.run(['unexpected'])
            except RuntimeError:
                pass
        fake_calls = []
        with patch('subprocess.run', side_effect=lambda command: fake_calls.append(command)):
            product()
        self.assertEqual(fake_calls, [['unexpected']])
        with patch('subprocess.run', side_effect=guard):
            product()
        self.assertEqual(attempts, [['unexpected']])
        # An explicitly selected harmless real subprocess is a separate path.
        self.assertEqual(subprocess.run([sys.executable, '-c', 'pass']).returncode, 0)

    def test_canonical_manifest_is_order_and_locale_independent(self):
        def manifest(root, paths):
            rows=[]
            for name in paths:
                path=root/name
                if path.is_symlink():
                    rows.append({'path':name,'type':'symlink','target':os.readlink(path)})
                else:
                    rows.append({'path':name,'type':'file','executable':bool(path.stat().st_mode & 0o111),
                                 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
            rows.sort(key=lambda row: row['path'].encode('utf-8'))
            return json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(',',':')).encode('utf-8')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            names=['space name','line\nbreak','é.txt']
            for name in names:(root/name).write_text(name,encoding='utf-8')
            (root/'link').symlink_to('é.txt');names.append('link')
            previous=locale.setlocale(locale.LC_COLLATE)
            try:
                locale.setlocale(locale.LC_COLLATE, 'C'); first=manifest(root,names)
                for candidate in ('en_US.UTF-8', 'C.UTF-8', 'UTF-8'):
                    try:
                        locale.setlocale(locale.LC_COLLATE, candidate)
                        break
                    except locale.Error:
                        continue
                else:
                    self.skipTest('no second UTF-8 locale available')
                second=manifest(root,list(reversed(names)))
            finally:
                locale.setlocale(locale.LC_COLLATE, previous)
            self.assertEqual(first,second)
            (root/'space name').write_text('changed')
            self.assertNotEqual(first,manifest(root,names))
            self.assertNotEqual(first,manifest(root,names[:-1]))
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
