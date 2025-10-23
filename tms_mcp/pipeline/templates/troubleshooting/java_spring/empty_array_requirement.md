---
title: Omelet API Empty Array Requirement
description: Resolve serialization issues when sending requests to Omelet API from Java/Spring applications.
---

# Omelet API Empty Array Requirement

When using Omelet API endpoints from Java/Spring applications, array-typed fields must be sent as empty arrays `[]` rather than `null` values, or the API may reject the request.

---

### Step 1: Identify Array Fields in Request Schema
Review the Omelet API request schema for the endpoint you're calling. Common array fields include:
- `vehicles` in VRP requests
- `orders` or `jobs` in routing problems
- `time_windows` for scheduling constraints
- `skills` or `capacities` for vehicle properties

### Step 2: Initialize Arrays as Empty Collections
In your Java request objects, initialize array fields as empty collections rather than leaving them null:

```java
@Data
public class VrpRequest {
    private List<Vehicle> vehicles = new ArrayList<>();  // Not null
    private List<Job> jobs = new ArrayList<>();          // Not null
    private List<String> skills = new ArrayList<>();     // Not null
}
```

### Step 3: Configure Jackson to Serialize Empty Arrays
If you're working with existing code that uses null values, configure Jackson's `ObjectMapper` to serialize null collections as empty arrays:

```java
@Configuration
public class JacksonConfig {
    @Bean
    public ObjectMapper objectMapper() {
        ObjectMapper mapper = new ObjectMapper();
        mapper.setSerializationInclusion(JsonInclude.Include.NON_NULL);
        mapper.configOverride(List.class)
              .setSetterInfo(JsonSetter.Value.forValueNulls(Nulls.AS_EMPTY));
        return mapper;
    }
}
```

Alternatively, use the `@JsonInclude` annotation on specific fields to control serialization behavior per field.
