# Last-Mile Delivery Workflow

This guide outlines a streamlined, three-step process for basic last-mile delivery.

---

### **Step 1: Geocode Addresses**

- **Goal:** Convert street addresses into geographic coordinates (latitude/longitude).
- **API:** iNavi `/maps/v3.0/appkeys/{appkey}/multi-coordinates`

---

### **Step 2: Build Cost Matrix**

- **Goal:** Calculate the real-world travel distance between all coordinate pairs.
- **API:** iNavi `/maps/v3.0/appkeys/{appkey}/route-distance-matrix`

---

### **Step 3: Optimize Routes**

- **Goal:** Determine the most efficient sequence of stops for each vehicle.
- **API:** Omelet `/api/vrp`
