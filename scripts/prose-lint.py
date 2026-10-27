#!/usr/bin/env python3
"""Lint Markdown prose against the structural rules in assets/writing.md.

The skills run it on every text a person will read before that text leaves the skill:
commit bodies, PR descriptions, reports, specs. CI runs it on the skills' own files.

Rules (all hard, exit 1 on any finding):

  long-sentence   a sentence over MAX_SENTENCE words
  long-lead       the first sentence of a paragraph over MAX_LEAD words
  long-paragraph  a paragraph with more than MAX_PARAGRAPH sentences
  teaser-lead     a paragraph lead that announces a count of things without naming them
  semicolon       any semicolon outside code
  dash            an em dash, a spaced en dash, or a spaced double hyphen outside code

With --commit the input is a git commit message: the first line must be a Conventional
Commits subject of at most 72 characters (type(scope): Subject, capitalized, no trailing
period), the second line must be blank, and the rest is linted as prose. Trailer lines
such as Co-Authored-By are skipped.

What it skips: fenced code, inline code, URLs, headings, YAML front matter, HTML lines,
table rows, and blockquotes (quoted material is someone else's prose). List items are
linted for sentence length but not for the lead rule: an item is a line, not a paragraph.

Heuristics, not a parser. The Markdown handling follows the approach of
danyuchn/asd-ste100-skill's ste-lint.py (MIT).

Usage:
    prose-lint.py FILE [FILE ...]     exit 1 when any rule fires
    echo "text" | prose-lint.py       lint stdin
    prose-lint.py --json FILE         one JSON object per finding
    prose-lint.py --commit MSGFILE    lint a commit message (subject rules + body prose)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MAX_SENTENCE = 25
MAX_LEAD = 20
MAX_PARAGRAPH = 6

CODE_FENCE = re.compile(r"^ {0,3}(```|~~~)")
INLINE_CODE = re.compile(r"`[^`\n]*`")
URL = re.compile(r"https?://[^\s)]+|www\.[^\s)]+")
HEADING = re.compile(r"^ {0,3}#{1,6}(\s|$)")
RULE_LINE = re.compile(r"^ {0,3}(?:[-*_] *){3,}$")
HTML_LINE = re.compile(r"^ {0,3}<")
TABLE_ROW = re.compile(r"^ {0,3}\|.*\|\s*$|^ {0,3}[^|\n]+\|[^|\n]+")
BLOCKQUOTE = re.compile(r"^ {0,3}>")
LIST_ITEM = re.compile(r"^(?P<indent> *)(?P<marker>[-*+]|\d+[.)])\s+")
FOOTNOTE_OR_REF = re.compile(r"^ {0,3}\[[^\]]+\]:\s")
IMAGE_ONLY = re.compile(r"^\s*!\[[^\]]*\]\([^)]*\)\s*$")

MAX_SUBJECT = 72
SUBJECT = re.compile(r"^(?:feat|fix|chore|refactor|test|docs|perf|build|ci|style|revert)(?:\([^)]+\))?!?: [A-Z]")
TRAILER = re.compile(r"^[A-Za-z-]+: \S")

# "Two things went wrong." as a paragraph opener: a count of unnamed things is not a claim.
TEASER = re.compile(
    r"^(?:Two|Three|Four|Five|Several|A few|Some|Multiple|Many)\s+"
    r"(?:things|designs|principles|reasons|factors|causes|changes|points|problems|issues|"
    r"parts|decisions|behaviou?rs|rules|forces|ideas|effects|concerns|aspects|observations)\b"
    r"[^.!?]{0,60}[.!?]$", re.I)

SEMICOLON = re.compile(r";")
DASH = re.compile(r"—|(?<=\s)–(?=\s)|(?<=\s)--(?=\s)")

WORD = re.compile(r"[^\W_]")
SENTENCE_END = re.compile(r"[.!?][\"'”’)\]*_]*$")
OPENERS = "\"'“‘([*_"
ABBREVIATIONS = {
    "vs.", "cf.", "approx.", "etc.", "mr.", "mrs.", "ms.", "dr.", "fig.",
}
DOTTED = re.compile(r"(?:[a-z]\.){2,}", re.I)


def count_words(text: str) -> int:
    return sum(1 for tok in text.split() if WORD.search(tok))


def mask(text: str) -> str:
    """Blank inline code and URLs with spaces so columns stay true."""
    text = INLINE_CODE.sub(lambda m: " " * len(m.group(0)), text)
    return URL.sub(lambda m: "x" * len(m.group(0)), text)


def sentences(text: str) -> list[tuple[int, int]]:
    """Return (start, end) offsets of each sentence in text."""
    words = list(re.finditer(r"\S+", text))
    if not words:
        return []
    starts = [words[0].start()]
    for word, nxt in zip(words, words[1:]):
        end = SENTENCE_END.search(word.group())
        if not end:
            continue
        core = word.group()[: end.start() + 1].lstrip(OPENERS)
        if core.lower() in ABBREVIATIONS:
            continue
        if DOTTED.fullmatch(core) and not nxt.group().lstrip(OPENERS)[:1].isupper():
            continue
        starts.append(nxt.start())
    ends = starts[1:] + [len(text)]
    return list(zip(starts, ends))


class Block:
    """Consecutive prose lines that form one paragraph or one list item."""

    def __init__(self, kind: str) -> None:
        self.kind = kind  # "paragraph" or "item"
        self.pieces: list[tuple[int, str]] = []  # (lineno, text)

    def add(self, lineno: int, text: str) -> None:
        if text.strip():
            self.pieces.append((lineno, text.strip()))

    def findings(self, filename: str) -> list[dict]:
        if not self.pieces:
            return []
        offsets, pos = [], 0
        for _, text in self.pieces:
            offsets.append(pos)
            pos += len(text) + 1
        joined = " ".join(text for _, text in self.pieces)
        spans = sentences(joined)
        out = []

        def line_of(offset: int) -> int:
            idx = max(i for i, o in enumerate(offsets) if o <= offset)
            return self.pieces[idx][0]

        for i, (start, end) in enumerate(spans):
            n = count_words(joined[start:end])
            if i == 0 and self.kind == "paragraph" and TEASER.match(joined[start:end].strip()):
                out.append(finding(filename, line_of(start), "teaser-lead",
                                   "Lead announces a count of things without naming them. "
                                   "State the claim instead."))
            if i == 0 and self.kind == "paragraph" and n > MAX_LEAD:
                out.append(finding(filename, line_of(start), "long-lead",
                                   f"Paragraph lead has {n} words (max {MAX_LEAD}). "
                                   "State the claim first, unfold it after."))
            elif n > MAX_SENTENCE:
                out.append(finding(filename, line_of(start), "long-sentence",
                                   f"Sentence has {n} words (max {MAX_SENTENCE}). Split it."))
        if self.kind == "paragraph" and len(spans) > MAX_PARAGRAPH:
            out.append(finding(filename, self.pieces[0][0], "long-paragraph",
                               f"Paragraph has {len(spans)} sentences (max {MAX_PARAGRAPH}). "
                               "One topic per paragraph."))
        return out


def finding(filename: str, line: int, rule: str, message: str) -> dict:
    return {"file": filename, "line": line, "rule": rule, "message": message}


def lint(text: str, filename: str = "<stdin>") -> list[dict]:
    out: list[dict] = []
    lines = text.splitlines()
    in_fence = False
    fence_mark = ""
    block: Block | None = None
    start = 0

    # YAML front matter
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() in ("---", "..."):
                start = i + 1
                break

    def flush() -> None:
        nonlocal block
        if block is not None:
            out.extend(block.findings(filename))
        block = None

    for lineno in range(start + 1, len(lines) + 1):
        raw = lines[lineno - 1]
        fence = CODE_FENCE.match(raw)
        if fence and (not in_fence or raw.strip().startswith(fence_mark)):
            if not in_fence:
                fence_mark = fence.group(1)
            in_fence = not in_fence
            flush()
            continue
        if in_fence:
            continue

        stripped = raw.strip()
        if (not stripped or HEADING.match(raw) or RULE_LINE.match(raw) or HTML_LINE.match(raw)
                or TABLE_ROW.match(raw) or BLOCKQUOTE.match(raw) or FOOTNOTE_OR_REF.match(raw)
                or IMAGE_ONLY.match(raw)):
            flush()
            continue

        line = mask(raw)
        for m in SEMICOLON.finditer(line):
            out.append(finding(filename, lineno, "semicolon",
                               "Semicolon. Split into two sentences."))
        for m in DASH.finditer(line):
            out.append(finding(filename, lineno, "dash",
                               "Dash used to join clauses. Split the sentence or use a comma."))

        item = LIST_ITEM.match(line)
        if item:
            flush()
            block = Block("item")
            block.add(lineno, line[item.end():])
            continue
        if block is None:
            block = Block("paragraph")
        block.add(lineno, line)
    flush()
    out.sort(key=lambda f: (f["line"], f["rule"]))
    return out


def lint_commit(text: str, filename: str = "<stdin>") -> list[dict]:
    """Subject-line rules for a commit message, then the body as prose."""
    lines = text.splitlines()
    out: list[dict] = []
    subject = lines[0] if lines else ""
    if not SUBJECT.match(subject):
        out.append(finding(filename, 1, "subject-format",
                           "Subject is not `type(scope): Subject` with a capitalized subject."))
    if len(subject) > MAX_SUBJECT:
        out.append(finding(filename, 1, "subject-length",
                           f"Subject has {len(subject)} characters (max {MAX_SUBJECT})."))
    if subject.rstrip().endswith("."):
        out.append(finding(filename, 1, "subject-period", "Subject ends with a period."))
    if len(lines) > 1 and lines[1].strip():
        out.append(finding(filename, 2, "subject-blank-line",
                           "Second line must be blank to separate subject and body."))
    body = [("" if TRAILER.match(l) else l) for l in lines[2:]]
    for f in lint("\n".join(body), filename):
        f["line"] += 2
        out.append(f)
    out.sort(key=lambda f: (f["line"], f["rule"]))
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("files", nargs="*", help="Markdown files; stdin when omitted")
    parser.add_argument("--json", action="store_true", help="emit one JSON object per finding")
    parser.add_argument("--commit", action="store_true",
                        help="treat each input as a git commit message")
    args = parser.parse_args(argv)

    sources: list[tuple[str, str]] = []
    if args.files:
        for name in args.files:
            path = Path(name)
            if path.is_dir():
                for p in sorted(path.rglob("*.md")):
                    sources.append((str(p), p.read_text(encoding="utf-8")))
            else:
                sources.append((name, path.read_text(encoding="utf-8")))
    else:
        sources.append(("<stdin>", sys.stdin.read()))

    findings: list[dict] = []
    for name, text in sources:
        findings.extend(lint_commit(text, name) if args.commit else lint(text, name))

    for f in findings:
        if args.json:
            print(json.dumps(f))
        else:
            print(f"{f['file']}:{f['line']}: {f['rule']}: {f['message']}")
    if not args.json:
        n = len(findings)
        print(f"{n} finding{'s' if n != 1 else ''} in {len(sources)} file{'s' if len(sources) != 1 else ''}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
