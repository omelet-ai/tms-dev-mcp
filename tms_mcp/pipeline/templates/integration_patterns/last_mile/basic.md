# Last-Mile Delivery Workflow

This guide outlines a streamlined, three-step process for basic last-mile delivery.

---

### Step 1: Geocode Addresses
Convert warehouse and customer addresses into geographic coordinates (latitude/longitude) using iNavi's `Multi Geocoding` API.

### Step 2: Build Cost Matrix
Calculate the real-world travel distance between all the coordinates from the previous step using iNavi's `Route Distance Matrix` API.

### Step 3: Optimize Routes
Determine the most efficient sequence of stops for each vehicle, using the cost matrix from the previous step using Omelet's `Vehicle Routing` API.
