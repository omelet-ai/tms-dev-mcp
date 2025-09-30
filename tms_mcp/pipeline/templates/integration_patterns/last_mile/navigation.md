# Last-Mile Delivery & Navigation Workflow

This guide outlines a streamlined, four-step process for last-mile delivery, with navigation path generation.

---

### Step 1: Geocode Addresses
Convert warehouse and customer addresses into geographic coordinates (latitude/longitude) using iNavi's `Multi Geocoding` API.

### Step 2: Build Cost Matrix
Calculate the real-world travel distance between all the coordinates from the previous step using iNavi's `Route Distance Matrix` API.

### Step 3: Optimize Routes
Determine the most efficient sequence of stops for each vehicle, using the cost matrix from the previous step using Omelet's `Vehicle Routing` API.

### Step 4: Generate Final Navigation Path
Create navigable routes that can be visualized on a map, using the sequence of stops from the previous step using iNavi's `Multi Waypoint Route Search` API.
