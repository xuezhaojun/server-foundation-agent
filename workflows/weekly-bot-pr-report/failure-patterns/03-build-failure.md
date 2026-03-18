---
id: FP-03
name: Locally Verifiable CI Failure
action_on_match: patched
requires_clone: true
---

# FP-03: Locally Verifiable CI Failure

Covers all CI checks that the agent can reproduce and fix locally: build, unit tests, integration tests, and verify (lint/vet). The agent clones the code, runs each failing check locally, and iteratively fixes errors until all pass.

## Detection

1. Check if any failed check name matches a **locally verifiable** pattern:

   | CI Check Pattern | Local Command | Category |
   |-----------------|---------------|----------|
   | `ci/prow/images`, or contains `build` or `image` (case-insensitive) | `make build` | Build |
   | `ci/prow/unit`, or contains `unit` (case-insensitive) | `make test` | Unit Test |
   | `ci/prow/integration`, or contains `integration` (case-insensitive) | `make integration` | Integration Test |
   | `ci/prow/verify`, or contains `verify` (case-insensitive, but NOT `verify-deps`) | `make verify` | Verify (lint/vet) |
   | `ci/prow/verify-deps` | `go mod tidy && go mod vendor` + check `git diff` | Dep Verify |

2. This pattern should be evaluated AFTER FP-01 (Go version mismatch) and FP-02 (E2E cluster pool).

**Match condition**: At least one failed check is locally verifiable AND FP-01/FP-02 did not match.

## Fix Procedure

**Principle: TRY FIRST, JUDGE LATER.** You MUST attempt to fix every locally verifiable failure before concluding it needs manual intervention. Do NOT skip to `needs-manual` based on reading error messages alone — always run the fix loop below.

### Step 1: Clone

Clone the PR branch using the `clone-worktree` skill:
```bash
WORKTREE=$(.claude/skills/clone-worktree/clone-worktree.sh <org/repo> <pr-number>)
cd "$WORKTREE"
```

### Step 2: Discover Make Targets and Map CI Checks

**Make target names are NOT fixed** — they vary by repository. You MUST inspect the Makefile first.

#### 2a: Read the Makefile to discover available targets
```bash
# List all make targets
grep -E '^[a-zA-Z_-]+:' Makefile | sed 's/:.*//' | sort -u
# Also check for included makefiles
grep -E '^include ' Makefile
```

Read the Makefile (or relevant sections) to understand what each target does. Look for targets related to: build/compile, test/unit, integration, verify/lint/vet, e2e, and code generation.

#### 2b: Map failed CI checks to local make targets

For each failed CI check, find the corresponding local make target by reading the Makefile. Common mappings (but verify against actual Makefile):

| CI Check Category | Typical Make Targets (examples, not guaranteed) |
|-------------------|------------------------------------------------|
| Build | `build`, `compile`, `images`, `binary` |
| Unit Test | `test`, `unit`, `unit-test`, `test-unit` |
| Integration Test | `integration`, `test-integration`, `integration-test` |
| Verify | `verify`, `lint`, `check`, `vet` |
| Dep Verify | `verify-deps`, `vendor` (or just `go mod tidy && go mod vendor`) |
| E2E (build only) | `e2e-build`, `test-e2e` (compile only, see Step 4) |

Create your checklist based on the **actual** targets found in the Makefile. Example:
```
Makefile targets found: build, test, verify, e2e
failed: ci/prow/images       → make build        (Build)
failed: ci/prow/unit         → make test          (Unit Test)
failed: ci/prow/verify       → make verify        (Verify)
failed: ci/prow/verify-deps  → go mod tidy/vendor (Dep Verify)
failed: ci/prow/e2e          → NOT locally verifiable (skip, but build-check in Step 4)
```

If a CI check has no matching make target, try `go build ./...`, `go test ./...`, or `go vet ./...` as fallbacks.

**Processing order**: Build → Dep Verify → Verify → Unit Test → Integration Test. Build must pass first since other checks depend on compilation.

### Step 3: Fix Each Check Category

For each failing check category (in order), run the fix loop below. Once a category passes, move to the next one. If a category cannot be fixed after exhausting iterations, continue to the next category anyway — fix as many as possible.

**Note**: The make targets shown below (e.g., `make build`, `make test`) are examples. Always use the **actual targets you discovered in Step 2**. If the repo uses `make compile` instead of `make build`, use that.

