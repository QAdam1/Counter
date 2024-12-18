import osmnx as ox
import networkx as nx
from geopy.geocoders import Nominatim
import folium
import logging
from heapq import heappush, heappop

def yen_k_shortest_paths(graph, source, target, k, weight='length'):
    """Find k shortest paths between source and target using Yen's algorithm."""
    def path_length(path):
        return sum(graph[u][v][weight] for u, v in zip(path[:-1], path[1:]))

    shortest_paths = []
    potential_paths = []
    # Find the initial shortest path
    try:
        initial_path = nx.shortest_path(graph, source, target, weight=weight)
        shortest_paths.append(initial_path)
    except nx.NetworkXNoPath:
        return []

    for i in range(1, k):
        for j in range(len(shortest_paths[-1]) - 1):
            # Create a spur path
            spur_node = shortest_paths[-1][j]
            root_path = shortest_paths[-1][:j + 1]
            edges_removed = []

            for path in shortest_paths:
                if path[:j + 1] == root_path:
                    try:
                        edge_data = graph[spur_node][path[j + 1]].copy()
                        graph.remove_edge(spur_node, path[j + 1])
                        edges_removed.append((spur_node, path[j + 1], edge_data))
                    except KeyError:
                        pass

            try:
                spur_path = nx.shortest_path(graph, spur_node, target, weight=weight)
                total_path = root_path[:-1] + spur_path
                heappush(potential_paths, (path_length(total_path), total_path))
            except nx.NetworkXNoPath:
                pass

            # Restore removed edges
            for u, v, edge_data in edges_removed:
                graph.add_edge(u, v, **edge_data)

        if not potential_paths:
            break

        _, next_shortest_path = heappop(potential_paths)
        shortest_paths.append(next_shortest_path)

    return shortest_paths


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("route_optimizer.log"),
        logging.StreamHandler()
    ]
)

# Geocode the addresses to get accurate coordinates
logging.info("Starting the geocoding process...")
geolocator = Nominatim(user_agent="route_optimizer")
start_address = "פנחס רוזן 72, תל אביב"
end_address = "שדרת התמרים 9, רמת גן"

try:
    start_location = geolocator.geocode(start_address)
    end_location = geolocator.geocode(end_address)

    if not start_location or not end_location:
        raise ValueError("Could not geocode one of the addresses.")

    start_coords = (start_location.latitude, start_location.longitude)
    end_coords = (end_location.latitude, end_location.longitude)
    logging.info(f"Geocoded start address: {start_address} -> {start_coords}")
    logging.info(f"Geocoded end address: {end_address} -> {end_coords}")
except Exception as e:
    logging.error(f"Error during geocoding: {e}")
    raise

# Download the road network for the area
logging.info("Downloading a larger road network...")
try:
    G = ox.graph_from_point(start_coords, dist=25000, network_type='drive')  # Increase distance
    logging.info("Larger road network downloaded successfully.")
except Exception as e:
    logging.error(f"Error downloading road network: {e}")
    raise

# Find the nearest nodes to the start and end points
logging.info("Finding nearest nodes for start and end points...")
try:
    start_node = ox.distance.nearest_nodes(G, start_coords[1], start_coords[0])
    end_node = ox.distance.nearest_nodes(G, end_coords[1], end_coords[0])
    logging.info(f"Nearest node to start: {start_node}")
    logging.info(f"Nearest node to end: {end_node}")
except Exception as e:
    logging.error(f"Error finding nearest nodes: {e}")
    raise

# Convert MultiDiGraph to DiGraph by choosing the shortest edge for each pair of nodes
logging.info("Converting MultiDiGraph to DiGraph...")
try:
    G_simplified = nx.DiGraph()

    # Copy nodes and their attributes
    G_simplified.add_nodes_from((node, data) for node, data in G.nodes(data=True))

    # Copy edges with the shortest length
    for u, v, data in G.edges(data=True):
        if G_simplified.has_edge(u, v):
            # Replace with the edge that has the smallest length
            if data['length'] < G_simplified[u][v]['length']:
                G_simplified[u][v].update(data)
        else:
            # Add the edge
            G_simplified.add_edge(u, v, **data)
    logging.info("Conversion to DiGraph completed successfully.")
except Exception as e:
    logging.error(f"Error converting graph: {e}")
    raise

# Generate multiple routes using NetworkX's shortest_simple_paths
logging.info("Generating multiple driving routes using Yen's K-Shortest Paths...")
try:
    k = 250  # Number of routes to generate
    routes = yen_k_shortest_paths(G_simplified, start_node, end_node, k, weight='length')
    logging.info(f"Generated {len(routes)} possible routes.")
except Exception as e:
    logging.error(f"Error generating routes: {e}")
    raise

# Convert routes to coordinates
def route_to_coordinates(route, graph):
    return [(graph.nodes[node]['y'], graph.nodes[node]['x']) for node in route]

routes_coords = [route_to_coordinates(route, G_simplified) for route in routes]

# Create a Folium map
logging.info("Creating an interactive map with all routes...")
map_center = ((start_coords[0] + end_coords[0]) / 2, (start_coords[1] + end_coords[1]) / 2)
m = folium.Map(location=map_center, zoom_start=14)

# Add routes to the map
colors = ["red", "blue", "green", "purple", "orange"]  # Assign a color for each route
for i, coords in enumerate(routes_coords):
    folium.PolyLine(
        coords,
        color=colors[i % len(colors)],
        weight=4,
        opacity=0.7,
        tooltip=f"Route {i + 1}"
    ).add_to(m)

# Add start and end points
folium.Marker(start_coords, popup="Start Point", icon=folium.Icon(color="yellow")).add_to(m)
folium.Marker(end_coords, popup="End Point", icon=folium.Icon(color="purple")).add_to(m)

# Save the map to an HTML file
output_file = "all_routes_map.html"
m.save(output_file)
logging.info(f"Map with all routes saved to {output_file}")
# Notify user
logging.info(f"Open {output_file} in a browser to view all possible routes.")
