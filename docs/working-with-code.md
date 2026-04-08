# Working with Code

**Two modes — pick the right one:**

| Intent | Where | How |
|--------|-------|-----|
| **Read / analyze** code (PR review, code search, dependency analysis) | `repos/` clones | Read files directly — do NOT clone elsewhere |
| **Read a specific version** (bug on release-2.12, historical commit) | `repos/` clones | `git fetch` + `git checkout FETCH_HEAD`, restore after |
| **Modify** code (create PR, fix bug, new feature) | `workspace/` worktrees | Use sfa-workspace-clone skill |

## `repos/` — Reading

Shallow clones under `repos/` are read-only reference copies, organized by category (see [repos.yaml](../repos/repos.yaml)). Use them directly for **all** read-only tasks: code analysis, PR diff review, dependency tracing, searching. NEVER clone a repo to `/tmp` or any other location just to read it — use `repos/` instead. NEVER modify source files, create branches, or commit inside `repos/`.

**Auto-clone on demand.** Not all repos may be cloned locally. When a task requires reading repo source code, check if the target repo directory exists. If not, run `./repos/sync-repos.sh` to clone all repos, or manually clone the specific one. For simple metadata queries (issue counts, PR status), prefer GitHub API calls instead.

**Prefer local repos/ for complex tasks.** When a task involves cross-file analysis, dependency tracing, code search across multiple repos, or detailed PR review requiring full file context — always use local `repos/` clones rather than GitHub CLI API. The GitHub API is better suited for simple metadata queries (PR status, issue counts, labels). For anything that needs code comprehension, local clones give better results.

**Version-specific analysis.** Repos are shallow clones (depth 1), so historical refs are not available by default. To analyze a specific branch or tag, fetch it on demand and restore afterward:

```bash
cd repos/path/to/repo
original=$(git rev-parse HEAD)
git fetch origin release-2.12 --depth 1
git checkout FETCH_HEAD        # detached HEAD, safe for reading
# ... analyze code ...
git checkout $original         # restore to original commit
```

## `workspace/` — Writing

All code modifications MUST use the [sfa-workspace-clone](../.claude/skills/sfa-workspace-clone/SKILL.md) skill. NEVER use plain `git clone` into `workspace/`. The sfa-workspace-clone skill uses bare repos + worktrees, which enables concurrent development on multiple branches of the same repo and supports automated cleanup. The `workspace/` directory is git-ignored.

- **Checking out a PR:** `.claude/skills/sfa-workspace-clone/clone-worktree.sh <org/repo> <pr-number>`
- **Starting new development:** `.claude/skills/sfa-workspace-clone/clone-worktree.sh --new <org/repo> <branch-name> [--base <base-branch>]`

**Push workflow is environment-aware.** The `--new` mode auto-detects the execution environment:

- **Autonomous mode** (`GH_APP_ID` + `GH_APP_INSTALLATION_ID` set): pushes directly to upstream with `sfa/` branch prefix. No fork needed.
- **Local mode** (default): uses fork workflow — pushes to your fork, creates PR from fork to upstream.

See the [Development Guide](development-guide.md#push-workflow) for details and PR targeting rules (OCM vs stolostron).

## Intermediate Artifacts

All intermediate and generated files (processed data, reports, payloads, temp scripts) **MUST** go into the `.output/` directory, never the project root. This directory is git-ignored.

```bash
mkdir -p .output
jq ... > .output/processed_prs.json
python3 ... .output/report.md
python3 ... .output/slack_payload.json
```

**NEVER** create intermediate files like `*.json`, `*.py`, `*.sh`, `report.md` in the project root.
