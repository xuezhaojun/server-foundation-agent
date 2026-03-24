# Jira Custom Fields Reference

Custom fields used in the ACM project on Red Hat Jira Cloud.

## Field Inventory

| Field | Field ID | Type | Required | Notes |
|-------|----------|------|----------|-------|
| Severity | `customfield_10840` | Option | No | Default: `Important` |
| Activity Type | `customfield_10464` | Option | **Yes** | Must be set on all issues |
| Epic Name | `customfield_10011` | String | Epic only | Required when creating Epics |
| Sprint | `customfield_10020` | JSON Array | No | Array of sprint objects |
| Git Pull Request | `customfield_10875` | String | No | GitHub PR URL smart-link |

## Severity Values

`customfield_10840` — option type, set via `{"value": "<name>"}`:

- `Critical`
- `Important` (default)
- `Moderate`
- `Low`
- `Informational`

## Activity Type Values

`customfield_10464` — option type, **required** for all issues. Set via `{"value": "<name>"}`.

### Auto-Mapping by Issue Type

| Issue Type | Default Activity Type |
|------------|----------------------|
| Bug | Quality / Stability / Reliability |
| Vulnerability | Security & Compliance |
| Story / Feature / Epic / Initiative | Product / Portfolio Work |
| Task | Quality / Stability / Reliability |
| Spike | Future Sustainability |

### All Valid Values

- Associate Wellness & Development
- Incidents & Support
- Security & Compliance
- Quality / Stability / Reliability
- Future Sustainability
- Product / Portfolio Work

## Sprint Field

`customfield_10020` — JSON array of sprint objects. To extract the current sprint name:

```python
sprint_field = fields.get('customfield_10020')
if sprint_field and isinstance(sprint_field, list) and len(sprint_field) > 0:
    sprint_name = sprint_field[-1].get('name', '')
```

## Version Format

Both `versions` (Affects Version) and `fixVersions` (Fix Version) are **required** fields.

Format: `MCE X.YY.Z` (e.g., `MCE 2.14.0`)

### Version Shortcuts (Natural Language)

- **"在 MCE 2.14.0 实现"** or **"for MCE 2.14.0"** → both versions = `MCE 2.14.0`
- **"MCE 2.13.0 发现的问题，2.14.0 fix"** → affects=`MCE 2.13.0`, fix=`MCE 2.14.0`
- **"found in 2.13, fix in 2.14"** → affects=`MCE 2.13.0`, fix=`MCE 2.14.0`

When only a single version is mentioned (not for a Bug), assume both are the same.

## CLI Limitation

The `jira` CLI tool does **not** support option-type custom fields (Severity, Activity Type) via the `--custom` flag. Always use the REST API directly for creating/updating issues with custom fields.
