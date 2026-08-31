"""Boundary tests for the skill-budget checks in scripts/validate.py.

Stdlib only, like the validator. Each test builds a throwaway skills/ tree so the
thresholds are exercised at their exact edges — the failures they guard against are silent.
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

VALIDATE = Path(__file__).resolve().parents[1] / "scripts" / "validate.py"
spec = importlib.util.spec_from_file_location("validate", VALIDATE)
validate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validate)

BYTES = validate.CODEX_SKILL_PROMPT_BYTES
CHARS = validate.CODEX_DESCRIPTION_CHARS


def skill_text(description: str, total_bytes: int, name: str = "demo") -> str:
    """A SKILL.md whose UTF-8 size is exactly `total_bytes`, padded with ASCII body text."""
    head = f"---\nname: {name}\ndescription: {description}\n---\n"
    pad = total_bytes - len(head.encode())
    assert pad >= 0, "frontmatter alone exceeds the requested size"
    return head + "x" * pad


class BudgetCase(unittest.TestCase):
    def check(self, text: str, enforce: bool = True) -> tuple[list[str], list[str]]:
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "demo"
            skill.mkdir()
            (skill / "SKILL.md").write_text(text, encoding="utf-8")
            errors: list[str] = []
            warnings: list[str] = []
            validate.validate_skill_budgets(
                errors, warnings, skills_dir=Path(tmp), enforce_bytes=enforce
            )
            return errors, warnings

    def test_exact_prompt_budget_passes(self):
        errors, warnings = self.check(skill_text("d", BYTES))
        self.assertEqual(errors, [])
        self.assertTrue(any("within" in w for w in warnings))  # inside the headroom band

    def test_one_byte_over_fails(self):
        errors, _ = self.check(skill_text("d", BYTES + 1))
        self.assertEqual(len(errors), 1)
        self.assertIn(f"{BYTES + 1} bytes", errors[0])

    def test_multibyte_counted_as_bytes_not_chars(self):
        text = skill_text("d", BYTES - 6) + "é" * 4  # 4 chars, 8 bytes → 8002 bytes
        self.assertLess(len(text), BYTES)
        self.assertGreater(len(text.encode()), BYTES)
        errors, _ = self.check(text)
        self.assertEqual(len(errors), 1)

    def test_frontmatter_counts_toward_prompt_budget(self):
        # Body alone fits; body + frontmatter does not. Codex truncates the raw file.
        long_desc = "d" * 500
        text = skill_text(long_desc, BYTES + 1)
        body_bytes = len(text.split("---\n", 2)[2].encode())
        self.assertLess(body_bytes, BYTES)
        errors, _ = self.check(text)
        self.assertEqual(len(errors), 1)

    def test_size_is_warning_while_not_enforced(self):
        errors, warnings = self.check(skill_text("d", BYTES + 1), enforce=False)
        self.assertEqual(errors, [])
        self.assertTrue(any("truncates" in w for w in warnings))

    def test_below_headroom_is_silent(self):
        errors, warnings = self.check(skill_text("d", int(BYTES * 0.9) - 1))
        self.assertEqual((errors, warnings), ([], []))

    def test_description_at_cap_passes_over_cap_fails(self):
        errors, _ = self.check(skill_text("d" * CHARS, BYTES))
        self.assertEqual(errors, [])
        errors, _ = self.check(skill_text("d" * (CHARS + 1), BYTES))
        self.assertEqual(len(errors), 1)
        self.assertIn(f"{CHARS + 1} chars", errors[0])

    def test_description_near_cap_warns_without_failing(self):
        errors, warnings = self.check(skill_text("d" * (CHARS - 10), 4000))
        self.assertEqual(errors, [])
        self.assertTrue(any("catalog cap" in w for w in warnings))


class FrontmatterCase(unittest.TestCase):
    def parse(self, frontmatter: str) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text(f"---\n{frontmatter}\n---\nbody\n", encoding="utf-8")
            data, err = validate.parse_frontmatter(path)
            self.assertIsNotNone(data, err)
            return data

    def test_folded_block_scalar_is_joined_and_measured_whole(self):
        data = self.parse("name: demo\ndescription: >\n  first line\n  second line")
        self.assertEqual(data["description"], "first line second line")

    def test_literal_block_scalar_keeps_newlines(self):
        data = self.parse("name: demo\ndescription: |\n  a\n  b")
        self.assertEqual(data["description"], "a\nb")

    def test_plain_continuation_lines(self):
        data = self.parse("name: demo\ndescription: starts here\n  and continues")
        self.assertEqual(data["description"], "starts here and continues")

    def test_quoted_scalar_is_unquoted(self):
        data = self.parse('name: demo\ndescription: "quoted: with colon"')
        self.assertEqual(data["description"], "quoted: with colon")


if __name__ == "__main__":
    unittest.main()
