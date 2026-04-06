# process_bot_prs.jq — Phase 2: Filter raw PRs to open bot PRs
#
# Usage:
#   jq --argjson today_sec $(date +%s) -f workflows/weekly-bot-pr-hygiene/process_bot_prs.jq <raw_prs.json>
#
# Input:  Raw JSON array from fetch-prs (open PRs from SF stolostron repos)
# Output: Filtered array of bot PRs with flat fields

def is_konflux_bot:
  .login == "red-hat-konflux" or .login == "app/red-hat-konflux";

def days_since_created:
  ($today_sec - (.createdAt | fromdateiso8601 | floor)) / 86400 | floor;

def extract_branch:
  # Try to extract branch from PR title parentheses, e.g., "Update x/crypto (backplane-2.9)"
  # Fall back to head branch ref name
  if (.title | test("\\(([^)]+)\\)\\s*$")) then
    .title | capture("\\((?<branch>[^)]+)\\)\\s*$") | .branch
  elif .headRefName then
    .headRefName
  else
    "unknown"
  end;

def has_ai_ignore_label:
  any(.labels[]?; .name == "ai-ignore");

map(select(.state == "OPEN" and (.author | is_konflux_bot) and (has_ai_ignore_label | not))) |
map(
  .age_days = days_since_created |
  .author = (.author.login // "unknown") |
  .repo = .repository.nameWithOwner |
  .short_repo = (.repository.nameWithOwner | sub("^[^/]+/"; "")) |
  .title = .title |
  .url = .url |
  .number = .number |
  .branch = extract_branch |
  .is_fork = (.isCrossRepository // false)
)
