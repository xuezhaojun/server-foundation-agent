# process_prs.jq — Phase 2: Filter and classify PRs
#
# Usage:
#   jq --argjson today_sec $(date +%s) -f workflows/weekly-pr-report/process_prs.jq <raw_prs.json>
#
# Input:  Raw JSON array from fetch-prs skill (detail level: all)
# Output: Filtered array of open human PRs with category, staleness, and flat fields

def is_bot:
  .login as $l |
  ($l == "red-hat-konflux" or $l == "dependabot" or $l == "renovate" or ($l | endswith("[bot]")) or ($l | endswith("-bot")));

def has_label($label):
  .content.labels.nodes | map(.name) | index($label) != null;

def has_approved:
  .content.reviewDecision == "APPROVED" or has_label("approved");

def has_lgtm:
  has_label("lgtm");

def has_do_not_merge:
  .content.labels.nodes | map(.name) | any(startswith("do-not-merge/"));

# Count comments from users other than the PR author
def non_author_comment_count:
  (.content.author.login // "unknown") as $author |
  [(.content.comments.nodes // [])[] | select(.author.login != null and .author.login != $author)] | length;

def days_since:
  ($today_sec - (.content.updatedAt | fromdateiso8601 | floor)) / 86400 | floor;

def staleness(days):
  if days <= 2 then "Fresh"
  elif days <= 7 then "Normal"
  elif days <= 14 then "Aging"
  elif days <= 30 then "Stale"
  elif days <= 90 then "Very Stale"
  else "Abandoned"
  end;

def get_category:
  if has_approved and has_lgtm and (has_do_not_merge | not) and .content.isDraft == false and .content.mergeable == "MERGEABLE" then
    "Ready to Merge"
  elif .content.isDraft == true or has_label("do-not-merge/work-in-progress") then
    "Work In Progress"
  elif has_label("do-not-merge/hold") then
    "On Hold"
  elif has_label("needs-rebase") or .content.mergeable == "CONFLICTING" then
    "Needs Rebase"
  elif has_approved and (has_lgtm | not) and (has_do_not_merge | not) then
    "Approved, Needs LGTM"
  else
    "Needs Review"
  end;

map(select(.content.state == "OPEN" and (.content.author | is_bot | not))) |
map(
  .days = days_since |
  .staleness = staleness(.days) |
  .category = get_category |
  .author = (.content.author.login // "unknown") |
  .repo = (.content.repository.nameWithOwner | sub("^[^/]+/"; "")) |
  .title = .content.title |
  .url = .content.url |
  .number = .content.number |
  .mergeable = .content.mergeable |
  .feedback_count = non_author_comment_count |
  .has_feedback = (.feedback_count > 0)
)
