import pandas as pd

def suggest_optimal_placement(df_routes, threshold, nodes):
    placement = {node: [] for node in nodes}
    pod_dependencies = []

    sorted_pods = df_routes.sum(axis=1).sort_values(ascending=False).index.tolist()

    print(f"Calculated threshold: {threshold}")

    for pod1 in df_routes.index:
        for pod2 in df_routes.columns:
            if pod1 != pod2 and df_routes.at[pod1, pod2] > threshold:
                pod_dependencies.append((pod1, pod2, df_routes.at[pod1, pod2]))
    
    pod_dependencies.sort(key=lambda x: x[2], reverse=True)
    
    for i, pod in enumerate(sorted_pods):
        node = nodes[i % len(nodes)]
        placement[node].append(pod)
    
    for pod1, pod2, count in pod_dependencies:
        node1 = next((node for node, pods in placement.items() if pod1 in pods), None)
        node2 = next((node for node, pods in placement.items() if pod2 in pods), None)
        
        if node1 and node2 and node1 != node2:
            if len(placement[node1]) < len(placement[node2]):
                placement[node1].append(pod2)
                placement[node2].remove(pod2)
            else:
                placement[node2].append(pod1)
                placement[node1].remove(pod1)
    
    return placement

def main():
    input_file = 'pod_communication_counts.csv'
    df_routes = pd.read_csv(input_file, index_col=0)
    
    N = int(input("Enter the number of nodes: "))
    nodes = [f'worker{i+1}' for i in range(N)]

    all_counts = df_routes.values.flatten()
    non_zero_counts = all_counts[all_counts > 0]

    mean_threshold = non_zero_counts.mean() if len(non_zero_counts) > 0 else 0

    mean_placement = suggest_optimal_placement(df_routes, mean_threshold, nodes)

    print("\nOptimal Pod Placement using Mean Threshold:")
    for node, pods in mean_placement.items():
        print(f"{node}: {pods}")

if __name__ == "__main__":
    main()