---

#### 3A: Build Fix Loop

**Initial attempt:**
```bash
make build 2>&1 | tail -100
```
- If `make build` **succeeds**: Skip to next category.
- If `make build` **fails**: Run the dependency refresh, then the adaptive loop.

**Phase A — Dependency Refresh (1 attempt):**
```bash
go mod tidy && go mod vendor && make build 2>&1 | tail -100
```
If build succeeds → move to next category. Otherwise proceed to Phase B.

**Phase B — Adaptive Fix Iterations (up to 5 iterations):**

Each iteration: capture errors → apply fixes → rebuild → evaluate progress. **"Analyzing errors" without editing files does NOT count as an iteration.**

Track your progress: record the error count after each iteration. Continue as long as errors are decreasing or you have a new strategy to try.

**Each iteration follows this procedure:**

1. **Capture errors and count them:**
   ```bash
   make build 2>&1 | tee /tmp/build_errors.txt | tail -80
   grep -c "^.*\.go:[0-9]*:[0-9]*:" /tmp/build_errors.txt
   ```

2. **Pick a fix strategy** based on the current errors:

   **Strategy A — Update transitive dependencies:**
   When errors are in vendored transitive dependencies (e.g., `vendor/open-cluster-management.io/sdk-go`), update the dependency:
   ```bash
   go get open-cluster-management.io/sdk-go@latest
   go mod tidy && go mod vendor
   ```

   **Strategy B — Edit source code in the repo:**
   When errors are in the repo's own source code (NOT under `vendor/`):
   - Find the new API signature: `grep -rn "func.*MethodName" vendor/<package>/`
   - Edit the calling code to match the new signature
   - Fix import paths, type mismatches, missing interface methods, etc.

   **Strategy C — Pin or downgrade a problematic dependency:**
   When a dependency upgrade cascades into too many breaking changes:
   ```bash
   go get k8s.io/client-go@v0.31.4
   go mod tidy && go mod vendor
   ```

   **Strategy D — Update multiple related dependencies together:**
   When individual updates cause version conflicts:
   ```bash
   go get k8s.io/client-go@v0.33.3 k8s.io/api@v0.33.3 k8s.io/apimachinery@v0.33.3
   go get open-cluster-management.io/sdk-go@latest
   go mod tidy && go mod vendor
   ```

3. **Rebuild and evaluate:**
   - **Build succeeds** → move to next category
   - **Error count decreased** → continue with next iteration
   - **Error count unchanged, different errors** → try a different strategy
   - **Error count unchanged, same errors** → switch strategy
   - **Error count increased** → revert (`git checkout -- .`) and switch strategy

4. **Do NOT repeat the same failed strategy.** Suggested iteration plan:
   - Iteration 1: Strategy A (update transitive deps)
   - Iteration 2: Strategy D (update related deps together)
   - Iteration 3: Strategy B (fix source code)
   - Iteration 4: Strategy C (pin/downgrade)
   - Iteration 5: Combine strategies or try alternative version pins

---

#### 3B: Dep Verify Fix Loop

If `ci/prow/verify-deps` failed:
```bash
go mod tidy && go mod vendor
git diff --stat
```
- If no diff → dep verify was already fixed during Build fix. Move on.
- If there is a diff → the PR's vendored dependencies were inconsistent. This is now fixed. Move on.

No iterative loop needed — `go mod tidy && go mod vendor` is the only fix.

---

#### 3C: Verify Fix Loop (up to 3 iterations)

If `ci/prow/verify` failed:
```bash
make verify 2>&1 | tee /tmp/verify_errors.txt | tail -100
```
- If `make verify` **succeeds**: Move to next category.
- If `make verify` **fails**: Analyze and fix iteratively.

**Common verify fixes:**
- **gofmt**: `gofmt -w <file.go>` or `gofmt -w .`
- **goimports**: `goimports -w <file.go>` (install with `go install golang.org/x/tools/cmd/goimports@latest` if needed)
- **go vet**: Fix the reported issues in source code (shadow variables, unused params, etc.)
- **golint / staticcheck**: Fix the reported code quality issues
- **generated code out of date**: Run the code generator (look for `make generate`, `make codegen`, or `hack/update-codegen.sh`)
- **CRD/manifest drift**: Run `make manifests` or `make update` if available

Each iteration: read error output → fix the reported issues → re-run `make verify`. After 3 iterations, move on regardless.

