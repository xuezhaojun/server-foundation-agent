# Jira Issue Templates

Standard templates for creating issues in the ACM project. Used by `sfa-jira-create`.

## Bug Template

```
Summary: [<Component>] <Brief description of the bug>

Description:
h3. Problem

<What is happening? Include error messages, logs, or screenshots.>

h3. Expected Behavior

<What should happen instead?>

h3. Steps to Reproduce

# <Step 1>
# <Step 2>
# <Step 3>

h3. Environment

* ACM version: <e.g., 2.14.0>
* OCP version: <e.g., 4.17>
* Cluster type: <Hub / Managed / SNO>

----
_Created by server-foundation-agent_
```

Required fields: type=Bug, affects-version, fix-version, severity, activity-type=Quality / Stability / Reliability

## Epic Template

```
Summary: [<Component>] <Epic title>

Description:
h3. Goal

<What is the objective of this epic?>

h3. Acceptance Criteria

* <Criterion 1>
* <Criterion 2>
* <Criterion 3>

h3. Stories

* <Story 1 — brief description>
* <Story 2 — brief description>

h3. Dependencies

* <Any blockers or related epics>

----
_Created by server-foundation-agent_
```

Required fields: type=Epic, epic-name (customfield_10011 = summary), activity-type=Product / Portfolio Work

## Story Template

```
Summary: [<Component>] <Story title>

Description:
h3. User Story

As a <role>, I want <goal>, so that <benefit>.

h3. Acceptance Criteria

* <Criterion 1>
* <Criterion 2>

h3. Technical Notes

<Implementation details, if known>

----
_Created by server-foundation-agent_
```

Required fields: type=Story, affects-version, fix-version, activity-type=Product / Portfolio Work

## Task Template

```
Summary: [<Component>] <Task title>

Description:
h3. Objective

<What needs to be done?>

h3. Steps

# <Step 1>
# <Step 2>
# <Step 3>

h3. Done Criteria

* <How do we know this is complete?>

----
_Created by server-foundation-agent_
```

Required fields: type=Task, affects-version, fix-version, activity-type=Quality / Stability / Reliability

## Vulnerability Template

```
Summary: [<Component>] <CVE-ID or vulnerability description>

Description:
h3. Vulnerability

* CVE: <CVE-ID>
* CVSS Score: <score>
* Severity: <Critical/Important/Moderate/Low>

h3. Affected Component

* Repository: <repo name>
* Dependency: <affected package>

h3. Remediation

<Fix approach: upgrade dependency, patch, etc.>

----
_Created by server-foundation-agent_
```

Required fields: type=Vulnerability, affects-version, fix-version, severity, activity-type=Security & Compliance

## Template Usage Notes

1. Replace `<Component>` with the SF component name (e.g., cluster-proxy, managed-serviceaccount)
2. Templates are guidelines — adapt the description sections as needed
3. Always include the agent signature footer
4. Always add the `sfa-assisted` label
5. If the user provides a detailed description, use it instead of the template structure
