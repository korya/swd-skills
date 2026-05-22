#!/usr/bin/env python3
"""Validate the swd plugin: marketplace.json shape, skill paths, SKILL.md frontmatter.

Exits 0 on success, 1 with a list of errors otherwise. Stdlib only — no pip required.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MARKETPLACE = REPO / ".claude-plugin" / "marketplace.json"

ALLOWED_FRONTMATTER_KEYS = {
    "name",
    "description",
    "license",
    "allowed-tools",
    "metadata",
    "compatibility",
}


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


def validate() -> list[str]:
    errors: list[str] = []

    if not MARKETPLACE.exists():
        return [f"missing {MARKETPLACE.relative_to(REPO)}"]

    try:
        marketplace = json.loads(MARKETPLACE.read_text())
    except json.JSONDecodeError as e:
        return [f"{MARKETPLACE.relative_to(REPO)} is not valid JSON: {e}"]

    if "name" not in marketplace:
        errors.append("marketplace.json missing 'name'")
    if "plugins" not in marketplace or not isinstance(marketplace["plugins"], list):
        return errors + ["marketplace.json missing 'plugins' array"]

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
