#!/usr/bin/env python3
"""Validate the swd plugin against both manifests it ships.

Two ecosystems read this repo:

  * Claude Code reads `.claude-plugin/marketplace.json` and the `skills` array in it.
  * Codex (and other Agent Plugins clients) read the root `plugin.json` and discover
    skills by scanning `skills/*/SKILL.md`.

The two must not drift, and the Agent Plugins manifest must be exactly right: a wrong
`$schema` is not a warning, it makes `codex plugin add` fail outright.

Exits 0 on success, 1 with a list of errors otherwise. Stdlib only — no pip required.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MARKETPLACE = REPO / ".claude-plugin" / "marketplace.json"
PLUGIN_MANIFEST = REPO / "plugin.json"
SKILLS_DIR = REPO / "skills"

ALLOWED_FRONTMATTER_KEYS = {
    "name",
    "description",
    "license",
    "allowed-tools",
    "metadata",
    "compatibility",
}

# Agent Plugins 1.0.0. Codex validates this string exactly and refuses to install the
# plugin if it does not match, so it is pinned deliberately — bumping it is a conscious,
# tested edit, not a maintenance chore.
AGENT_PLUGINS_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"

# The Agent Plugins manifest schema is closed (additionalProperties: false). The spec
# downgrades unknown keys to warnings; we treat them as errors because in our own repo an
# unknown key is always a typo.
ALLOWED_MANIFEST_KEYS = {
    "$schema",
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "extensions",
}
ALLOWED_AUTHOR_KEYS = {"name", "email", "url"}

# From plugin.schema.json: lowercase alphanumerics, dots and hyphens, no leading or
# trailing separator, no `--` or `..` runs.
PLUGIN_NAME_RE = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")

# Skills must read the same on every host, so they may not name one host's tool registry.
# Describe the capability ("a read-only search subagent", "your task or plan tool")
# instead of the tool that provides it on Claude Code.
HOST_SPECIFIC_PATTERNS = [
    (re.compile(r"\bExplore (?:sub)?agents?\b"), "read-only search subagent"),
    (re.compile(r"\bTask(?:Create|Update|List)\b"), "your host's task or plan tool"),
    (re.compile(r"\bTodoWrite\b"), "your host's task or plan tool"),
    (re.compile(r"\bExitPlanMode\b"), "plain prose about leaving plan mode"),
    (re.compile(r"\bNotebookEdit\b"), "a generic description of editing the notebook"),
    (re.compile(r"\bWeb(?:Fetch|Search)\b"), "a generic description of fetching or searching"),
]

# Codex injects the raw SKILL.md text — frontmatter included — and cuts it at this many
# UTF-8 bytes (codex-rs/ext/skills/src/render.rs, `MAX_SKILL_PROMPT_BYTES`). The model gets a
# one-line "was truncated" warning and no pointer back to the file, so anything past the cut
# is simply gone. Claude Code has no such cap. Mirrors an upstream constant deliberately: a
# bump here is a conscious edit, made after re-reading the source. See issue #10.
CODEX_SKILL_PROMPT_BYTES = 8_000

# Same file, `MAX_CATALOG_SKILL_DESCRIPTION_CHARS`: longer descriptions are shortened in the
# skill catalog. Counted in Unicode scalar values, which is what Python's len() returns.
CODEX_DESCRIPTION_CHARS = 1_024

# Codex's default shared budget for every skill's name + description (or 2% of the context
# window when known); past it, all descriptions are trimmed proportionally.
CODEX_METADATA_CHARS = 8_000

# The cut lands mid-word at byte 8000. Warn at 90% so one added paragraph cannot tip a skill
# over between two CI runs.
BUDGET_HEADROOM = 0.9

# Every skill is over the prompt budget today (#10). Size violations are warnings until the
# last core is under budget; then this flips to True and they fail the build.
ENFORCE_PROMPT_BYTES = False


def parse_frontmatter(skill_md: Path) -> tuple[dict | None, str]:
    """Parse the flat YAML frontmatter of a SKILL.md without a YAML library.

    Handles what skill frontmatter actually uses: `key: value` scalars, quoted scalars, and
    multi-line values — both block scalars (`key: >` / `key: |`) and plain continuation
    lines. Anything fancier (nested maps, lists) is out of scope and reported as an error.
    """
    text = skill_md.read_text()
    if not text.startswith("---"):
        return None, "no YAML frontmatter (file does not start with '---')"
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return None, "frontmatter delimiters not found"

    data: dict = {}
    key: str | None = None
    block: str | None = None  # ">" folded, "|" literal, None plain
    for raw_line in match.group(1).splitlines():
        line = raw_line.rstrip()
        if key is not None and (line.startswith((" ", "\t")) or (block and not line)):
            # Continuation of the previous value.
            piece = line.strip()
            if block == "|":
                data[key] = f"{data[key]}\n{piece}" if data[key] else piece
            else:
                data[key] = f"{data[key]} {piece}".strip() if piece else data[key]
            continue
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            return None, f"unparseable frontmatter line: {raw_line!r}"
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value in (">", "|", ">-", "|-", ">+", "|+"):
            block, value = value[0], ""
        else:
            block = None
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
        data[key] = value
    return data, ""


def validate_agent_plugins_manifest(errors: list[str]) -> dict:
    """Check root plugin.json against Agent Plugins 1.0.0. Returns {} if unusable."""
    if not PLUGIN_MANIFEST.exists():
        errors.append("missing plugin.json (Agent Plugins manifest) at the repo root")
        return {}

    try:
        manifest = json.loads(PLUGIN_MANIFEST.read_text())
    except json.JSONDecodeError as e:
        errors.append(f"plugin.json is not valid JSON: {e}")
        return {}

    if not isinstance(manifest, dict):
        errors.append("plugin.json must contain a JSON object")
        return {}

    schema = manifest.get("$schema")
    if schema != AGENT_PLUGINS_SCHEMA:
        errors.append(
            f"plugin.json '$schema' must be exactly {AGENT_PLUGINS_SCHEMA!r} "
            f"(found {schema!r}) — Codex refuses to install the plugin otherwise"
        )

    name = manifest.get("name")
    if not name:
        errors.append("plugin.json missing 'name'")
    elif not isinstance(name, str) or not PLUGIN_NAME_RE.match(name) or len(name) > 64:
        errors.append(
            f"plugin.json 'name' {name!r} is not a valid Agent Plugins name "
            "(lowercase alphanumerics, '.' and '-', no leading/trailing separator, "
            "no '--' or '..' runs, max 64 chars)"
        )

    unexpected = set(manifest) - ALLOWED_MANIFEST_KEYS
    if unexpected:
        errors.append(
            f"plugin.json: unexpected top-level key(s): {', '.join(sorted(unexpected))} "
            "(the Agent Plugins manifest schema is closed)"
        )

    author = manifest.get("author")
    if author is not None:
        if not isinstance(author, dict):
            errors.append("plugin.json 'author' must be an object")
        else:
            unexpected_author = set(author) - ALLOWED_AUTHOR_KEYS
            if unexpected_author:
                errors.append(
                    "plugin.json 'author': unexpected key(s): "
                    f"{', '.join(sorted(unexpected_author))}"
                )

    keywords = manifest.get("keywords")
    if keywords is not None and (
        not isinstance(keywords, list) or not all(isinstance(k, str) for k in keywords)
    ):
        errors.append("plugin.json 'keywords' must be an array of strings")

    return manifest


def validate_versions(errors: list[str], marketplace: dict, manifest: dict) -> None:
    """Every version field in the repo must agree — one number, bumped everywhere."""
    canonical = manifest.get("version")
    if not canonical:
        errors.append(
            "plugin.json missing 'version' — Codex derives the installed version from it, "
            "so omitting it stalls updates for Codex users"
        )
        return

    metadata_version = marketplace.get("metadata", {}).get("version")
    if metadata_version != canonical:
        errors.append(
            f"version mismatch: plugin.json has {canonical!r} but "
            f"marketplace.json metadata.version has {metadata_version!r}"
        )

    for plugin in marketplace.get("plugins", []):
        if plugin.get("name") != manifest.get("name"):
            continue
        entry_version = plugin.get("version")
        if entry_version != canonical:
            errors.append(
                f"version mismatch: plugin.json has {canonical!r} but marketplace entry "
                f"{plugin.get('name')!r} has {entry_version!r}"
            )


def validate_skill_layout(errors: list[str], marketplace: dict) -> None:
    """Both discovery paths must see the same five skills.

    Claude Code reads the marketplace `skills` array; Agent Plugins clients scan the
    immediate subdirectories of `skills/`. Drift between the two means a skill silently
    exists on one host and not the other.
    """
    if not SKILLS_DIR.is_dir():
        errors.append("missing skills/ directory")
        return

    on_disk = {d.name for d in sorted(SKILLS_DIR.iterdir()) if (d / "SKILL.md").is_file()}

    declared: set[str] = set()
    for plugin in marketplace.get("plugins", []):
        for skill_ref in plugin.get("skills", []):
            ref = Path(skill_ref)
            if ref.parent.name != "skills":
                errors.append(
                    f"marketplace skill path {skill_ref!r} is not directly under skills/ — "
                    "Agent Plugins clients only scan immediate subdirectories"
                )
            declared.add(ref.name)

    for missing in sorted(on_disk - declared):
        errors.append(
            f"skills/{missing}/ has a SKILL.md but is not listed in marketplace.json — "
            "Agent Plugins clients would load it, Claude Code would not"
        )
    for missing in sorted(declared - on_disk):
        errors.append(
            f"marketplace.json lists {missing!r} but skills/{missing}/SKILL.md does not exist"
        )

    # A SKILL.md nested deeper than one level is invisible to Agent Plugins clients.
    for nested in sorted(SKILLS_DIR.glob("*/*/**/SKILL.md")):
        errors.append(
            f"{nested.relative_to(REPO)}: nested SKILL.md is ignored by Agent Plugins "
            "clients (they do not recurse below skills/<name>/)"
        )


def validate_references(errors: list[str]) -> None:
    """Progressive-disclosure hygiene: reference files and SKILL.md must point at each other.

    A file under skills/<name>/references/ that SKILL.md never mentions is dead weight the
    model will never load; a referenced path that does not exist is an instruction the model
    cannot follow. Both are errors.
    """
    if not SKILLS_DIR.is_dir():
        return
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue
        text = skill_md.read_text()

        refs_dir = skill_dir / "references"
        on_disk = {p.name for p in refs_dir.glob("*.md")} if refs_dir.is_dir() else set()
        mentioned = set(re.findall(r"references/([\w.-]+\.md)", text))

        for unused in sorted(on_disk - mentioned):
            errors.append(
                f"skills/{skill_dir.name}/references/{unused}: not mentioned in SKILL.md — "
                "a reference file the skill never loads is dead weight"
            )
        for missing in sorted(mentioned - on_disk):
            errors.append(
                f"skills/{skill_dir.name}/SKILL.md references references/{missing}, "
                "which does not exist"
            )


def validate_skill_budgets(
    errors: list[str],
    warnings: list[str],
    skills_dir: Path = SKILLS_DIR,
    enforce_bytes: bool = ENFORCE_PROMPT_BYTES,
) -> list[dict]:
    """Keep every SKILL.md inside what Codex will actually load.

    Codex measures the raw file in UTF-8 bytes, frontmatter included; the catalog cap on the
    description is in characters. Returns one row per skill for the budget table.
    """
    rows: list[dict] = []
    if not skills_dir.is_dir():
        return rows

    byte_soft = int(CODEX_SKILL_PROMPT_BYTES * BUDGET_HEADROOM)
    desc_soft = int(CODEX_DESCRIPTION_CHARS * BUDGET_HEADROOM)
    metadata_total = 0

    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        rel = f"skills/{skill_md.parent.name}/SKILL.md"
        size = len(skill_md.read_bytes())
        frontmatter, _ = parse_frontmatter(skill_md)
        description = (frontmatter or {}).get("description", "")
        desc_len = len(description)
        metadata_total += len(skill_md.parent.name) + desc_len
        rows.append({"skill": skill_md.parent.name, "bytes": size, "description": desc_len})

        if size > CODEX_SKILL_PROMPT_BYTES:
            msg = (
                f"{rel}: {size} bytes; Codex truncates the prompt at "
                f"{CODEX_SKILL_PROMPT_BYTES} — move detail into references/ (#10)"
            )
            (errors if enforce_bytes else warnings).append(msg)
        elif size > byte_soft:
            warnings.append(
                f"{rel}: {size} bytes, within {CODEX_SKILL_PROMPT_BYTES - size} of the "
                f"{CODEX_SKILL_PROMPT_BYTES}-byte Codex cut — trim before adding more"
            )

        if desc_len > CODEX_DESCRIPTION_CHARS:
            errors.append(
                f"{rel}: description is {desc_len} chars; Codex shortens it in the catalog "
                f"past {CODEX_DESCRIPTION_CHARS}"
            )
        elif desc_len > desc_soft:
            warnings.append(
                f"{rel}: description is {desc_len} chars, close to the "
                f"{CODEX_DESCRIPTION_CHARS}-char Codex catalog cap"
            )

    if metadata_total > CODEX_METADATA_CHARS * BUDGET_HEADROOM:
        warnings.append(
            f"skill names + descriptions total {metadata_total} chars; Codex trims all "
            f"descriptions proportionally past {CODEX_METADATA_CHARS}"
        )
    return rows


def format_budget_table(rows: list[dict]) -> str:
    lines = [
        f"Skill budgets (Codex loads at most {CODEX_SKILL_PROMPT_BYTES} bytes of SKILL.md, "
        f"{CODEX_DESCRIPTION_CHARS} chars of description):"
    ]
    for row in rows:
        pct = 100 * row["bytes"] // CODEX_SKILL_PROMPT_BYTES
        lines.append(
            f"  {row['skill']:<12} {row['bytes']:>6} B {pct:>4}%   "
            f"description {row['description']:>5} ch"
        )
    return "\n".join(lines)


def validate_host_neutrality(errors: list[str]) -> None:
    """Skills must not hardcode one host's tool names."""
    if not SKILLS_DIR.is_dir():
        return
    for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        lines = skill_md.read_text().splitlines()
        for lineno, line in enumerate(lines, start=1):
            for pattern, suggestion in HOST_SPECIFIC_PATTERNS:
                match = pattern.search(line)
                if match:
                    errors.append(
                        f"{skill_md.relative_to(REPO)}:{lineno}: host-specific tool name "
                        f"{match.group(0)!r} — describe the capability instead "
                        f"(e.g. {suggestion})"
                    )


