---
title: cluster-proxy-addon fails after backup/restore activation
symptom: "cluster-proxy-proxy-agent failed after restore activation"
keywords: [cluster-proxy, addon, restore, backup, CSR, signer, hub-config, certificate, customized signer, proxy-agent-signer-client-cert]
affected_versions: "ACM 2.5 and earlier (fixed in addon-framework in 2.6+)"
last_verified: 2025-03-25
status: active
---

## Symptom

After performing a backup/restore of an ACM hub cluster, the `cluster-proxy-addon` (and potentially other addons with customized CSR signers like the observability addon) stops functioning. The proxy agent on managed clusters cannot reconnect to the new hub.

## Root Cause

cluster-proxy-addon uses a **customized CSR signer** instead of the default `kubernetes.io/kube-apiserver-client` signer. This creates two CSRs during registration:

1. **`cluster-proxy-hub-config`** — signed by the hub's kube-apiserver (standard)
2. **`cluster-proxy-open-cluster-management.io-proxy-agent-signer-client-cert`** — signed by cluster-proxy's own signer (customized)

The critical difference: when the standard CSR is saved as a secret, it includes a `hub-config` field alongside `tls.crt` and `tls.key`. After a restore, this `hub-config` changes (new hub identity), which triggers the addon to detect the hub change and re-register.

However, the **customized CSR signer does NOT include `hub-config`** in its secret. After restore:
- The addon cannot detect that the hub has changed
- It does not create a new CSR
- The old certificate remains, pointing to the old hub
- cluster-proxy-addon fails to function

## Fix

**For ACM 2.5:** A special workaround was implemented specifically for this version — apply the hotfix patch for cluster-proxy-addon restore handling.

**For ACM 2.6+:** This is fixed at the `addon-framework` level. The framework now handles hub change detection for all addons regardless of signer type. Ensure you are running addon-framework 2.6+.

**Manual recovery (any version):** Force re-registration by deleting the stale secrets on the managed cluster:
```bash
# On the managed cluster
kubectl delete secret -n open-cluster-management-agent-addon \
  cluster-proxy-open-cluster-management.io-proxy-agent-signer-client-cert

# The addon agent will detect the missing secret and create a new CSR
```

## References

- [ACM-10093](https://issues.redhat.com/browse/ACM-10093): cluster-proxy-proxy-agent failed after restore activation
