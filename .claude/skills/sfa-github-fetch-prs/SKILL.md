---
name: sfa-github-fetch-prs
description: "Fetch/Get/View all active(open) pull requests of sf(server foundation) team. For example: `How many sf PRs opened today?` sometimes user may omit `sf`, directly say `How many PRs opened today?`, if user's context does not contain any other PR related information, then it is assumed that the user intends to query the PRs of the sf team."
---

# Fetch PRs Skill

This skill fetches all open Pull Requests from SF stolostron downstream repos using `gh pr list` per repo. The repo list comes from `repos/repos.yaml` → `repos.server-foundation.stolostron`.

## When to Use This Skill

Use this skill when the user requests to:

- View all PRs of server foundation
- Analyze PR statistics (by state, repository, author, etc.)
- Filter PRs by criteria (state, repository, labels, etc.)
- Generate reports about PRs
- Perform batch operations on PRs

## Usage Instructions

### Basic Usage

Fetch PR data using the script:

```bash
fetch-prs.sh detailed
```

MUST make sure you're in the same directory as the `fetch-prs.sh` script.

This returns a JSON array of all open PRs with comprehensive information.

### Detail Levels

Choose the appropriate detail level based on user needs:

#### 1. **basic** (Minimal Information)

Returns only essential PR identification data:

- `url` - PR link
- `number` - PR number
- `state` - PR status (OPEN/MERGED/CLOSED)
- `author.login` - Author username
- `headRefName` - Head branch name
- `repository.nameWithOwner` - Repository full name (added by script)

**Use when:** Quick PR list viewing, minimal API overhead needed

#### 2. **detailed** (Recommended)

Extends basic with human-readable context:

- All basic fields
- `title` - PR title
- `createdAt` - Creation timestamp
- `updatedAt` - Last update timestamp
- `labels` - Array of label objects `[{name: "..."}]`

**Use when:** Statistical analysis, report generation, understanding PR content and timeline

#### 3. **all** (Complete Information)

Includes full PR lifecycle and review data:

- All detailed fields
- `mergedAt` - Merge timestamp
- `closedAt` - Close timestamp
- `assignees` - Array of assignee objects
- `comments` - Array of comment objects
- `reviewDecision` - Review status (APPROVED/CHANGES_REQUESTED/REVIEW_REQUIRED)
- `isDraft` - Draft status
- `mergeable` - Merge capability status (MERGEABLE/CONFLICTING/UNKNOWN)
- `isCrossRepository` - Whether PR is from a fork

**Use when:** Deep analysis, automation decisions, understanding review workflow and merge readiness

### Caching Behavior

- Cache files stored in system temporary directory (e.g., `/tmp/sf-fetch-prs-<user>/`)
- Default TTL: 300 seconds (5 minutes)
- Cache file format: `$TMPDIR/sf-fetch-prs-$USER/prs_sf_<detail_level>.json`

**Cache Control**:

- Use cached data by default (fast, no API calls)
- Force fresh fetch: `$SCRIPT detailed nocache`
- Custom TTL: `CACHE_TTL=600 $SCRIPT detailed`

## Output Format

The script returns a JSON array where each item is a flat PR object:

```json
{
  "url": "https://github.com/stolostron/ocm/pull/123",
  "number": 123,
  "title": "PR title",
  "state": "OPEN",
  "createdAt": "2025-01-01T00:00:00Z",
  "updatedAt": "2025-01-01T00:00:00Z",
  "author": {
    "login": "username"
  },
  "repository": {
    "nameWithOwner": "stolostron/ocm"
  },
  "labels": [
    { "name": "bug" },
    { "name": "priority-high" }
  ]
}
```

## Best Practices

- **Use "detailed" level by default** - good balance of information vs API cost
- **Use "all" level only when** user needs review status, assignees, or mergeable state

## Error Handling

- Check if script exists before running
- Verify gh CLI is authenticated
- Handle empty results gracefully
- If a repo fails to fetch, the script logs a warning and continues with remaining repos
