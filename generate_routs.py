import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
from math import radians, cos, sin, sqrt, atan2

# Step 1: Define locations (latitude, longitude)
start_coords = (32.100636, 34.824439)  # Pinhas Rosen Street, Tel Aviv-Yafo
end_coords = (32.083509, 34.812152)    # Ben Gurion Road, Ramat Gan

# Step 2: Download the road network for the area
G = ox.graph_from_point(start_coords, dist=2000, network_type='drive')

# Step 3: Find the nearest nodes to the start and end points
start_node = ox.distance.nearest_nodes(G, start_coords[1], start_coords[0])
end_node = ox.distance.nearest_nodes(G, end_coords[1], end_coords[0])

# Step 4: Define a heuristic function for A* (Haversine formula)
def haversine_heuristic(u, v):
    lat1, lon1 = G.nodes[u]['y'], G.nodes[u]['x']
    lat2, lon2 = G.nodes[v]['y'], G.nodes[v]['x']
    R = 6371  # Radius of the Earth in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c * 1000  # Distance in meters

# Step 5: Generate and visualize multiple routes
route_shortest = nx.shortest_path(G, start_node, end_node, weight='length')
route_dijkstra = nx.shortest_path(G, start_node, end_node, method='dijkstra')
route_astar = nx.astar_path(G, start_node, end_node, heuristic=haversine_heuristic)

# Plot the routes
fig, ax = ox.plot_graph_routes(
    G, 
    [route_shortest, route_dijkstra, route_astar],
    route_colors=['red', 'blue', 'green'],
    orig_dest_node_size=100,
    figsize=(12, 8)
)

plt.title("Alternative Routes Between Pinhas Rosen St and Ben Gurion Rd")
plt.show()