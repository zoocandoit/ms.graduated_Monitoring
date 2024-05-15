import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# Load the communication counts and dependency matrices
comm_counts_path = 'pod_communication_counts.csv'
dep_matrix_path = 'Pod_communication_dep.csv'

comm_counts_df = pd.read_csv(comm_counts_path, index_col=0)
dep_matrix_df = pd.read_csv(dep_matrix_path, index_col=0)

# Create a directed graph
G = nx.DiGraph()

# Add edges with weights (dependency scores) to the graph
for source in comm_counts_df.index:
    for destination in comm_counts_df.columns:
        if comm_counts_df.at[source, destination] > 0:  # Only add edges where communication occurs
            weight = dep_matrix_df.at[source, destination]
            if weight > 0:
                G.add_edge(source, destination, weight=weight)

# Draw the graph
plt.figure(figsize=(14, 10))
pos = nx.spring_layout(G, seed=42)
edges = G.edges(data=True)

nx.draw(G, pos, node_size=500, node_color="lightblue", 
        arrows=True, arrowstyle='-|>', arrowsize=8)

pos_labels = {node: (coords[0], coords[1] - 0.03) for node, coords in pos.items()}
nx.draw_networkx_labels(G, pos_labels, labels={node: node for node in G.nodes()}, 
                        font_size=10, font_weight="bold", 
                        verticalalignment='top', horizontalalignment='center')

edge_labels = {(u, v): d['weight'] for u, v, d in edges}
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, label_pos=0.5, font_size=9, bbox=dict(facecolor='white', edgecolor='none', alpha=0.7))

plt.title('Pod Communication Dependency Graph')
plt.show()

print("Dependency graph visualization complete")

