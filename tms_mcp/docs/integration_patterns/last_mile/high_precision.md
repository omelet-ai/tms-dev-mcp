# High-Precision Last-Mile Workflow

This guide outlines a streamlined, four-step process for high-precision last-mile delivery.

---

### Step 1: Geocode Addresses
Convert warehouse and customer addresses into geographic coordinates (latitude/longitude) using iNavi's `Multi Geocoding` API.

### Step 2: Refine Entry Points
Adjust base coordinates to the most practical building access locations using iNavi's `Multi Optimal Point Search` API.

### Step 3: Build Cost Matrix
Calculate real-world travel distance and time between refined coordinate pairs using iNavi's `Route Distance Matrix` API.

### Step 4: Optimize Routes
Determine the most efficient sequence of stops for each vehicle, using the cost matrix from the previous step using Omelet's `Vehicle Routing` API.
