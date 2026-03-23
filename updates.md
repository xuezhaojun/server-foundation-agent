# Server Foundation Agent - Updates

Daily development log. Keep it short — each day's entry should be scannable in 30 seconds, like a tweet thread (max ~1140 chars per day). Strip all details, keep only the core.

Use `/sfa-session-log` to append entries after each session.

**Format:** `## YYYY-MM-DD` heading, then bullet points. No sub-sections needed — just write what matters.

---

## 2026-03-23

- Fixed 2 cluster-permission bugs. Root cause tied to recent ACM→MCE migration.
- Test cluster access is a game changer — once agent got admin kubeconfig, it found root cause fast. Confirms: agent needs cluster access for debug tasks.
- Agent lacks long-term memory of engineering activities. Had to manually tell it about the cluster-permission migration. It should know "what happened recently" as context — recent changes are highly correlated with recent bugs. Need a mechanism to feed engineering history into agent context.
- Agent cannot access QE Jenkins (`*.dno.corp.redhat.com`) — behind VPN. Workaround: paste logs manually.
- Agent cannot access downstream test environments — can't reproduce or verify. Need dedicated test cluster.
