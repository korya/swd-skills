# swd — software development skills

A Claude Code plugin bundling four skills for serious software work.

| Skill | When it triggers |
| --- | --- |
| **super-plan** | "/super-plan", "plan this thoroughly", "deep plan" — non-trivial changes where a wrong direction would burn meaningful time. |
| **rca** | "/rca", "root cause", "5 whys", "why is this failing" — failures you want to learn from, not just patch. |
| **repo-docs** | "document the project for coding agents", "set up agent docs", "add AGENTS.md" — bootstrap or extend `AGENTS.md` + `docs/`. |
| **rebase** | "rebase this branch on X", "move these commits onto the new base" — keep the original spec, invariants, and conventions intact. |

## Install (from GitHub)

```sh
/plugin marketplace add korya/swd-skills
/plugin install swd@swd
```

The first command points Claude Code at `github.com/korya/swd-skills` as a marketplace. The second installs the `swd` plugin from that marketplace (`<plugin>@<marketplace>`).

The marketplace's internal name is `swd` (set in `.claude-plugin/marketplace.json`), which is why the install target is `swd@swd` even though the repo is `swd-skills`.

## Install (local checkout, for development)

```sh
git clone https://github.com/korya/swd-skills.git
/plugin marketplace add /absolute/path/to/swd-skills
/plugin install swd@swd
```

After editing a skill, run `/reload-plugins` to pick up the changes.

## Update

```sh
/plugin marketplace update swd
```

## Layout

```
.claude-plugin/
  marketplace.json   # marketplace manifest (one plugin: swd)
  plugin.json        # plugin manifest
skills/
  super-plan/
  rca/
  repo-docs/
  rebase/
```
