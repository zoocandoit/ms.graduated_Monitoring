import os
import json
import pandas as pd

output_directory = './memchange_output'
csv_output_file = './pod_communication_weights.csv'

def calculate_memory_changes():
    pod_memory_changes = {}

    for output_filename in os.listdir(output_directory):
        if output_filename.startswith('related_packets_') and output_filename.endswith('.log'):
            output_file = os.path.join(output_directory, output_filename)
            
            with open(output_file, 'r') as f:
                for line in f:
                    try:
                        packet_data = json.loads(line)
                        src_pod = packet_data['source_pod']
                        dst_pod = packet_data['destination_pod']
                        memory_usage = packet_data['memory_usage']

                        key = tuple(sorted((src_pod, dst_pod)))
                        if key not in pod_memory_changes:
                            pod_memory_changes[key] = 0
                        pod_memory_changes[key] += memory_usage

                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON from line: {line}")

    return pod_memory_changes

def save_memory_changes_to_csv(pod_memory_changes):
    if pod_memory_changes:
        max_memory_change = max(pod_memory_changes.values())
    else:
        max_memory_change = 0
    
    df = pd.DataFrame(
        [
            (pods[0], pods[1], change, change / max_memory_change if max_memory_change > 0 else 0)
            for pods, change in pod_memory_changes.items()
        ],
        columns=['source_pod', 'destination_pod', 'memory_change', 'weight']
    )
    df.to_csv(csv_output_file, index=False)
    print(f"Memory changes with weights saved to {csv_output_file}")

def main():
    pod_memory_changes = calculate_memory_changes()
    save_memory_changes_to_csv(pod_memory_changes)

if __name__ == "__main__":
    main()