def validate_marketplace(errors: list[str]) -> dict:
    if not MARKETPLACE.exists():
        errors.append(f"missing {MARKETPLACE.relative_to(REPO)}")
        return {}

    try:
        marketplace = json.loads(MARKETPLACE.read_text())
    except json.JSONDecodeError as e:
        errors.append(f"{MARKETPLACE.relative_to(REPO)} is not valid JSON: {e}")
        return {}

    if "name" not in marketplace:
        errors.append("marketplace.json missing 'name'")
    if "plugins" not in marketplace or not isinstance(marketplace["plugins"], list):
        errors.append("marketplace.json missing 'plugins' array")
        return marketplace

    for plugin in marketplace["plugins"]:
        plugin_name = plugin.get("name", "<unnamed>")
        skills = plugin.get("skills", [])
        if not skills:
            errors.append(f"plugin {plugin_name!r}: no skills listed")
            continue
        for skill_ref in skills:
            skill_dir = (REPO / skill_ref).resolve()
            if not skill_dir.is_dir():
                errors.append(f"plugin {plugin_name!r}: skill path {skill_ref!r} is not a directory")
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                errors.append(f"{skill_ref}: missing SKILL.md")
                continue
            frontmatter, err = parse_frontmatter(skill_md)
            if frontmatter is None:
                errors.append(f"{skill_ref}/SKILL.md: {err}")
                continue
            unexpected = set(frontmatter) - ALLOWED_FRONTMATTER_KEYS
            if unexpected:
                errors.append(
                    f"{skill_ref}/SKILL.md: unexpected frontmatter key(s): "
                    f"{', '.join(sorted(unexpected))}"
                )
            if "name" not in frontmatter:
                errors.append(f"{skill_ref}/SKILL.md: frontmatter missing 'name'")
            elif frontmatter["name"] != skill_dir.name:
                errors.append(
                    f"{skill_ref}/SKILL.md: frontmatter name {frontmatter['name']!r} "
                    f"does not match directory {skill_dir.name!r}"
                )
            if "description" not in frontmatter or not frontmatter["description"]:
                errors.append(f"{skill_ref}/SKILL.md: frontmatter missing 'description'")

    return marketplace


def validate() -> tuple[list[str], list[str], list[dict]]:
    errors: list[str] = []
    warnings: list[str] = []
    marketplace = validate_marketplace(errors)
    manifest = validate_agent_plugins_manifest(errors)
    if marketplace and manifest:
        validate_versions(errors, marketplace, manifest)
    if marketplace:
        validate_skill_layout(errors, marketplace)
    validate_references(errors)
    budgets = validate_skill_budgets(errors, warnings)
    validate_host_neutrality(errors)
    return errors, warnings, budgets


def main() -> int:
    errors, warnings, budgets = validate()
    print(format_budget_table(budgets))
    if warnings:
        print("Warnings:")
        for w in warnings:
            print(f"  - {w}")
            if os.environ.get("GITHUB_ACTIONS"):
                # Surfaces as an annotation on the PR instead of dying in the job log.
                file, _, rest = w.partition(": ")
                print(f"::warning file={file}::{rest}")
    if errors:
        print("Validation failed:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
