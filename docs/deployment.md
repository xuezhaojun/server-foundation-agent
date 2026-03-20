# Deployment

## Architecture

```
┌─────────────────────────────────────────┐
│  server-foundation namespace            │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  Agent: server-foundation-agent   │  │
│  │  (repo-as-agent)                  │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  CronJob: weekly-pr-report-cron   │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  Tasks (created by CronJobs)      │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

The agent runs on a Kubernetes cluster powered by [KubeOpenCode](https://github.com/kubeopencode/kubeopencode) — a Kubernetes-native platform for running AI agents. All resources are deployed to a single `server-foundation` namespace.

For cluster deployment details (secrets, kustomize setup, manual task triggers, monitoring), see [deploy/README.md](../deploy/README.md).

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
