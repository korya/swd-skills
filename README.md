# swd — software development skills

A plugin bundling five skills for serious software work. Runs on **Claude Code**, **Codex CLI**, and any [Agent Plugins](https://agent-plugins.org/) client.

| Skill | When it triggers |
| --- | --- |
| **blueprint** | "/blueprint", "blueprint this", "plan this thoroughly", "deep plan" — non-trivial changes where a wrong direction would burn meaningful time. |
| **rca** | "/rca", "root cause", "5 whys", "why is this failing" — failures you want to learn from, not just patch. |
| **repo-docs** | "document the project for coding agents", "set up agent docs", "add AGENTS.md" — bootstrap or extend `AGENTS.md` + `docs/`. |
| **rebase** | "rebase this branch on X", "move these commits onto the new base" — keep the original spec, invariants, and conventions intact. |
| **examine** | "/examine", "examine this PR", "review this PR", "review my branch", "check my PR before merge" — production-risk-first holistic review of a PR, branch, or working tree; the host's built-in review is defect-first, this one also judges intent, approach, and right-sizing. |

Invocation differs per host: in Claude Code the skills fire on `/blueprint`, `/rca`, `/examine`, … (or on the natural-language triggers above); in Codex they are namespaced mentions — `$swd:blueprint`, `$swd:rca`, `$swd:examine`, `$swd:rebase`, `$swd:repo-docs`.

## Install (from GitHub)

**Claude Code** — in the session:

```sh
/plugin marketplace add korya/swd-skills
/plugin install swd@swd
```

**Codex CLI** — in the shell (requires Codex ≥ 0.145):

```sh
codex plugin marketplace add korya/swd-skills
codex plugin add swd@swd
```

The first command points the host at `github.com/korya/swd-skills` as a marketplace. The second installs the `swd` plugin from that marketplace (`<plugin>@<marketplace>`).

The marketplace's internal name is `swd` (set in `.claude-plugin/marketplace.json`), which is why the install target is `swd@swd` even though the repo is `swd-skills`.

## Install (local checkout, for development)

```sh
git clone https://github.com/korya/swd-skills.git
```

**Claude Code:**

```sh
/plugin marketplace add /absolute/path/to/swd-skills
/plugin install swd@swd
```

After editing a skill, run `/reload-plugins` to pick up the changes.

**Codex CLI:**

```sh
codex plugin marketplace add /absolute/path/to/swd-skills
codex plugin add swd@swd
```

Codex copies the plugin into `~/.codex/plugins/cache/`, so edits to your checkout are *not* live. After editing a skill, re-run `codex plugin add swd@swd` to re-sync the copy, then start a new Codex session.

## Update

**Claude Code:**

```sh
/plugin marketplace update swd
```

**Codex CLI:**

```sh
codex plugin marketplace upgrade swd
```

This refreshes the Git snapshot *and* the installed copy under `~/.codex/plugins/cache/`. It only works for unpinned Git marketplaces — if you added the marketplace with `--ref <sha>`, `upgrade` fails; re-add it without the ref.

## Other hosts

The skills themselves are portable — `SKILL.md` with YAML frontmatter is read by OpenCode, pi, Grok Build, and Muse Code too. Only the *packaging* is host-specific: outside Claude Code and Codex there is no install command, so clone the repo and point your agent at `skills/`.

| Host | Reads |
| --- | --- |
| OpenCode | `.opencode/skills/`, `.claude/skills/`, `.agents/skills/` (and `~/` equivalents) |
| pi | `~/.pi/agent/skills/`, `~/.agents/skills/`, `.agents/skills/` |
| Muse Code | `~/.agents/skills/`, `.agents/skills/`; also `muse skills import --from claude` |
| Grok Build | `.claude/` skills, `AGENTS.md`, hooks, MCP |

`~/.agents/skills/` is the closest thing to a vendor-neutral location — symlinking `skills/*` there covers most of the table.

## Layout

```
plugin.json          # Agent Plugins 1.0.0 manifest (Codex + other AP clients)
.claude-plugin/
  marketplace.json   # marketplace manifest + plugin definition (Claude Code)
skills/
  blueprint/
  rca/
  repo-docs/
  rebase/
  examine/           # SKILL.md core + references/ loaded per step
LICENSE              # AGPL-3.0-or-later
```

Two manifests, one package. Claude Code reads `marketplace.json` and ignores `plugin.json`; Codex resolves `plugin.json` first and validates its `$schema` strictly — a wrong value makes `codex plugin add` fail outright. CI runs both hosts' native validators to keep them honest, plus `scripts/validate.py` for the checks neither host makes (version agreement across manifests, marketplace ↔ `skills/` symmetry, and skills naming no host-specific tool).

## Development

```sh
python3 scripts/validate.py
```

Bump the version in **both** `plugin.json` and `.claude-plugin/marketplace.json` (`metadata.version` and the plugin entry). The validator fails if they disagree — Codex derives the installed version from `plugin.json`, so a stale value stalls updates for Codex users.
