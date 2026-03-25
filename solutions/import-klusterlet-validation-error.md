---
title: ManagedCluster import stuck due to kubectl/oc version incompatibility
symptom: "error validating data: ValidationError(Klusterlet.spec.registrationConfiguration.bootstrapKubeConfigs): missing required field \"type\""
keywords: [import, klusterlet, ValidationError, missing required field, type, authType, registrationConfiguration, bootstrapKubeConfigs, kubectl, oc, Importing resources are applied]
affected_versions: "ACM 2.8+"
last_verified: 2025-03-25
status: active
---

## Symptom

ManagedCluster stuck at condition:

```
Importing resources are applied, wait for resources be available
```

Checking the klusterlet status on the managed cluster reveals a validation error:

```
error validating "STDIN": error validating data: [ValidationError(Klusterlet.spec.registrationConfiguration.bootstrapKubeConfigs): missing required field "type" in io.open-cluster-management.operator.v1.Klusterlet.spec.registrationConfiguration.bootstrapKubeConfigs, ValidationError(Klusterlet.spec.registrationConfiguration.registrationDriver): missing required field "authType" in io.open-cluster-management.operator.v1.Klusterlet.spec.registrationConfiguration.registrationDriver]
```

## Root Cause

The `kubectl` or `oc` binary on the managed cluster is too old to understand the newer Klusterlet CRD schema. The import process applies the Klusterlet manifest via `kubectl apply`, and older versions perform client-side validation that rejects the new required fields (`type`, `authType`) introduced in newer OCM operator versions.

This is **not** a problem with the manifest itself — it is a client-side validation mismatch.

## Fix

1. Check the `kubectl`/`oc` version on the managed cluster:
   ```bash
   kubectl version --client
   oc version --client
   ```

2. Upgrade `kubectl`/`oc` to a version that includes the updated Klusterlet CRD schema, or use `--validate=false` as a temporary workaround:
   ```bash
   kubectl apply --validate=false -f <klusterlet-manifest>
   ```

3. Alternatively, check the klusterlet status directly to confirm the root cause:
   ```bash
   kubectl get klusterlet -o yaml
   # Look at status.conditions for validation errors
   ```

## References

- [ACM-21811](https://issues.redhat.com/browse/ACM-21811)
