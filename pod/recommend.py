import pandas as pd

input_file = 'pod_communication_counts.csv'
df_routes = pd.read_csv(input_file, index_col=0)

def suggest_optimal_placement(df_routes, threshold=22981):
    nodes = ['worker', 'worker2']
    placement = {node: [] for node in nodes}
    pod_dependencies = []

    # Calculate the total communication count for each pod
    sorted_pods = df_routes.sum(axis=1).sort_values(ascending=False).index.tolist()
    
    # Identify pairs with high dependency based on a threshold
    for pod1 in df_routes.index:
        for pod2 in df_routes.columns:
            if pod1 != pod2 and df_routes.at[pod1, pod2] > threshold:
                pod_dependencies.append((pod1, pod2, df_routes.at[pod1, pod2]))
    
    # Sort dependencies by communication count (descending)
    pod_dependencies.sort(key=lambda x: x[2], reverse=True)
    
    # Place most communicative pods on different nodes initially
    for i, pod in enumerate(sorted_pods):
        node = nodes[i % len(nodes)]
        placement[node].append(pod)
    
    # Adjust placement to keep highly dependent pods together
    for pod1, pod2, count in pod_dependencies:
        node1 = next((node for node, pods in placement.items() if pod1 in pods), None)
        node2 = next((node for node, pods in placement.items() if pod2 in pods), None)
        
        if node1 and node2 and node1 != node2:
            # Try to move pod2 to node1
            if len(placement[node1]) < len(placement[node2]):
                placement[node1].append(pod2)
                placement[node2].remove(pod2)
            else:
                placement[node2].append(pod1)
                placement[node1].remove(pod1)
    
    return placement

optimal_placement = suggest_optimal_placement(df_routes, threshold=10)

# Display the optimal placement suggestion
print("Optimal Pod Placement:")
for node, pods in optimal_placement.items():
    print(f"{node}: {pods}")

