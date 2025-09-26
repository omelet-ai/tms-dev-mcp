# High-Precision Last-Mile Workflow

This guide outlines a streamlined, four-step process for high-precision last-mile delivery.

---

### **Step 1: Geocode Addresses**

- **Goal:** Convert pickup and delivery addresses into geographic coordinates (latitude/longitude).
- **API:** iNavi `/maps/v3.0/appkeys/{appkey}/multi-coordinates`

---

### **Step 2: Refine Entry Points**

- **Goal:** Adjust base coordinates to the most practical building access locations.
- **API:** iNavi `/maps/v3.0/appkeys/{appkey}/multi-optimal-searches`

---

### **Step 3: Build Cost Matrix**

- **Goal:** Calculate real-world travel distance and time between refined coordinate pairs.
- **API:** iNavi `/maps/v3.0/appkeys/{appkey}/route-distance-matrix`

---

### **Step 4: Optimize Routes**

- **Goal:** Determine the most efficient sequence of stops for each vehicle.
- **API:** Omelet `/api/vrp`
