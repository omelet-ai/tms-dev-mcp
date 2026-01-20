---
title: API Key and Authentication Errors
description: Resolve authentication issues when using multiple API keys across Omelet and iNavi endpoints.
---

# API Key and Authentication Errors

This MCP server integrates with two different API providers (Omelet and iNavi), each requiring its own API key. Using the wrong key for an endpoint is a common authentication failure.

---

### Step 1: Verify MCP Server Configuration
Call the `get_basic_info()` tool to retrieve the configured API keys for both Omelet and iNavi. This helps confirm which keys are currently active in the MCP server settings.

### Step 2: Match the Correct Key to the Endpoint
Identify which provider the endpoint belongs to:
- **Omelet endpoints** include `/api/vrp`, `/api/fsmvrp`, `/api/pdp`, `/api/cost-matrix`, and their `-long` variants
- **iNavi endpoints** include `/route-normal-via`, `/route-time`, `/coordinates`, `/route-distance-matrix`

Ensure you're using the Omelet API key for Omelet endpoints and the iNavi API key for iNavi endpoints.

### Step 3: Provide Keys Manually if Unconfigured
If the MCP server has not been configured with API keys, the user must provide them directly. Request the appropriate API key based on the endpoint being called.
