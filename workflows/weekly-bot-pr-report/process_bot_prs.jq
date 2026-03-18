# process_bot_prs.jq — Phase 2: Filter raw PRs to open bot PRs
#
# Usage:
#   jq --argjson today_sec $(date +%s) -f workflows/weekly-bot-pr-report/process_bot_prs.jq <raw_prs.json>
#
# Input:  Raw JSON array from fetch-prs skill (detail level: all)
# Output: Filtered array of open bot PRs with flat fields

def is_konflux_bot:
  .login == "red-hat-konflux";

def days_since_created:
  ($today_sec - (.content.createdAt | fromdateiso8601 | floor)) / 86400 | floor;

def extract_branch:
  # Try to extract branch from PR title parentheses, e.g., "Update x/crypto (backplane-2.9)"
  # Fall back to head branch ref name
  if (.content.title | test("\\(([^)]+)\\)\\s*$")) then
    .content.title | capture("\\((?<branch>[^)]+)\\)\\s*$") | .branch
  elif .content.headRefName then
    .content.headRefName
  else
    "unknown"
  end;

def is_stolostron_org:
  .content.repository.nameWithOwner | startswith("stolostron/");

def has_ai_ignore_label:
  any(.content.labels.nodes[]?; .name == "ai-ignore");

map(select(.content.state == "OPEN" and (.content.author | is_konflux_bot) and is_stolostron_org and (has_ai_ignore_label | not))) |
map(
  .age_days = days_since_created |
  .author = (.content.author.login // "unknown") |
  .repo = .content.repository.nameWithOwner |
  .short_repo = (.content.repository.nameWithOwner | sub("^[^/]+/"; "")) |
  .title = .content.title |
  .url = .content.url |
  .number = .content.number |
  .branch = extract_branch |
  .is_fork = (.content.isCrossRepository // false)
)
