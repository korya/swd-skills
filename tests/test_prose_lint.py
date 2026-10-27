"""Rule-by-rule tests for scripts/prose-lint.py.

Stdlib only, like the linter. Each test feeds a small Markdown fragment and asserts which
rules fire, so a change to the Markdown handling cannot silently mute a rule.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

LINT = Path(__file__).resolve().parents[1] / "scripts" / "prose-lint.py"
spec = importlib.util.spec_from_file_location("prose_lint", LINT)
prose_lint = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(prose_lint)


def words(n: int) -> str:
    return " ".join(f"w{i}" for i in range(n))


def rules(text: str) -> list[str]:
    return [f["rule"] for f in prose_lint.lint(text, "t.md")]


class SentenceRules(unittest.TestCase):
    def test_clean_text_passes(self):
        self.assertEqual(rules("Short claim. Then a detail.\n\nAnother paragraph."), [])

    def test_long_sentence_fires_past_cap(self):
        text = f"Lead here. {words(prose_lint.MAX_SENTENCE + 1)}."
        self.assertEqual(rules(text), ["long-sentence"])

    def test_sentence_at_cap_passes(self):
        text = f"Lead here. {words(prose_lint.MAX_SENTENCE)}."
        self.assertEqual(rules(text), [])

    def test_long_lead_fires_on_first_sentence_only(self):
        text = f"{words(prose_lint.MAX_LEAD + 1)}. Short detail."
        self.assertEqual(rules(text), ["long-lead"])

    def test_lead_between_caps_is_lead_not_sentence(self):
        text = f"{words(prose_lint.MAX_SENTENCE)}. Detail."
        self.assertEqual(rules(text), ["long-lead"])

    def test_wrapped_sentence_counts_once(self):
        text = "This sentence wraps across\nthree source lines but is\nstill one sentence."
        self.assertEqual(rules(text), [])

    def test_long_paragraph(self):
        text = " ".join("Short one." for _ in range(prose_lint.MAX_PARAGRAPH + 1))
        self.assertEqual(rules(text), ["long-paragraph"])

    def test_abbreviation_does_not_end_sentence(self):
        text = f"Use git vs. {words(prose_lint.MAX_LEAD - 3)} fine."
        self.assertEqual(rules(text), ["long-lead"])  # one sentence, not two short ones


class TeaserLead(unittest.TestCase):
    def test_count_of_unnamed_things_is_flagged(self):
        for lead in ("Two things went wrong.", "Two designs caused this.",
                     "Two principles drive the design.", "Several factors compound here."):
            self.assertEqual(rules(lead + " Detail follows."), ["teaser-lead"], lead)

    def test_claim_with_a_count_passes(self):
        self.assertEqual(rules("Three staging tenants burst 100 sends per second. Detail."), [])
        self.assertEqual(rules("Two retries at one second apart were not enough. Detail."), [])

    def test_only_the_lead_is_checked(self):
        self.assertEqual(rules("The sender lost messages. Two things went wrong."), [])


class PunctuationRules(unittest.TestCase):
    def test_semicolon(self):
        self.assertEqual(rules("One clause; another."), ["semicolon"])

    def test_em_dash_and_spaced_double_hyphen(self):
        self.assertEqual(rules("A thing — another.\n\nA thing -- another."), ["dash", "dash"])

    def test_spaced_en_dash_only(self):
        self.assertEqual(rules("Pages 3–4 are fine.\n\nBut this – is not."), ["dash"])

    def test_hyphen_in_word_is_fine(self):
        self.assertEqual(rules("A well-known case-insensitive match."), [])


class MarkdownSkips(unittest.TestCase):
    def test_fenced_code_is_skipped(self):
        text = "```\nfoo; bar — baz " + words(40) + "\n```\n"
        self.assertEqual(rules(text), [])

    def test_inline_code_is_masked(self):
        self.assertEqual(rules("Run `a; b — c`. Done."), [])

    def test_link_at_sentence_end_keeps_the_boundary(self):
        text = ("The catalog cap is tracked in issue ([#10](https://x.y/issues/10)). "
                "This second sentence is long enough to push the pair over twenty-five words combined.")
        self.assertNotIn("long-sentence", rules(text))

    def test_url_is_masked(self):
        self.assertEqual(rules("See https://example.test/a;b—c for it."), [])

    def test_headings_tables_quotes_html_are_skipped(self):
        text = (
            "# Heading; with — dash\n\n"
            "| a; b | c — d |\n|---|---|\n| e; f | g |\n\n"
            "> quoted; text — here\n\n"
            "<div>html; — </div>\n"
        )
        self.assertEqual(rules(text), [])

    def test_front_matter_is_skipped(self):
        text = "---\nname: x\ndescription: a; b — c\n---\n\nBody is fine."
        self.assertEqual(rules(text), [])

    def test_list_items_get_sentence_rule_not_lead_rule(self):
        item = f"- {words(prose_lint.MAX_LEAD + 1)}.\n"
        self.assertEqual(rules(item), [])
        item = f"- {words(prose_lint.MAX_SENTENCE + 1)}.\n"
        self.assertEqual(rules(item), ["long-sentence"])

    def test_list_item_continuation_joins(self):
        text = "- This item wraps\n  onto a second line.\n- Next item."
        self.assertEqual(rules(text), [])

    def test_image_line_is_skipped(self):
        self.assertEqual(rules("![alt; text — here](x.png)\n"), [])


class CommitMode(unittest.TestCase):
    def commit(self, text: str) -> list[str]:
        return [f["rule"] for f in prose_lint.lint_commit(text, "msg")]

    def test_good_message_passes(self):
        msg = "feat(auth): Redirect to login on 401\n\nPreviously X. Now Y.\n\nCo-Authored-By: Bot <b@x.test>\n"
        self.assertEqual(self.commit(msg), [])

    def test_subject_too_long(self):
        msg = "feat(auth): " + "A" + "x" * 70 + "\n\nBody."
        self.assertEqual(self.commit(msg), ["subject-length"])

    def test_subject_format_and_period(self):
        self.assertEqual(self.commit("added stuff.\n\nBody."), ["subject-format", "subject-period"])
        self.assertEqual(self.commit("feat: lowercase subject\n"), ["subject-format"])
        self.assertEqual(self.commit("feat(api)!: Breaking change\n"), [])

    def test_missing_blank_line(self):
        self.assertEqual(self.commit("fix: Thing\nBody right away."), ["subject-blank-line"])

    def test_body_prose_is_linted_with_offset(self):
        found = prose_lint.lint_commit("fix: Thing\n\nFine lead.\n\nOne; two.", "msg")
        self.assertEqual([(f["line"], f["rule"]) for f in found], [(5, "semicolon")])

    def test_trailers_are_skipped(self):
        msg = "fix: Thing\n\nFine.\n\nSigned-off-by: Someone; Else <x@y.test>\nCo-Authored-By: A — B <a@b.test>\n"
        self.assertEqual(self.commit(msg), [])


class Reporting(unittest.TestCase):
    def test_line_numbers_point_at_sentence_start(self):
        text = "Fine lead.\n\nFine lead. " + words(30) + "."
        found = prose_lint.lint(text, "t.md")
        self.assertEqual([(f["line"], f["rule"]) for f in found], [(3, "long-sentence")])


if __name__ == "__main__":
    unittest.main()
