# Deployment Guide

## Architecture

```
┌─────────────────────────────────────┐
│  server-foundation namespace        │
│                                     │
│  ┌───────────────────────────────┐  │
│  │  Agent: server-foundation-agent│  │
│  │  (repo-as-agent)              │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  CronJob: weekly-pr-report    │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  Tasks (created by CronJobs)  │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

## Platform

The resources in this directory (`Agent`, `Task`, `TaskTemplate`) are custom resources defined by [KubeOpenCode](https://github.com/kubeopencode/kubeopencode) — a Kubernetes-native platform for running AI agents. Standard Kubernetes resources (`CronJob`, `ServiceAccount`, `Role`, etc.) are used alongside them for scheduling and RBAC.

| Custom Resource | API Group | Description |
|-----------------|-----------|-------------|
| `Agent` | `kubeopencode.io/v1alpha1` | Declares an agent (identity, model, credentials, contexts) |
| `Task` | `kubeopencode.io/v1alpha1` | A unit of work assigned to an agent |
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

This deploys agents, CronJobs, RBAC, and namespace — but not secrets. Secrets must already exist in the cluster (see step 1).

## Changing Resources

When renaming, adding, or removing any resource file under `deploy/`, always review `kustomization.yaml` to ensure all `resources:` entries match the actual filenames. Stale references will cause `kubectl apply -k` to fail.

## Manual Task Triggers

### Weekly PR Report

```bash
kubectl create job test-weekly-pr-report \
  --from=cronjob/weekly-pr-report-cron \
  -n server-foundation
```

### Ad-hoc Task

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

## Monitoring

```bash
# Watch tasks
kubectl get tasks -n server-foundation -w

# Check CronJob status
kubectl get cronjobs -n server-foundation

# View recent jobs
kubectl get jobs -n server-foundation --sort-by=.metadata.creationTimestamp
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
