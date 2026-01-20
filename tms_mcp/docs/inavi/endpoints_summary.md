# iNavi Maps API
**Base URL:** `https://imaps.inavi.com`

## Endpoints
| Path | Method | Summary | Description |
|------|--------|---------|-------------|
| /maps/v3.0/appkeys/{appkey}/route-time | POST | General Route Prediction Search | Predicts a route and returns detailed guidance based on a specified estimated departure or arrival time, using the coordinates of an origin, destination, and optional waypoints. |
| /maps/v3.0/appkeys/{appkey}/route-normal-via | POST | Multi-Waypoint Route Search | Returns optimized route information based on a search using an origin, a destination, and up to 100 waypoints. Performs route searches using various strategies based on request parameters, such as reflecting real-time traffic, prioritizing the shortest distance, or optimizing for motorcycles. |
| /maps/v3.0/appkeys/{appkey}/route-distance-matrix | POST | Route Distance Matrix | Searches for drivable routes between multiple origin/destination points and returns distance and time information. |
| /maps/v3.0/appkeys/{appkey}/coordinates | GET | Geocoding | Returns coordinate information corresponding to the input address. |
