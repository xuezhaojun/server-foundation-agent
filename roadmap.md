# Server Foundation Agent - Roadmap

Planned features and improvements. Items are roughly prioritized.

---

## 1. Integrate Google Workspace CLI

Integrate GWS CLI to enable agent interaction with Google Workspace (Gmail, Calendar, Drive, Docs). Opens up workflows like reading team emails, scheduling, and document collaboration.

## 2. Build Jira Daily Report Workflow + CronJob

Create a workflow that generates a daily Jira status report for the SF team and deploy it as a CronJob on the cluster. Automates the daily standup prep — team members see what changed overnight without manual checking.

## 3. Knowledge Base: Workflows & Solutions

Long-term, ongoing effort to build, maintain, and update the agent's knowledge base — `solutions/`, `workflows/`, and `docs/`. The more domain knowledge the agent has, the more autonomously it can operate. Includes documenting common debugging patterns, release procedures, CI/CD recipes, and team conventions.
