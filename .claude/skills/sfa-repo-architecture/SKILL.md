---
name: sfa-repo-architecture
description: "Generate an architectural overview of upstream OCM-io vs downstream stolostron repos for Server Foundation. Clones all repos, analyzes their code, and produces a Mermaid-diagrammed markdown file at the repo root. Trigger phrases: 'generate architecture doc', 'repo architecture', 'upstream downstream diagram', 'ocm vs stolostron', 'generate repo overview'."
---

# Repo Architecture Overview Generator

Generates `SF-REPO-ARCHITECTURE.md` at the repo root — a self-contained architectural explanation of how upstream `open-cluster-management-io` repos relate to downstream `stolostron` repos for the Server Foundation team, including Mermaid diagrams renderable on GitHub.

## When to Use This Skill

- Onboarding someone who needs to understand the upstream/downstream repo landscape
- Refreshing the diagram after repos are added or removed in `repos.yaml`
- Explaining to stakeholders why the mapping is not 1:1

## Output

- **File**: `SF-REPO-ARCHITECTURE.md` (repo root, sibling to `README.md`)
- **Format**: Markdown with Mermaid diagrams (GitHub-renderable)

## Checklist

### Step 1: Parse repos.yaml for the definitive repo list

Read `repos/repos.yaml` — the **single source of truth** for which repos the SF team owns. Extract repos from these categories:

- **`server-foundation`** — SF-owned components (both `ocm-io` and `stolostron` sub-groups)
- **`deps`** — forked dependency libraries with SF-specific changes (e.g., apiserver-network-proxy, grpc-go)

Also note repos under `installer` (backplane-operator, multiclusterhub-operator) — not SF-owned but needed for deployment context.

Do NOT hardcode repo names. Parse them from `repos.yaml` so new repos are automatically picked up.

### Step 2: Clone repos to a temp directory

Clone all repos extracted from Step 1:

```bash
WORK_DIR=$(mktemp -d /tmp/sfa-repo-arch-XXXXXX)

# Parse repos.yaml and clone all server-foundation + deps repos
# (the agent should extract org/repo pairs from the YAML and clone each)
```

Additionally clone these **context repos** that are not SF-owned but are needed for analysis:

- `stolostron/backplane-operator` — deployment topology (from `installer` category)
- `stolostron/cluster-lifecycle-api` — shared API types (not in repos.yaml but used by 4 SF repos; TODO: consider adding to repos.yaml)

### Step 3: Analyze each repo

For **every** cloned repo, read and understand:

1. **README.md** — what the project says it does
2. **go.mod** — module path, Go version, key dependencies (especially `open-cluster-management-io/*` and `stolostron/*` imports)
3. **cmd/** or **main.go** — what binaries it builds, what each binary does
4. **pkg/** or **internal/** — top-level package names to understand the domain
5. **deploy/** or **config/** or **charts/** — what CRDs it installs, what it deploys
6. **Makefile** or **Dockerfile** — build targets, image names

For each repo, write a **2-3 sentence summary** of what it actually does based on the code, not just the name.

### Step 4: Analyze relationships

From the code analysis in Step 3, determine:

1. **Paired repos** — repos that exist in both orgs. Read both copies to understand what the downstream adds on top (look for Dockerfile differences, extra cmd/ binaries, downstream-only packages)
2. **Upstream-only repos** — why they don't need a downstream copy (are they libraries? CLI tools? consumed how?)
3. **Downstream-only repos** — what product-specific function they serve, which upstream libraries they consume (from go.mod)
4. **Dependency forks** — repos under `deps` in repos.yaml (e.g., apiserver-network-proxy, grpc-go) and why SF maintains forks
5. **Dependency flow** — from go.mod analysis, build the actual dependency graph
6. **Shared stolostron dependencies** — identify libraries like `cluster-lifecycle-api`, `stolostron/applier`, `stolostron/library-go` that are used across multiple downstream repos
7. **Deployment topology** — from `backplane-operator/pkg/templates/charts/`, determine which Helm chart deploys which component

### Step 5: Generate the markdown file

Write `SF-REPO-ARCHITECTURE.md` at the repo root with the following sections. Populate with **current data** from Step 1-4.

The file MUST contain these sections:

1. **Title and intro** — what this document is, when it was generated, which repos.yaml categories were used
2. **Context** — what the two GitHub orgs are and their purpose
3. **Why It's Not 1:1** — explanation grounded in actual code analysis
4. **Repo Landscape Diagram** — Mermaid flowchart showing both orgs with color-coded groupings and relationship arrows
5. **Per-repo descriptions** — for EVERY repo from repos.yaml `server-foundation` + `deps`, a real description based on code analysis
6. **Upstream-Only Repos** — with code-based explanation of why no downstream copy exists
7. **Downstream-Only Repos** — with code-based explanation of what product function they serve
8. **Paired Repos** — what the downstream adds on top of the upstream
9. **SF-Maintained Dependency Forks** — repos from `deps` category in repos.yaml, why they're forked and what changes SF maintains
10. **Notable Shared Dependencies** — `cluster-lifecycle-api` and other cross-repo deps not owned by SF but used by multiple SF repos
11. **Go Module Dependency Flow Diagram** — Mermaid diagram of actual dependency layers from go.mod analysis, including `cluster-lifecycle-api` and dep fork edges
12. **Deployment Topology Diagram** — Mermaid diagram based on actual `backplane-operator` chart structure: which toggle/always charts deploy which components. Verify against `pkg/templates/charts/toggle/` directory
13. **Runtime Integration Flow Diagram** — Mermaid `graph LR` showing which controllers watch which CRDs, what creates what, hub vs managed cluster side
14. **Architectural Observations** — structural insights: no circular deps, blast radius of `api`, heaviest consumer, deployment root, RBAC distribution pipeline
15. **Branch Convention Summary** — MCE uses `backplane-*`, ACM uses `release-*`, upstream uses `main`/tags
16. **Summary Matrix** — compact table of all repos
17. **Regeneration instructions** — how to regenerate this file, noting it reads repos.yaml dynamically

#### Diagram Style Guidelines

- Use `classDef` with named color classes instead of inline `style` per node
- Color scheme: blue (#e1f5fe/#0288d1) for upstream-only, green (#c8e6c9/#388e3c or #e8f5e9/#388e3c) for paired, orange (#fff3e0/#f57c00) for downstream-only, yellow (#ffecb3/#ff8f00) for operators, purple (#f3e5f5/#7b1fa2) for shared deps/forks
- Use `<br/>` and `<i>` tags in node labels for multi-line descriptions
- Use edge labels (e.g., `-->|"label"|`) to describe relationships
- Use `graph TD` for dependency/deployment diagrams, `graph LR` for runtime flow

### Step 6: Verify against cloned repos

**Do NOT skip this step.** Before cleanup, verify EVERY claim in the generated file against the actual cloned repos:

1. **Repo list completeness** — confirm every repo from repos.yaml `server-foundation` + `deps` appears in the generated file
2. **Module paths** — confirm each module path matches go.mod line 1
3. **Binary counts** — confirm cmd/ directory listing matches stated binary count for each repo
4. **go.mod dependencies** — confirm each dependency arrow in diagrams matches an actual go.mod require line
5. **Deployment chart mapping** — confirm which backplane-operator toggle chart contains each component by checking `pkg/templates/charts/toggle/*/templates/`
6. **Paired repo identity** — confirm upstream and downstream copies share the same Go module path
7. **cluster-lifecycle-api consumers** — confirm which repos import it via go.mod
8. **Dep fork verification** — confirm the forked repos (apiserver-network-proxy, grpc-go) exist and check what they fork

If ANY claim is wrong, fix the generated file and re-verify. **Loop until everything passes.**

### Step 7: Cleanup

Remove the temp directory:

```bash
rm -rf "${WORK_DIR}"
```

## Notes

- This file is **generated** — regenerate when repos change, don't hand-edit
- The repo list comes from `repos/repos.yaml` — when repos are added/removed there, regenerating this file will automatically reflect the changes
- The temp clones are discarded after analysis; the agent's `repos/` directory is not used (it may be stale or absent)
- The older `docs/repo-dependencies.md` and `docs/repo-deps/` files are marked as outdated and point to `SF-REPO-ARCHITECTURE.md`