---

#### 3D: Unit Test Fix Loop (up to 3 iterations)

If `ci/prow/unit` failed:
```bash
make test 2>&1 | tee /tmp/test_errors.txt | tail -100
```
- If `make test` **succeeds**: Move to next category.
- If `make test` **fails**: Analyze and fix iteratively.

**Common unit test fixes:**
- **Dependency API changes broke tests**: Update test code to use the new API (same strategies as Build fix)
- **Expected values changed**: If a dependency update changes default values or output format, update test expectations
- **Missing test fixtures**: Add or update fixture files
- **Import path changes**: Update import paths in `_test.go` files

Each iteration: read test output → identify failing tests → fix → re-run. Focus on the specific failing test packages:
```bash
# Run only the failing package to get faster feedback
go test ./pkg/specific/package/... 2>&1 | tail -50
```
After 3 iterations, move on regardless.

---

#### 3E: Integration Test Fix Loop (up to 3 iterations)

If `ci/prow/integration` failed:
```bash
make integration 2>&1 | tee /tmp/integration_errors.txt | tail -100
```
- If the command is not available (`make: *** No rule to make target 'integration'`), try `make test-integration` or `make e2e-test`.
- If `make integration` **succeeds**: Move to next category.
- If `make integration` **fails**: Apply same fix strategies as Unit Test.

Each iteration: read output → fix → re-run. After 3 iterations, move on regardless.

---

### Step 4: Final Verification

After processing all categories, run a combined check to confirm everything passes:
```bash
make build 2>&1 | tail -20 && echo "BUILD OK" || echo "BUILD FAILED"
make verify 2>&1 | tail -20 && echo "VERIFY OK" || echo "VERIFY FAILED"
make test 2>&1 | tail -20 && echo "TEST OK" || echo "TEST FAILED"
```
Only run the commands for categories that were originally failing. Record which categories now pass and which still fail.

**E2E build check (always run):** Even though E2E tests are not locally verifiable (they need a live cluster), verify that E2E test code **compiles** successfully. Dependency updates can break E2E test compilation too.

First, find where E2E test code lives:
```bash
# Look for e2e directories
find . -type d -name "*e2e*" | grep -v vendor | grep -v .git
# Check if Makefile has an e2e build target
grep -iE 'e2e.*build|build.*e2e|e2e.*compile' Makefile
```

Then compile the E2E test packages without running them:
```bash
# Compile test binaries without executing (the -run=^$ -c pattern)
go test -run=^$ -c ./<e2e-test-dir>/... 2>&1 | tail -20 && echo "E2E BUILD OK" || echo "E2E BUILD FAILED"
```

If E2E compilation fails, apply the same fix strategies from the Build fix loop (Step 3A) to resolve it — the errors are typically the same kind (API changes, import paths, etc.). Include the E2E build status in the final result.

### Step 5: Commit and Push

If **at least one** previously-failing category now passes after your fixes:
```bash
git add -A
git commit -s -m "fix: resolve CI failures from dependency update

Fixes: <list which categories were fixed, e.g., build, verify, unit test>"
git push
```
Record as `patched` with details of what was fixed and what still needs manual attention (if any).

If **no** category was fixed (all still fail), do NOT push. Record as `needs-manual`.

### Step 6: Clean Up

Always clean up the worktree, whether the fix succeeded or failed:
```bash
.claude/skills/clone-worktree/clone-worktree.sh --remove <org/repo> <pr-number>
```

## Fallback

Only mark as `needs-manual` after ALL fix loops above have been attempted and no category was fixed:
- Include the error count progression for build (e.g., "Phase A: 12 errors → Iter 1: 8 errors → ... → Iter 5: 3 errors").
- List which categories were attempted and their final status.
- Describe the strategy used in each build iteration and why it did or didn't help.
- Include the specific remaining errors from the final attempt of each category.
- Do NOT push partial or broken fixes.

## Verification

- After pushing a fix, confirm `git push` succeeded.
- The pushed commit should trigger a CI re-run automatically.
- If no checks could be fixed, document errors clearly for manual review.

## Scope

- Only modify files within the PR's repository.
- Only attempt fixes that are directly related to the CI errors.
- Do NOT refactor code or make unrelated changes.
- Do NOT attempt to fix `ci/prow/e2e` — E2E tests require a live cluster and are NOT locally verifiable.
