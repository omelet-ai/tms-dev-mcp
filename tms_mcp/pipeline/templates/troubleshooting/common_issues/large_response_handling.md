---
title: Large Response Handling in Route APIs
description: Handle oversized responses from route-normal-via and route-time endpoints when dealing with many waypoints over long distances.
---

# Large Response Handling in Route APIs

The `/route-normal-via` and `/route-time` endpoints can return extremely large responses when processing many waypoints over long distances. AI agents may avoid making these requests due to response size concerns.

---

### Step 1: Reduce Test Scope
When encountering this pattern, reduce the number of waypoints and/or the distance between points to create a smaller test case. This helps verify functionality without overwhelming the agent's context.

### Step 2: Use Schema-Based Analysis
Instead of having the agent directly inspect the full response body, leverage the response schema to analyze the structure indirectly. The agent can understand the response format through the schema without processing the entire payload.

### Step 3: Implement Pagination or Batching
For production use cases requiring many waypoints, consider breaking the route into smaller segments and making multiple requests. Process each segment independently and combine results programmatically.
