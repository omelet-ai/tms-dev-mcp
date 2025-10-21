---
title: Rate Limit Exceeded
description: Resolve HTTP 429 responses and throttling warnings across Omelet and iNavi APIs.
---

# Rate Limit Exceeded

Hitting rate limits stalls batch jobs and interactive requests. Use these steps to reduce traffic and stay within quota.

---

### Step 1: Identify the Limiting Service
Check response headers for `Retry-After` or service-specific limit headers. Omelet responses include `x-rate-limit-remaining`, while iNavi surfaces bucket usage in the JSON payload.

### Step 2: Implement Backoff Logic
Add exponential backoff with jitter in the calling service. Start with a base delay of 2 seconds and cap at 1 minute to avoid request bursts.

### Step 3: Request Higher Limits
If traffic requirements are steady, contact the platform team with recent usage metrics and required throughput to request a tier upgrade.
