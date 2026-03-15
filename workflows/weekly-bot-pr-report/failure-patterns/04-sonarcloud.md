---
id: FP-04
name: SonarCloud Code Analysis
action_on_match: patched
requires_clone: true
---

# FP-04: SonarCloud Code Analysis Failure

SonarCloud is the only failing check — all build and test checks pass. The agent clones the code, retrieves the SonarCloud report details, and attempts to fix the reported issues.

## Detection

1. Check if `SonarCloud Code Analysis` is in the `failed_checks` list.
2. Check that **all other checks passed** — i.e., `SonarCloud Code Analysis` is the **only** entry in `failed_checks`.
3. If SonarCloud failed alongside other checks (build, e2e, etc.), this pattern does NOT match — fall through to later patterns or default.

**Match condition**: `failed_checks` contains exactly one entry: `SonarCloud Code Analysis`.

## Fix Procedure

1. Get the SonarCloud check details from `all_checks` — find the entry where `name == "SonarCloud Code Analysis"` and extract its `link` URL.

2. Fetch the SonarCloud report page at the check link URL to understand what issues were found. Common SonarCloud issue categories:
   - **Bugs**: Null pointer dereferences, resource leaks, logic errors
   - **Code Smells**: Unused variables, duplicated code, overly complex functions
   - **Security Hotspots**: Hardcoded credentials, insecure crypto, SQL injection risks
   - **Coverage**: Insufficient test coverage (usually NOT fixable by agent)

3. Clone the PR branch using the `clone-worktree` skill:
   ```bash
   WORKTREE=$(.claude/skills/clone-worktree/clone-worktree.sh <org/repo> <pr-number>)
   cd "$WORKTREE"
   ```

4. Based on the SonarCloud findings, apply fixes:
   - **Unused imports/variables**: Remove them
   - **Error not checked**: Add proper error handling (`if err != nil`)
   - **Duplicated code blocks**: Extract into shared helper
   - **Security issues**: Fix according to SonarCloud recommendation
   - **Complexity issues**: Simplify logic, extract functions

5. Verify the fix compiles:
   ```bash
   make build 2>&1
   ```

6. If the fix compiles successfully, commit and push:
   ```bash
   git add -A
   git commit -s -m "fix: resolve SonarCloud code analysis issues"
   git push
   ```

7. Clean up the worktree:
   ```bash
   .claude/skills/clone-worktree/clone-worktree.sh --remove <org/repo> <pr-number>
   ```

## Fallback

If the SonarCloud issues cannot be fixed automatically (e.g., coverage requirements, complex refactoring needed):
- Record as `needs-manual`.
- Include the SonarCloud issue summary in `action_details` so the human reviewer knows what to look at.
- Do NOT push partial or broken fixes.

## Verification

- After pushing a fix, confirm `git push` succeeded.
- The pushed commit should trigger a CI re-run including SonarCloud re-analysis.
- If `make build` fails after applying fixes, revert and report as `needs-manual`.

## Scope

- Only fix issues reported by SonarCloud in the files changed by the PR.
- Do NOT refactor unrelated code or fix pre-existing SonarCloud issues outside the PR's scope.
- Keep fixes minimal and focused on the specific SonarCloud findings.
