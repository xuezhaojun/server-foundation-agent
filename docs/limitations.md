# Server Foundation Agent - Known Limitations

This document tracks known capability gaps, access restrictions, and environmental limitations of the Server Foundation Agent. When you discover a new limitation, add it here so the team is aware.

## How to Add a Limitation

Add a new entry under the appropriate category with:
- **Title**: Short description of the limitation
- **Impact**: What the agent cannot do because of this
- **Workaround**: How users can work around it (if any)
- **Date discovered**: When this was first identified

---

## Access Restrictions

### 1. QE Jenkins Platform Inaccessible

- **URL**: `https://jenkins-csb-rhacm-tests.dno.corp.redhat.com/`
- **Impact**: When QE reports bugs, they often include links to detailed error logs on this internal Jenkins instance. The agent cannot access these logs because the platform sits behind Red Hat's corporate VPN (`*.dno.corp.redhat.com`), which the agent has no connectivity to.
- **Workaround**: Users must manually copy the relevant error logs or screenshots from Jenkins and paste them into the conversation or Jira issue so the agent can analyze them.
- **Date discovered**: 2026-03-23

---

## Capability Gaps

_(No entries yet. Add limitations related to missing features or unsupported workflows here.)_

---

## Environmental Constraints

_(No entries yet. Add limitations related to runtime environment, resource limits, or tooling here.)_
