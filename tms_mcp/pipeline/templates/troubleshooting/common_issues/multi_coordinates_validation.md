---
title: Multi-Coordinates Request Body Validation
description: Resolve validation errors in iNavi's multi-coordinates API caused by invalid ID field formats.
---

# Multi-Coordinates Request Body Validation

The iNavi `multi-coordinates` API enforces strict validation on the `id` field in the request body. Invalid ID formats will cause the request to fail.

---

### Step 1: Understand the ID Pattern Requirement
The `id` field must match the regex pattern: `^[a-zA-Z0-9]{1,10}$`. This means:
- Only alphanumeric characters (letters and numbers)
- Minimum length: 1 character
- Maximum length: 10 characters
- No special characters, spaces, or Unicode

### Step 2: Validate IDs Before Sending
Before making the API call, validate each ID in your request body against the pattern. Common violations include:
- Using hyphens, underscores, or other special characters
- Exceeding 10 characters
- Including spaces or empty strings

### Step 3: Generate Compliant IDs
If your application uses IDs that don't meet this format, create a mapping between your internal IDs and API-compliant IDs. Use short alphanumeric codes (e.g., `LOC001`, `PT2`, `ADDR99`) that can be mapped back to your original identifiers.
