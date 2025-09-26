# Last-Mile Delivery & Navigation Workflow

This guide outlines a streamlined, four-step process for last-mile delivery, with navigation path generation.

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

---

### **Step 4: Generate Final Navigation Path**

- **Goal:** Create navigable routes that can be visualized on a map.
- **API:** iNavi `/maps/v3.0/appkeys/{appkey}/route-normal-via`
