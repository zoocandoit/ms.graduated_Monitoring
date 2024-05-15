import os
import json
import pandas as pd

log_directory = '../cluster/cl_log'
output_csv_path = 'Pod_communication_dep.csv'

def read_memory_data(file_path):
    memory_data = []
    with open(file_path, 'r') as file:
        for line in file:
            log_entry = json.loads(line.strip())
            memory_data.append(log_entry["memory_usage"])
    return memory_data

def calculate_memory_change(memory_data):
    if not memory_data:
        return 0
    max_memory = max(memory_data)
    min_memory = min(memory_data)
    return max_memory - min_memory

memory_changes = {}

for filename in os.listdir(log_directory):
    if filename.startswith('cl_') and filename.endswith('.log'):
        pod_name = filename[len('cl_'):-len('.log')]
        file_path = os.path.join(log_directory, filename)
        memory_data = read_memory_data(file_path)
        memory_change = calculate_memory_change(memory_data)
        memory_changes[pod_name] = memory_change

sorted_pods = sorted(memory_changes.items(), key=lambda item: item[1], reverse=True)

priority_scores = {pod: len(sorted_pods) - idx for idx, (pod, _) in enumerate(sorted_pods)}

print("Pod Memory Change Priority List with Scores:")
for pod, change in sorted_pods:
    score = priority_scores[pod]
    print(f"{pod}: {change} bytes, Score: {score}")

pod_list = list(priority_scores.keys())
dependency_matrix = pd.DataFrame(index=pod_list, columns=pod_list)

for i, pod_a in enumerate(pod_list):
    for j, pod_b in enumerate(pod_list):
        if i != j:
            dependency_matrix.at[pod_a, pod_b] = priority_scores[pod_a] + priority_scores[pod_b]
        else:
            dependency_matrix.at[pod_a, pod_b] = 0

dependency_matrix.to_csv(output_csv_path)

print(f"Dependency matrix saved to {output_csv_path}")

