# process_prs.jq — Phase 2: Filter and classify PRs
#
# Usage:
#   jq --argjson today_sec $(date +%s) -f workflows/weekly-pr-report/process_prs.jq <raw_prs.json>
#
# Input:  Raw JSON array from fetch-prs (open PRs from SF stolostron repos)
# Output: Filtered array of open human PRs with category, staleness, and flat fields

def is_bot:
  .login as $l |
  ($l == "red-hat-konflux" or $l == "app/red-hat-konflux" or $l == "dependabot" or $l == "app/dependabot" or $l == "renovate" or $l == "app/renovate" or ($l | endswith("[bot]")) or ($l | endswith("-bot")));

def has_label($label):
  .labels | map(.name) | index($label) != null;

def has_approved:
  .reviewDecision == "APPROVED" or has_label("approved");

def has_lgtm:
  has_label("lgtm");

def has_do_not_merge:
  .labels | map(.name) | any(startswith("do-not-merge/"));

# Count comments from users other than the PR author
def non_author_comment_count:
  (.author.login // "unknown") as $author |
  [(.comments // [])[] | select(.author.login != null and .author.login != $author)] | length;

def days_since:
  ($today_sec - (.updatedAt | fromdateiso8601 | floor)) / 86400 | floor;

def staleness(days):
  if days <= 2 then "Fresh"
  elif days <= 7 then "Normal"
  elif days <= 14 then "Aging"
  elif days <= 30 then "Stale"
  elif days <= 90 then "Very Stale"
  else "Abandoned"
  end;

def get_category:
  if has_approved and has_lgtm and (has_do_not_merge | not) and .isDraft == false and .mergeable == "MERGEABLE" then
    "Ready to Merge"
  elif .isDraft == true or has_label("do-not-merge/work-in-progress") then
    "Work In Progress"
  elif has_label("do-not-merge/hold") then
    "On Hold"
  elif has_label("needs-rebase") or .mergeable == "CONFLICTING" then
    "Needs Rebase"
  elif has_approved and (has_lgtm | not) and (has_do_not_merge | not) then
    "Approved, Needs LGTM"
  else
    "Needs Review"
  end;

map(select(.state == "OPEN" and (.author | is_bot | not))) |
map(
  .days = days_since |
  .staleness = staleness(.days) |
  .category = get_category |
  # IMPORTANT: feedback_count must be computed before .author is flattened to a string
  .feedback_count = non_author_comment_count |
  .author = (.author.login // "unknown") |
  .repo = (.repository.nameWithOwner | sub("^[^/]+/"; "")) |
  .title = .title |
  .url = .url |
  .number = .number |
  .mergeable = .mergeable |
  .has_feedback = (.feedback_count > 0)
)
