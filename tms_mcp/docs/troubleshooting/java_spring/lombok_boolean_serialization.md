---
title: Lombok Boolean Field Serialization Issue
description: Fix JSON serialization problems with Boolean fields when using Lombok in Java/Spring applications.
---

# Lombok Boolean Field Serialization Issue

When using Lombok's `@Data` or `@Getter` annotations with Boolean-typed fields, Jackson may serialize field names incorrectly, causing mismatches with API response schemas.

---

### Step 1: Understand the Problem
Lombok generates getter methods for Boolean fields following JavaBeans conventions. A field named `isSuccessful` gets a getter `isIsSuccessful()`, which Jackson then interprets as a property named `successful` (removing the `is` prefix), not `isSuccessful`.

### Step 2: Solution A - Use @JsonProperty Annotation
Explicitly specify the JSON property name with Jackson's `@JsonProperty` annotation:

```java
@Data
public class ApiResponse {
    @JsonProperty("isSuccessful")
    private Boolean isSuccessful;
}
```

This ensures the field serializes exactly as `isSuccessful` in the JSON output.

### Step 3: Solution B - Manually Define Getter
Override Lombok's generated getter by providing your own method:

```java
@Data
public class ApiResponse {
    private Boolean isSuccessful;

    public Boolean getIsSuccessful() {
        return isSuccessful;
    }
}
```

This preserves the `is` prefix in the getter method name, resulting in correct JSON serialization.
