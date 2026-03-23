# GitHub Projects V2 API Reference

Canonical reference for all `sfa-project-*` skills. Contains project board metadata, field IDs, CLI commands, and GraphQL examples.

Dashboard: <https://github.com/orgs/stolostron/projects/9>

## Project Board Info

| Property       | Value                              |
|----------------|------------------------------------|
| Owner          | stolostron                         |
| Project Number | 9                                  |
| Project ID     | PVT_kwDOA5awWc4BSgim              |
| Title          | server foundation agent tasks kanban |

## Field ID Mapping

All `sfa-project-*` skills depend on these IDs to read and update project item fields. IDs are stable and do not change unless the field is deleted and recreated.

### Single-Select Fields (with Option IDs)

#### Status

Field ID: `PVTSSF_lADOA5awWc4BSgimzhABWLU`

| Option      | Option ID    | Description |
|-------------|--------------|-------------|
| Backlog     | `7582c76d`   | Not yet started |
| In progress | `f33d0676`   | Agent is working on this task |
| In review   | `196397cb`   | Agent done, waiting for human supervisor review |
| Done        | `2a255443`   | Reviewed and completed |

#### Priority

Field ID: `PVTSSF_lADOA5awWc4BSgimzhABWTk`

| Option | Option ID    |
|--------|--------------|
| P0     | `79628723`   |
| P1     | `0a877460`   |
| P2     | `da944a9c`   |

#### Size

Field ID: `PVTSSF_lADOA5awWc4BSgimzhABWTo`

| Option | Option ID    |
|--------|--------------|
| XS     | `6c6483d2`   |
| S      | `f784b110`   |
| M      | `7515a9f1`   |
| L      | `817d0097`   |
| XL     | `db339eb2`   |

### Other Fields

**Convention:** The **Assignees** field represents the **human supervisor** — the person who oversees, reviews, and approves the agent's work on each item. The agent is always the executor; the assignee is the human in the loop.

| Field               | Field ID                                  | Type       |
|---------------------|-------------------------------------------|------------|
| Title               | `PVTF_lADOA5awWc4BSgimzhABWLM`           | Text       |
| Assignees           | `PVTF_lADOA5awWc4BSgimzhABWLQ`           | Assignees  | **Human Supervisor** — the person responsible for reviewing and approving the agent's work on this item |
| Labels              | `PVTF_lADOA5awWc4BSgimzhABWLY`           | Labels     |
| Linked PRs          | `PVTF_lADOA5awWc4BSgimzhABWLc`           | Linked PRs |
| Milestone           | `PVTF_lADOA5awWc4BSgimzhABWLg`           | Milestone  |
| Repository          | `PVTF_lADOA5awWc4BSgimzhABWLk`           | Repository |
| Reviewers           | `PVTF_lADOA5awWc4BSgimzhABWLs`           | Reviewers  |
| Parent issue        | `PVTF_lADOA5awWc4BSgimzhABWLw`           | Parent     |
| Sub-issues progress | `PVTF_lADOA5awWc4BSgimzhABWL0`           | Progress   |
| Estimate            | `PVTF_lADOA5awWc4BSgimzhABWTs`           | Number     |
| Start date          | `PVTF_lADOA5awWc4BSgimzhABWTw`           | Date       |
| Target date         | `PVTF_lADOA5awWc4BSgimzhABWT0`           | Date       |

## gh project CLI Reference

All commands below use project number `9` and owner `stolostron`.

### Create a draft issue

```bash
gh project item-create 9 --owner stolostron --title "Task title" --body "Task description"
```

Returns the new item ID (e.g., `PVTI_...`).

### List items

```bash
gh project item-list 9 --owner stolostron --format json
```

### Add an existing issue or PR to the project

```bash
gh project item-add 9 --owner stolostron --url https://github.com/stolostron/repo/issues/123
```

### Update a single-select field (Status, Priority, Size)

