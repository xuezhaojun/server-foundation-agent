# Deployment Guide

## Architecture

```
┌──────────────────────────────────────────────┐
│  server-foundation namespace                 │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │  AgentTemplate: server-foundation-     │  │
│  │  template (shared config blueprint)    │  │
│  └────────────────────────────────────────┘  │
│          ▲ templateRef                       │
│  ┌────────────────────────────────────────┐  │
│  │  Agent: server-foundation-agent        │  │
│  │  (always-running, auto-standby)        │  │
│  └────────────────────────────────────────┘  │
│          ▲ agentRef                          │
│  ┌────────────────────────────────────────┐  │
│  │  CronTasks (scheduled Task creation)  │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

## Platform

All resources in this directory are custom resources defined by [KubeOpenCode](https://github.com/kubeopencode/kubeopencode) — a Kubernetes-native platform for running AI agents. Standard Kubernetes resources (`ServiceAccount`, `Role`, etc.) are used alongside them for RBAC.

| Custom Resource | API Group | Description |
|-----------------|-----------|-------------|
| `AgentTemplate` | `kubeopencode.io/v1alpha1` | Shared agent configuration blueprint (images, credentials, contexts) |
| `Agent` | `kubeopencode.io/v1alpha1` | Always-running agent instance (Deployment + Service), inherits from AgentTemplate |
| `Task` | `kubeopencode.io/v1alpha1` | A unit of work assigned to an agent (via agentRef) or run ephemerally (via templateRef) |
| `CronTask` | `kubeopencode.io/v1alpha1` | Scheduled Task creation with cron expressions, concurrency control, and retention limits |
| `TaskTemplate` | `kubeopencode.io/v1alpha1` | Reusable task definition |

All resources are deployed to a single `server-foundation` namespace.

## Prerequisites

- Kubernetes cluster with [KubeOpenCode](https://kubeopencode.io) operator installed
- `kubectl` and `kustomize` CLI tools
- GitHub App credentials for the bot

## Setup

### 1. Deploy secrets (one-time, per cluster)

Secrets are managed separately from the kustomization to avoid requiring credentials for every deploy. Each developer applies secrets to their own cluster independently.

```bash
cp deploy/secrets.example.yaml deploy/secrets.yaml
# Edit secrets.yaml with actual values
kubectl apply -f deploy/secrets.yaml -n server-foundation
```

> **Note:** `secrets.yaml` is git-ignored. Never commit it. In the future, secrets may be managed via a more secure method (e.g., Vault, External Secrets Operator).

### 2. Deploy everything else

```bash
kubectl apply -k deploy/
```

This deploys AgentTemplate, Agent, CronTasks, RBAC, and namespace — but not secrets. Secrets must already exist in the cluster (see step 1).

## Changing Resources

When renaming, adding, or removing any resource file under `deploy/`, always review `kustomization.yaml` to ensure all `resources:` entries match the actual filenames. Stale references will cause `kubectl apply -k` to fail.

## Manual Task Triggers

### Trigger a CronTask

```bash
# Trigger any CronTask immediately via annotation
kubectl annotate crontask weekly-pr-report kubeopencode.io/trigger=true -n server-foundation
kubectl annotate crontask daily-bug-triage kubeopencode.io/trigger=true -n server-foundation
```

### Ad-hoc Task (via Agent)

Runs on the persistent agent (wakes it from standby if needed):

```bash
cat <<EOF | kubectl create -f -
apiVersion: kubeopencode.io/v1alpha1
kind: Task
metadata:
  generateName: adhoc-task-
  namespace: server-foundation
spec:
  agentRef:
    name: server-foundation-agent
  description: |
    <your task description here>
  contexts:
    - name: target-repo
      type: Git
      git:
        repository: https://github.com/org/repo.git
        ref: main
      mountPath: target
EOF
```

### Ad-hoc Task (via Template, ephemeral)

Runs as a standalone ephemeral pod — no persistent agent needed:

```bash
cat <<EOF | kubectl create -f -
apiVersion: kubeopencode.io/v1alpha1
kind: Task
metadata:
  generateName: adhoc-task-
  namespace: server-foundation
spec:
  templateRef:
    name: server-foundation-template
  description: |
    <your task description here>
  contexts:
    - name: target-repo
      type: Git
      git:
        repository: https://github.com/org/repo.git
        ref: main
      mountPath: target
EOF
```

## Monitoring

```bash
# Watch tasks
kubectl get tasks -n server-foundation -w

# Check CronTask status and next schedule
kubectl get crontasks -n server-foundation

# Check agent status
kubectl get agents -n server-foundation
```

## Local Development

To run the agent locally with the same secrets used in the cluster, use [direnv](https://direnv.net/) to auto-load environment variables from `deploy/secrets.yaml`.

**Setup (one-time):**

```bash
# 1. Install direnv
brew install direnv

# 2. Add hook to your shell (zsh)
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
source ~/.zshrc

# 3. Generate .env from K8s secrets
yq eval-all '.stringData // {} | to_entries[] | .key + "=" + "\"" + (.value | sub("\n$","") ) + "\""' deploy/secrets.yaml | grep -v '^---$' > .env

# 4. Allow direnv for this directory
direnv allow
```

After this, entering the project directory will automatically export all secrets as environment variables. The `.env` and `.envrc` files are git-ignored.

**Regenerate after secrets change:**

```bash
yq eval-all '.stringData // {} | to_entries[] | .key + "=" + "\"" + (.value | sub("\n$","") ) + "\""' deploy/secrets.yaml | grep -v '^---$' > .env
```
