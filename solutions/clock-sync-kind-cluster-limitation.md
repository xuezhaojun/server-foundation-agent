---
title: Cannot test clock sync issues with kind clusters
symptom: "ManagedCluster status flapping due to clock desync — kind clusters share host clock"
keywords: [clock sync, kind, time zone, lease, ManagedCluster status flapping, clock not synced, time desync, clocksync daemon]
affected_versions: "All ACM/MCE versions"
last_verified: 2025-03-25
status: active
---

## Symptom

When trying to reproduce clock synchronization issues (e.g., ManagedCluster status flapping due to lease time mismatches) using kind clusters, the test fails to reproduce because both hub and agent kind clusters always have the same system time.

Related Jira issues:
- ACM-8853: Lease node vs managed cluster Lease in different time zone
- ACM-16330: ManagedCluster status flapping due to clock desync

## Root Cause

kind clusters run as containers on the host machine and **inherit the host's system clock**. There is no way to set different times for hub and agent kind clusters independently. Additionally, macOS has a clock sync daemon that synchronizes time from the host to kind containers, preventing any manual time drift.

This is an architectural limitation of kind — it does not support per-container time namespaces.

## Fix

Use an **OCP cluster as the hub** combined with a **local kind cluster as the agent**:

1. Deploy the hub on a remote OCP cluster (which has its own independent system clock)
2. **Before** creating the local kind cluster, modify the macOS system time to simulate clock desync:
   ```bash
   # Disable automatic time sync on macOS
   sudo systemsetup -setusingnetworktime off

   # Set a different time (e.g., 2 hours ahead)
   sudo date -u <desired-time>

   # Now create the kind cluster — it will inherit the modified time
   kind create cluster --name agent-cluster
   ```
3. Register the kind cluster to the OCP hub — the time difference will now be present
4. After testing, restore the system time:
   ```bash
   sudo systemsetup -setusingnetworktime on
   ```

**Key point:** The macOS time must be changed **before** creating the kind cluster, because the clocksync daemon syncs time at container creation.

## References

- [ACM-8853](https://issues.redhat.com/browse/ACM-8853)
- [ACM-16330](https://issues.redhat.com/browse/ACM-16330)
