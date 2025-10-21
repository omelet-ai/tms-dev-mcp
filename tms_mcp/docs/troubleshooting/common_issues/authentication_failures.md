---
title: Authentication Failures
description: Diagnose 401 and 403 errors caused by missing or invalid credentials when calling Omelet or iNavi endpoints.
---

# Authentication Failures

Unauthorized responses usually indicate credential problems or expired tokens. Follow these steps to resolve them quickly.

---

### Step 1: Confirm Active Credentials
Verify that the API key or token in use is current. For iNavi, ensure the app key has not been rotated. For Omelet, check the project dashboard for recently revoked keys.

### Step 2: Validate Request Headers
Inspect the outgoing request to confirm the correct header name (`Authorization`, `x-app-key`, etc.) and formatting. Omelet expects `Authorization: Bearer <token>`, while iNavi requires query parameters such as `appkey`.

### Step 3: Retry With a Known-Good Key
Swap in a key that is confirmed to be valid—ideally from a simple curl command. If the call succeeds, rotate or regenerate the failing credential set.
