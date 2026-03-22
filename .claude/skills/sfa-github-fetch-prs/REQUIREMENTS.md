# Installation Requirements for Fetch PRs Skill

Before using this skill, ensure you have:

## 1. Required Tools

```bash
# GitHub CLI (v2.0.0+)
gh --version

# jq (for JSON processing)
jq --version

# Bash 4.0+ (macOS users: brew install bash)
bash --version
```

Install missing tools:

```bash
# macOS
brew install gh jq bash

# Linux (Debian/Ubuntu)
sudo apt-get install gh jq

# Linux (RHEL/CentOS)
sudo yum install gh jq
```

### 2. GitHub Authentication

```bash
# Login to GitHub
gh auth login

# Grant required permissions
gh auth refresh -s project -s read:org

# Verify authentication
gh auth status
```

You should see "Logged in to github.com as <your-username>".
