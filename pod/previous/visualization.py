import os
import re
import subprocess
from collections import defaultdict, Counter
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

log_directory = '../application/log/'


def get_log_files(directory):
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.log')]


filenames = get_log_files(log_directory)



def get_ip_to_pod_mapping():
    ip_to_pod = {}
    try:
        result = subprocess.run(['kubectl', 'get', 'pods', '-o', 'wide', '-n', 'teastore'],
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

ip_to_pod_mapping = get_ip_to_pod_mapping()



def parse_all_routes(filenames, ip_mapping):
    all_routes = defaultdict(set)
    
    for filename in filenames:
        with open(filename, 'r') as file:
            log_data = file.readlines()
        
        pod_name = filename.split('/')[-1].split('_')[0]
        
        for line in log_data:
            match = re.search(r'(\d+\.\d+\.\d+\.\d+) → (\d+\.\d+\.\d+\.\d+)', line)
            if match:
                source_ip = match.group(1)
                destination_ip = match.group(2)
                if source_ip in ip_mapping and destination_ip in ip_mapping:
                    source_pod = ip_mapping[source_ip]
                    destination_pod = ip_mapping[destination_ip]
                    all_routes[source_pod].add(destination_pod)
    
    return all_routes


all_routes = parse_all_routes(filenames, ip_to_pod_mapping)


G = nx.DiGraph()

for source, destinations in all_routes.items():
    for destination in destinations:
        G.add_edge(source, destination)

plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G, seed=42)  
nx.draw(G, pos, with_labels=True, node_size=4000, node_color="lightblue", 
        font_size=10, font_weight="bold", arrows=True, arrowstyle='-|>', arrowsize=8)
plt.title("Teastore Service Pod Communication Graph")
plt.show()

