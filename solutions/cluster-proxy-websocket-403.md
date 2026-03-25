---
title: Console WebSocket to cluster-proxy returns 403 Forbidden
symptom: "403 Forbidden when console connects to cluster-proxy via WebSocket"
keywords: [cluster-proxy, 403, Forbidden, WebSocket, Host header, Origin header, console, watch, proxy, CSWH]
affected_versions: "ACM 2.4+"
last_verified: 2025-03-25
status: active
---

## Symptom

The ACM console fails to establish WebSocket connections through cluster-proxy. Requests return `403 Forbidden`. Notably, VNC WebSocket connections through the same proxy work fine, but Kubernetes API `watch` endpoints fail.

## Root Cause

A network proxy (e.g., F5, nginx, or corporate forward proxy) sitting between the console and cluster-proxy is **stripping the `Host` and `Origin` HTTP headers** from the WebSocket upgrade request.

**Why this causes 403:**

- **`Host` header** — HTTP/1.1 mandatory header. The Kubernetes API server uses it to route requests to the correct virtual host. Without it, the request is rejected.
- **`Origin` header** — Used by the Kubernetes API server to prevent Cross-Site WebSocket Hijacking (CSWH). The API server checks `Origin` against an allowlist; if the header is missing, the handshake is rejected with 403.

**Why VNC works but K8s API watch does not:**

- VNC WebSocket endpoints have relaxed header validation
- Kubernetes API `watch` endpoints strictly enforce `Host` and `Origin` header checks for security

## Fix

Configure the intermediate proxy to **preserve** the `Host` and `Origin` headers when forwarding WebSocket requests:

For **nginx**:
```nginx
proxy_set_header Host $host;
proxy_set_header Origin $http_origin;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

For **F5 / other load balancers**: ensure the HTTP profile does not strip standard headers from WebSocket upgrade requests.

**Verification:** After the proxy config change, confirm the console can establish WebSocket connections to cluster-proxy and that `kubectl` watch operations through the proxy work without 403 errors.

## References

- Slack thread: `#forum-acm-platform` discussion on console 403 via cluster-proxy
