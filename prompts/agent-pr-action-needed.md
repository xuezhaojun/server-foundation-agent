# SF agent PR action reminder (agent-swarm)

List open PRs authored by **`acm-agent[bot]`** that need human action after
`jira-pipeline.md` (or `jira-solve.md`) creates a draft fix, then notify the
Server Foundation Slack channel.

Designed for **non-interactive** scheduled runs (weekday cron, after pipeline slots).
Detailed reference: `workflows/agent-pr-action-needed.md`.

## Why this exists

`jira-pipeline` intentionally leaves PRs in **draft** and does not merge or mark
them ready. On stolostron repos, bot PRs also get **`needs-ok-to-test`** until an
org member comments `/ok-to-test`. Humans must:

1. **Draft PRs** — mark *Ready for review* (and `/ok-to-test` when labeled)
2. **Non-draft PRs** — *Approve* when review looks good (`reviewDecision: REVIEW_REQUIRED`)

This prompt collects those PRs and posts a Slack digest. It does **not** change
GitHub state.

## SFA conventions

**Working directory:** `/workspace/server-foundation-agent`

**GitHub:** `gh` only. Fetch SF open PRs via bundled `fetch-prs.sh` (`all` detail).
Filter/classify with bundled jq + Python scripts under
`workflows/agent-pr-action-needed/`.

**Slack:** `SLACK_WEBHOOK_URL` + `.claude/skills/sfa-slack-notify/send_to_slack.sh`

**Output dir:** `.output/agent-pr-action-needed/`

**Agent PR signals** (any of):

- Author `acm-agent` / `app/acm-agent`
- Label `sfa-assisted`
- Head branch `fix-ACM-*` or `sfa/fix-ACM-*`

Extended conventions: `prompts/_sfa-conventions.md`

## Workflow

```
Collect → Classify → Slack → Summary
```

## Phase 1: Collect open PRs

```bash
mkdir -p .output/agent-pr-action-needed

bash .claude/skills/sfa-github-fetch-prs/fetch-prs.sh all \
  > .output/agent-pr-action-needed/raw_prs.json
```

Requires `gh` auth and `yq` (same as fetch-prs skill).

## Phase 2: Classify PRs needing action

```bash
jq --argjson today_sec "$(date +%s)" \
  -f workflows/agent-pr-action-needed/filter_agent_prs.jq \
  .output/agent-pr-action-needed/raw_prs.json \
  > .output/agent-pr-action-needed/classified_prs.json
```

Output schema:

| Bucket | Criteria | Human action |
|--------|----------|--------------|
| `draft_ready_for_review` | `isDraft` | Mark ready; `/ok-to-test` if `needs-ok-to-test` |
| `awaiting_approval` | not draft, `reviewDecision == REVIEW_REQUIRED` | Approve (and `/ok-to-test` if still labeled) |

PRs with `reviewDecision: CHANGES_REQUESTED` are **excluded** — the author must
address feedback first, not approve.

## Phase 3: Build Slack payload

```bash
python3 workflows/agent-pr-action-needed/generate_slack_payload.py \
  .output/agent-pr-action-needed/classified_prs.json \
  .output/agent-pr-action-needed/slack_payload.json
```

## Phase 4: Send Slack

```bash
bash .claude/skills/sfa-slack-notify/send_to_slack.sh \
  .output/agent-pr-action-needed/slack_payload.json
```

- Skip Phase 4 if `SLACK_WEBHOOK_URL` is unset — log a warning in the final summary
- **Always send** when the webhook is set, even if both buckets are empty (confirms
  the job ran)

## Final summary

Report:

- Total agent PRs scanned (from raw fetch)
- Count in each bucket with PR numbers and repos
- Slack delivery status
- Any fetch/classify errors (repos skipped, etc.)

## instruction_prompt overrides

| Text | Effect |
|------|--------|
| `SKIP_SLACK` | Skip Phase 4 |
| `nocache` | Pass `nocache` to `fetch-prs.sh` for a fresh GitHub fetch |
| `author <login>` | Override author filter in jq (edit run notes only — default `acm-agent`) |

## Do not

- Ask the user for confirmation (automated mode)
- Mark PRs ready for review, comment `/ok-to-test`, approve, merge, or close PRs
- Modify Jira issues
- Process more than listing + notification in this run
