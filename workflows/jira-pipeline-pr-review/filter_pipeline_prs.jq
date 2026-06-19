# filter_pipeline_prs.jq — Keep open jira-pipeline PRs (acm-agent + sfa-assisted + ACM title)
#
# Usage:
#   jq -f workflows/jira-pipeline-pr-review/filter_pipeline_prs.jq <raw_prs.json>
#
# Input:  Raw JSON array from fetch-prs.sh (detail level: all)
# Output: JSON array of flattened pipeline PR objects (non-draft only)
#
# Identity uses author + label + title — not strict branch shape. Branch variants
# (fix/ACM-*, fix-ACM-*-v2) are documented but not required for inclusion.

def is_acm_agent:
  (.login // "") == "acm-agent"
  or (.login // "") == "app/acm-agent"
  or ((.login // "") | test("^acm-agent"));

def has_label($name):
  any(.labels[]?; .name == $name);

def jira_key:
  if (.title | test("ACM-[0-9]+")) then
    (.title | capture("(?<key>ACM-[0-9]+)") | .key)
  else
    null
  end;

def branch_style:
  if ((.headRefName // "") | test("^(sfa/)?fix-ACM-[0-9]+([-.][a-zA-Z0-9]+)*$")) then
    "canonical"
  elif ((.headRefName // "") | test("^(sfa/)?fix/ACM-[0-9]+([-.][a-zA-Z0-9]+)*$")) then
    "slash-variant"
  else
    "other"
  end;

def is_pipeline_pr:
  (.author | is_acm_agent)
  and has_label("sfa-assisted")
  and (.title | test("ACM-[0-9]+"));

def flatten_pr:
  {
    number: .number,
    url: .url,
    title: .title,
    repo: .repository.nameWithOwner,
    short_repo: (.repository.nameWithOwner | sub("^[^/]+/"; "")),
    author: (.author.login // "unknown"),
    branch: (.headRefName // "unknown"),
    branch_style: branch_style,
    created_at: .createdAt,
    jira_key: jira_key,
    is_draft: (.isDraft // false),
    review_decision: (.reviewDecision // "NONE"),
    mergeable: (.mergeable // "UNKNOWN"),
    labels: [(.labels[]?.name)?]
  };

[.[]
  | select(.state == "OPEN")
  | select(.isDraft == false)
  | select(is_pipeline_pr)
  | flatten_pr
]
