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


def parse_frontmatter(skill_md: Path) -> tuple[dict | None, str]:
    text = skill_md.read_text()
    if not text.startswith("---"):
        return None, "no YAML frontmatter (file does not start with '---')"
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return None, "frontmatter delimiters not found"
    # Minimal YAML: scalar key: value lines only. Skill frontmatter is flat enough that
    # the stdlib gets us through without a full YAML parser.
    data: dict = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.rstrip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            return None, f"unparseable frontmatter line: {raw_line!r}"
        key, _, value = line.partition(":")
        data[key.strip()] = value.strip()
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


def validate() -> list[str]:
    errors: list[str] = []
    marketplace = validate_marketplace(errors)
    manifest = validate_agent_plugins_manifest(errors)
    if marketplace and manifest:
        validate_versions(errors, marketplace, manifest)
    if marketplace:
        validate_skill_layout(errors, marketplace)
    validate_host_neutrality(errors)
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Validation failed:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
