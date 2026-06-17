# filter_agent_prs.jq — Classify open acm-agent PRs needing human action
#
# Usage:
#   jq --argjson today_sec $(date +%s) -f workflows/agent-pr-action-needed/filter_agent_prs.jq <raw_prs.json>
#
# Input:  Raw JSON array from fetch-prs.sh (detail level: all)
# Output: JSON object { draft_ready_for_review: [...], awaiting_approval: [...] }

def is_acm_agent:
  (.login // "") == "acm-agent"
  or (.login // "") == "app/acm-agent"
  or ((.login // "") | test("^acm-agent"));

def has_label($name):
  any(.labels[]?; .name == $name);

def days_since_created:
  ($today_sec - (.createdAt | fromdateiso8601 | floor)) / 86400 | floor;

def jira_key:
  if (.title | test("ACM-[0-9]+")) then
    (.title | capture("(?<key>ACM-[0-9]+)") | .key)
  else
    null
  end;

def is_agent_pr:
  (.author | is_acm_agent)
  or has_label("sfa-assisted")
  or ((.headRefName // "") | test("^(sfa/)?fix-ACM-[0-9]+$"));

def needs_ok_to_test:
  has_label("needs-ok-to-test");

def flatten_pr:
  {
    number: .number,
    url: .url,
    title: .title,
    repo: .repository.nameWithOwner,
    short_repo: (.repository.nameWithOwner | sub("^[^/]+/"; "")),
    author: (.author.login // "unknown"),
    branch: (.headRefName // "unknown"),
    age_days: days_since_created,
    jira_key: jira_key,
    is_draft: (.isDraft // false),
    review_decision: (.reviewDecision // "NONE"),
    mergeable: (.mergeable // "UNKNOWN"),
    needs_ok_to_test: needs_ok_to_test,
    labels: [(.labels[]?.name)?]
  };

[.[] | select(.state == "OPEN" and is_agent_pr) | flatten_pr] as $agent_prs
| {
    draft_ready_for_review: [
      $agent_prs[] | select(.is_draft == true)
      | . + {action: (
          if .needs_ok_to_test then
            "Mark *Ready for review*, then comment `/ok-to-test` (Prow requires org-member approval before CI runs)"
          else
            "Mark *Ready for review* so reviewers and CI can proceed"
          end
        )}
    ],
    awaiting_approval: [
      $agent_prs[] | select(.is_draft == false and .review_decision == "REVIEW_REQUIRED")
      | . + {action: (
          if .needs_ok_to_test then
            "Comment `/ok-to-test`, then *Approve* the PR (reviews and CI gate merge)"
          else
            "*Approve* the PR — code is ready for review but lacks required approval"
          end
        )}
    ]
  }
