# Solutions

Solutions are **agent-discovered**, problem-oriented SOPs. When the agent encounters a specific problem during its work (e.g., a CVE dependency cascade on an older branch), it searches `solutions/` for a matching SOP and follows it.

**Key trait:** The agent initiates the lookup. The user does not need to know which solution exists — the agent finds it by matching the problem context against solution descriptions.

> Compare with [Workflows](../workflows/README.md): workflows are **user-triggered or scheduled** — the user knows the workflow and asks for it by name.

| Solution | Description |
|----------|-------------|
| [SOP-older-branch-dep-upgrade](SOP-older-branch-dep-upgrade.md) | CVE-driven dependency upgrades on older release branches |
| [ocm-dependency-versions](ocm-dependency-versions.md) | OCM upstream dependency version survey and analysis |

## Adding a New Solution

1. Create `solutions/<solution-name>.md` with the SOP content
2. Update this table
3. Open a PR