```bash
gh project item-edit --id <item-id> \
  --field-id PVTSSF_lADOA5awWc4BSgimzhABWLU \
  --project-id PVT_kwDOA5awWc4BSgim \
  --single-select-option-id f33d0676
```

The example above sets Status to "In progress".

### Update a text field

```bash
gh project item-edit --id <item-id> \
  --field-id PVTF_lADOA5awWc4BSgimzhABWLM \
  --project-id PVT_kwDOA5awWc4BSgim \
  --text "Updated title"
```

### Update a date field

```bash
gh project item-edit --id <item-id> \
  --field-id PVTF_lADOA5awWc4BSgimzhABWTw \
  --project-id PVT_kwDOA5awWc4BSgim \
  --date "2026-04-01"
```

### Update a number field

```bash
gh project item-edit --id <item-id> \
  --field-id PVTF_lADOA5awWc4BSgimzhABWTs \
  --project-id PVT_kwDOA5awWc4BSgim \
  --number 5
```

### Archive an item

```bash
gh project item-archive 9 --owner stolostron --id <item-id>
```

### Delete an item

```bash
gh project item-delete 9 --owner stolostron --id <item-id>
```

### List project fields

```bash
gh project field-list 9 --owner stolostron --format json
```

Useful for discovering field IDs and option IDs when the project schema changes.

## GraphQL API Examples

Use GraphQL when the CLI does not cover an operation or when you need to query item field values.

### Query items with field values

```graphql
query {
  organization(login: "stolostron") {
    projectV2(number: 9) {
      items(first: 50) {
        nodes {
          id
          content {
            ... on Issue {
              title
              url
            }
            ... on DraftIssue {
              title
            }
          }
          fieldValues(first: 20) {
            nodes {
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                field { ... on ProjectV2SingleSelectField { name } }
              }
              ... on ProjectV2ItemFieldTextValue {
                text
                field { ... on ProjectV2Field { name } }
              }
              ... on ProjectV2ItemFieldDateValue {
                date
                field { ... on ProjectV2Field { name } }
              }
              ... on ProjectV2ItemFieldNumberValue {
                number
                field { ... on ProjectV2Field { name } }
              }
            }
          }
        }
      }
    }
  }
}
```

### Create a draft issue (mutation)

```graphql
mutation {
  addProjectV2DraftIssue(input: {
    projectId: "PVT_kwDOA5awWc4BSgim"
    title: "Task title"
    body: "Task description"
  }) {
    projectItem {
      id
    }
  }
}
```

### Update a field value (mutation)

```graphql
mutation {
  updateProjectV2ItemFieldValue(input: {
    projectId: "PVT_kwDOA5awWc4BSgim"
    itemId: "PVTI_..."
    fieldId: "PVTSSF_lADOA5awWc4BSgimzhABWLU"
    value: { singleSelectOptionId: "f33d0676" }
  }) {
    projectV2Item {
      id
    }
  }
}
```

For text fields use `value: { text: "..." }`, for date fields use `value: { date: "YYYY-MM-DD" }`, and for number fields use `value: { number: N }`.

### Run a GraphQL query via gh CLI

```bash
gh api graphql -f query='{ ... }'
```

## API Constraints

- **One field per mutation.** Each `updateProjectV2ItemFieldValue` call updates exactly one field. To set Status, Priority, and Size on a single item, make three separate calls.
- **No dynamic option creation.** Single-select options (Status, Priority, Size values) cannot be added via the API. They must be created in the project settings UI first.
- **Max 50 fields per project.** Hard limit on the number of custom fields.
- **Rate limits.** GitHub GraphQL API allows 5000 points per hour. Each query or mutation costs at least 1 point. Complex queries with nested pagination cost more.
- **Draft issues have no repo.** Draft issues created via `item-create` or `addProjectV2DraftIssue` are lightweight items not associated with any repository. Convert them to real issues when they need tracking in a repo.
