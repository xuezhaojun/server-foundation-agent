---
name: sfa-solution-add
description: "Add a new solution (error-notebook entry) to solutions/. Use this skill when a problem was hard to diagnose and the fix should be recorded for future reference. Automatically scans for credentials and formats for grep discoverability. Trigger phrases: 'add solution', 'new solution', 'save this as a solution', 'record this fix', 'submit solution'."
---

# Add Solution

Create a new solution file in `solutions/` following the error-notebook format.

## Qualification Check

Before creating, confirm the problem meets at least 2 of these criteria:
- Took significant effort to diagnose or fix
- Is likely to recur (other repos, branches, environments)
- Has a non-obvious root cause the agent would struggle to rediscover
- Error messages are misleading or point away from the real cause

**Reject if** the problem is:
- A general how-to or workflow (→ belongs in `workflows/`)
- A basic capability or tool usage (→ belongs in `.claude/skills/`)
- Trivially googleable or well-documented upstream

## Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| problem | Yes | - | Description of the problem — what went wrong, error messages |
| root_cause | Yes | - | Why it happened — the non-obvious explanation |
| fix | Yes | - | How it was fixed — commands, config changes, code changes |
| versions | No | "All ACM/MCE versions" | Affected version range |
| references | No | - | Jira issues, PRs, Slack threads |

If the user gives a free-form description instead of structured parameters, extract the above from context.

## Workflow

### Step 1: Credential Scan (CRITICAL)

Scan ALL input content for sensitive data before writing anything:

```
Patterns to detect and STRIP:
- AWS access keys: AKIA[0-9A-Z]{16}
- AWS secret keys: [0-9a-zA-Z/+]{40}
- Bearer tokens: Bearer [a-zA-Z0-9\-._~+/]+=*
- Base64-encoded secrets: large base64 blocks in secret/credential context
- Pull secrets: auths.*auth.*dockerconfigjson
- Registry credentials: quay.io/docker.io auth tokens
- API keys: any key=<long-alphanumeric-string> patterns
- Kubeconfig with embedded certs/tokens
- Passwords in plaintext
```

**If credentials found:** replace with placeholders (`<YOUR-TOKEN>`, `<AWS-ACCESS-KEY>`, `$TOKEN`, etc.) and warn the user.

### Step 2: Generate filename

Derive a kebab-case filename from the problem:
- Use the core component + symptom pattern
- Example: `cluster-proxy-websocket-403`, `import-klusterlet-validation-error`
- Check `solutions/` for duplicates — if a similar solution exists, update it instead

### Step 3: Write the solution file

Create `solutions/<filename>.md` with this exact structure:

```markdown
---
title: <short descriptive title>
symptom: "<exact error message or observable behavior — grep-friendly>"
keywords: [<keyword1>, <keyword2>, ...]
affected_versions: "<version range>"
last_verified: <today's date YYYY-MM-DD>
status: active
---

## Symptom

<What the error looks like — exact error messages, failing commands, observable behavior.
Include enough literal text for grep matching.>

## Root Cause

<Why it happens — the non-obvious explanation.>

## Fix

<Step-by-step resolution. Include commands, code snippets, or config changes.>

## References

<Links to Jira issues, PRs, Slack threads, or docs.>
```

**Keyword selection tips** (for grep discoverability):
- Include the exact error code or message fragment
- Include the component name (e.g., `cluster-proxy`, `import-controller`)
- Include the tool or command that triggers the error (e.g., `kubectl`, `oc`, `go build`)
- Include the symptom verb (e.g., `403`, `timeout`, `stuck`, `flapping`)

### Step 4: Update the Solution Catalog

Read `solutions/README.md` and add a row to the Solution Catalog table:

```markdown
| [<filename>](<filename>.md) | <one-line description> |
```

### Step 5: Confirm with user

Show the user:
1. The generated filename
2. The frontmatter (title, symptom, keywords)
3. Whether any credentials were stripped
4. Ask if they want to commit now or make edits first
