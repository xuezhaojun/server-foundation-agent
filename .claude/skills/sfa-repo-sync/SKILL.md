---
name: sfa-repo-sync
description: "Sync repos under repos/ to latest remote commits. Use this skill to initialize or update all SF repo clones. Trigger phrases: 'sync repos', 'update repos', 'fetch repos', 'init repos', 'refresh repos'."
---

# Sync Repos Skill

Clones or updates all repos defined in `repos.yaml` as shallow copies under `repos/`.

## When to Use This Skill

- First time setup: clone all repos after setting up the agent
- Before searching/reading repo code: ensure repos have the latest content
- Periodic refresh to keep reference copies up to date

## Usage

### Clone all repos (first time)

```bash
./repos/sync-repos.sh
```

### Update to latest remote commits

```bash
./repos/sync-repos.sh --update
```

### Show status

```bash
./repos/sync-repos.sh --status
```

## How It Works

- Reads `repos.yaml` for the list of repos and their categories
- Uses `git clone --depth 1` for initial clones (shallow)
- Uses `git fetch --depth 1` + checkout for updates
- Repos are organized by category: `repos/{category}/{org}/{repo}`

## Important

- `repos/` is **READ-ONLY** — clones are reference copies for reading/searching only
- NEVER modify, branch, or commit inside `repos/`
- For code changes, use the [sfa-workspace-clone](../sfa-workspace-clone/SKILL.md) skill instead
- To add a new repo, edit `repos.yaml` and re-run the sync
