# Jira Formatting Reference

Formatting syntax for Jira wiki markup (used with REST API v2 endpoints).

## Wiki Markup Syntax

| Format | Syntax | Example |
|--------|--------|---------|
| Bold | `*text*` | *bold text* |
| Italic | `_text_` | _italic text_ |
| Monospace | `{{text}}` | `code` |
| Link | `[title\|url]` | [PR\|https://github.com/...] |
| Heading | `h1.` to `h6.` | `h3. Section Title` |
| Unordered list | `* item` | bullet point |
| Ordered list | `# item` | numbered item |
| Horizontal rule | `----` | separator line |
| Code block | `{code}...{code}` | code block |
| Code block (lang) | `{code:java}...{code}` | syntax-highlighted code |

## Common Pitfalls

### Headers vs List Items

**WRONG** — using headers for list items:
```
h1. Investigated the route configuration
h1. Identified two routes
```

**CORRECT** — headers for sections, `#` for numbered lists:
```
h1. Actions Taken

# Investigated the route configuration
# Identified two routes
```

### Nested Lists

```
* Item 1
** Sub-item 1a
** Sub-item 1b
* Item 2
```

## API Version and Formatting

| API Version | Format | Use Case |
|------------|--------|----------|
| v2 (`/rest/api/2/`) | Wiki markup | Comments, descriptions (preferred) |
| v3 (`/rest/api/3/`) | ADF (Atlassian Document Format) | Search endpoint only |

**Rule**: Use v2 for all CRUD operations (comments, issue creation/updates) because wiki markup is simpler. Use v3 only for the search endpoint (`/rest/api/3/search/jql` POST).

## SFA Agent Signature

All agent-generated content must include a signature footer:

**For issue descriptions:**
```
<description text>

----
_Created by server-foundation-agent_
```

**For comments:**
```
<comment text>

----
_— server-foundation-agent_
```
