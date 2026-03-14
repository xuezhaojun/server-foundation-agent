---
name: fetch-prs
description: "Fetch/Get/View all active(open) pull requests of sf(server foundation) team. For example: `How many sf PRs opened today?` sometimes user may omit `sf`, directly say `How many PRs opened today?`, if user's context does not contain any other PR related information, then it is assumed that the user intends to query the PRs of the sf team."
---

# Fetch PRs Skill

This skill provides efficient access to all Pull Requests managed in a GitHub Project board using the optimized `fetch-prs.sh` script.

## When to Use This Skill

Use this skill when the user requests to:

- View all PRs of server foudation
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

This returns a JSON array of all PRs with comprehensive information.

### Detail Levels

Choose the appropriate detail level based on user needs:

#### 1. **basic** (Minimal Information)

Returns only essential PR identification data:

- `url` - PR link
- `number` - PR number
- `state` - PR status (OPEN/MERGED/CLOSED)
- `repository.nameWithOwner` - Repository full name

**Use when:** Quick PR list viewing, minimal API overhead needed

#### 2. **detailed** (Recommended)

Extends basic with human-readable context:

- All basic fields
- `title` - PR title
- `createdAt` - Creation timestamp
- `updatedAt` - Last update timestamp
- `author.login` - Author username
- `labels` - First 10 labels

**Use when:** Statistical analysis, report generation, understanding PR content and timeline

#### 3. **all** (Complete Information)

Includes full PR lifecycle and review data:

- All detailed fields
- `mergedAt` - Merge timestamp
- `closedAt` - Close timestamp
- `assignees` - First 10 assignees
- `reviewDecision` - Review status (APPROVED/CHANGES_REQUESTED/REVIEW_REQUIRED)
- `isDraft` - Draft status
- `mergeable` - Merge capability status

**Use when:** Deep analysis, automation decisions, understanding review workflow and merge readiness

### Caching Behavior

- Cache files stored in system temporary directory (e.g., `/tmp/sf-claude-code-plugins-fetch-prs-<user>/`)
- Default TTL: 300 seconds (5 minutes)
- Cache automatically cleans up on system restart
- Cache file format: `$TMPDIR/sf-claude-code-plugins-fetch-prs-$USER/prs_stolostron_8_<detail_level>.json`

**Cache Control**:

- Use cached data by default (fast, no API calls)
- Force fresh fetch: `$SCRIPT detailed nocache`
- Custom TTL: `CACHE_TTL=600 $SCRIPT detailed`

## Output Format

The script returns a JSON array where each item has:

```json
{
  "id": "PROJECT_ITEM_ID",
  "content": {
    "url": "https://github.com/org/repo/pull/123",
    "number": 123,
    "title": "PR title",
    "state": "OPEN|MERGED|CLOSED",
    "createdAt": "2025-01-01T00:00:00Z",
    "updatedAt": "2025-01-01T00:00:00Z",
    "author": {
      "login": "username"
    },
    "repository": {
      "nameWithOwner": "org/repo"
    },
    "labels": {
      "nodes": [{ "name": "bug" }, { "name": "priority-high" }]
    }
  }
}
```

## Best Practices

- **Use "detailed" level by default** - good balance of information vs API cost
- **Use "all" level only when** user needs review status, assignees, or mergeable state

## Error Handling

- Check if script exists before running
- Verify gh CLI is authenticated
- Handle empty results gracefully
- Provide clear error messages if GraphQL query fails

## Cache Management

### Force Fresh Data (Recommended)

To force fetching the latest PR data and update the cache, use the `nocache` parameter:

ONLY do this if user explicitly requests it.

```bash
# Force refresh with detailed information
fetch-prs.sh detailed nocache

# Force refresh with all information
fetch-prs.sh all nocache

# Force refresh with basic information
fetch-prs.sh nocache
```

**Note**:

- Cache is automatically cleaned on system restart since it's stored in the temporary directory
- For security reasons, this skill cannot delete cache files automatically
- Using the `nocache` parameter is preferred over manual deletion

## Troubleshooting

If you encounter errors or issues when using the script, please refer to the [REQUIREMENTS.md](REQUIREMENTS.md) file to make sure all requirements are met.
