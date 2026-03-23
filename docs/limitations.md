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

### 1. No Access to Downstream Test Environment or QE Test Clusters

- **Impact**: The agent cannot create downstream (RHACM/MCE) test environments or directly access QE's test clusters. This significantly slows down debugging and issue resolution — the agent cannot reproduce reported bugs in a real downstream environment, verify fixes end-to-end, or inspect cluster state when investigating QE-reported failures.
- **Workaround**: Users must either reproduce the issue on their own cluster and share logs/state with the agent, or grant the agent kubeconfig access to an existing test cluster. Having a dedicated always-on test cluster with agent access would greatly accelerate the debug-fix cycle.
- **Date discovered**: 2026-03-23
