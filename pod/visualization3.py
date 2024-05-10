import os
import re
import subprocess
from collections import defaultdict, Counter
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

log_directory = '../application/log/'
namespace = 'teastore'
output_file = 'pod_communication_counts.csv'

def get_log_files(directory):
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.log')]

filenames = get_log_files(log_directory)

def get_ip_to_pod_mapping(namespace):
    ip_to_pod = {}
    try:
        result = subprocess.run(['kubectl', 'get', 'pods', '-o', 'wide', '-n', namespace],
                                stdout=subprocess.PIPE, text=True)
        lines = result.stdout.splitlines()
        for line in lines[1:]:  # Skip header line
            parts = line.split()
            if len(parts) >= 6:
                pod_name = parts[0]
                ip_address = parts[5]
                ip_to_pod[ip_address] = pod_name
    except Exception as e:
        print(f"Error getting pod info: {e}")
    return ip_to_pod

ip_to_pod_mapping = get_ip_to_pod_mapping(namespace)



def parse_all_routes_with_counts(filenames, ip_mapping):
    all_routes = defaultdict(Counter)
    
    for filename in filenames:
        with open(filename, 'r') as file:
            log_data = file.readlines()
        
        for line in log_data:
            match = re.search(r'(\d+\.\d+\.\d+\.\d+) → (\d+\.\d+\.\d+\.\d+)', line)
            if match:
                source_ip = match.group(1)
                destination_ip = match.group(2)
                if source_ip in ip_mapping and destination_ip in ip_mapping:
                    source_pod = ip_mapping[source_ip]
                    destination_pod = ip_mapping[destination_ip]
                    all_routes[source_pod][destination_pod] += 1
    
    return all_routes

all_routes_counts = parse_all_routes_with_counts(filenames, ip_to_pod_mapping)

all_pods = set(ip_to_pod_mapping.values())
for pod in all_pods:
    if pod not in all_routes_counts:
        all_routes_counts[pod] = Counter()
    for inner_pod in all_pods:
        if inner_pod not in all_routes_counts[pod]:
            all_routes_counts[pod][inner_pod] = 0



df_routes = pd.DataFrame(all_routes_counts).fillna(0).astype(int)
df_routes.to_csv(output_file, index=True)
print(f"Pod Communication Counts saved to {output_file}")




# Create a directed graph
G = nx.DiGraph()

for source, destinations in all_routes_counts.items():
    for destination, count in destinations.items():
        if count > 0:
            G.add_edge(source, destination, weight=count)

plt.figure(figsize=(14, 10))
pos = nx.spring_layout(G, seed=42)
edges = G.edges(data=True)

nx.draw(G, pos, node_size=500, node_color="lightblue", 
        arrows=True, arrowstyle='-|>', arrowsize=8)


pos_labels = {node: (coords[0], coords[1] - 0.02) for node, coords in pos.items()}
nx.draw_networkx_labels(G, pos_labels, labels={node: node for node in G.nodes()}, 
                        font_size=10, font_weight="bold", 
                        verticalalignment='top', horizontalalignment='center')


edge_labels = {(u, v): d['weight'] for u, v, d in edges}
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, label_pos=0.5, font_size=9, bbox=dict(facecolor='white', edgecolor='none', alpha=0.7))

plt.show()

