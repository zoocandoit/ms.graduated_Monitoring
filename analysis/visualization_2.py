import os
import re
import json

log_dir = '../cluster/cl_log'

def extract_memory_usage(log_file):
    memory_usages = []
    with open(log_file, 'r') as file:
        for line in file:
            try:
                log_data = json.loads(line.strip())
                if 'memory_usage' in log_data:
                    memory_usages.append(int(log_data['memory_usage']))
            except json.JSONDecodeError:
                continue
    return memory_usages

def calculate_memory_amplitude(memory_usages):
    if not memory_usages:
        return 0
    return max(memory_usages)

memory_amplitudes = {}
for log_file in os.listdir(log_dir):
    if log_file.endswith('.log'):
        pod_name = log_file.split('.')[0]
        memory_usages = extract_memory_usage(os.path.join(log_dir, log_file))
        memory_amplitudes[pod_name] = calculate_memory_amplitude(memory_usages)

ranked_pods = sorted(memory_amplitudes.items(), key=lambda x: x[1], reverse=True)

print("Pod Ranking based on Memory Amplitude from 0:")
for rank, (pod, amplitude) in enumerate(ranked_pods, start=1):
    print(f"{rank}. Pod: {pod}, Memory Amplitude: {amplitude} bytes")

