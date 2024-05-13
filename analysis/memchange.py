import os
import re
import json
import subprocess
from datetime import datetime

pre_cl_log_directory = '../cluster/precl_log'
cl_log_directory = '../cluster/cl_log'
app_log_directory = '../application/app_log'
output_directory = './memchange_output'

def load_ip_pod_mapping(namespace='teastore'):
    ip_pod_mapping = {}
    try:
        result = subprocess.run(
            ['kubectl', 'get', 'pods', '-o', 'wide', '-n', namespace],
            stdout=subprocess.PIPE, text=True, check=True
        )
        lines = result.stdout.splitlines()
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 6:
                pod_name = parts[0]
                ip_address = parts[5]
                ip_pod_mapping[ip_address] = pod_name
    except subprocess.CalledProcessError as e:
        print(f"Error fetching pod IP mappings: {e}")
    return ip_pod_mapping

def load_memory_changes(cl_log_file):
    changes = []
    timestamp_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)')
    
    with open(cl_log_file, 'r') as f:
        for line in f:
            match = timestamp_pattern.search(line)
            if match:
                log_time = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S.%f")
                try:
                    log_data = json.loads(line[line.index('{'):])  # JSON 부분만 추출
                    changes.append((log_time, log_data['memory_usage']))
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Error parsing JSON from line: {line}")
    return changes

def map_packets_to_memory_changes(app_log_file, memory_changes, ip_pod_mapping):
    timestamp_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)')
    packet_pattern = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) → (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')

    memory_change_index = 0
    memory_change_data = []

    with open(app_log_file, 'r') as app_log:
        for line in app_log:
            match = timestamp_pattern.search(line)
            if match:
                pkt_time = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S.%f")
                while memory_change_index < len(memory_changes) and memory_changes[memory_change_index][0] < pkt_time:
                    memory_change_index += 1
                if memory_change_index < len(memory_changes) and abs((pkt_time - memory_changes[memory_change_index][0]).total_seconds()) <= 2:
                    packet_match = packet_pattern.search(line)
                    if packet_match:
                        src_ip, dst_ip = packet_match.groups()
                        src_pod = ip_pod_mapping.get(src_ip, src_ip)
                        dst_pod = ip_pod_mapping.get(dst_ip, dst_ip)
                        if 'teastore' in src_pod and 'teastore' in dst_pod:
                            memory_change_data.append({
                                'timestamp': pkt_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
                                'source_pod': src_pod,
                                'destination_pod': dst_pod,
                                'memory_usage': memory_changes[memory_change_index][1]
                            })
    return memory_change_data

def save_related_packets(output_file, related_packets):
    with open(output_file, 'w') as f:
        for packet in related_packets:
            f.write(json.dumps(packet) + '\n')

def main():
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    ip_pod_mapping = load_ip_pod_mapping()

    for cl_log_filename in os.listdir(cl_log_directory):
        if cl_log_filename.startswith('cl_') and cl_log_filename.endswith('.log'):
            cl_log_file = os.path.join(cl_log_directory, cl_log_filename)
            pod_specific_name = cl_log_filename.split('cl_')[1].replace('.log', '')
            pre_cl_filename = f'pre_cl_{pod_specific_name}.log'
            pre_cl_log_file = os.path.join(pre_cl_log_directory, pre_cl_filename)
            app_log_filename = f'app_{pod_specific_name}.pcap.log'
            app_log_file = os.path.join(app_log_directory, app_log_filename)
            output_filename = f'related_packets_{pod_specific_name}.log'
            output_file = os.path.join(output_directory, output_filename)

            memory_changes = load_memory_changes(cl_log_file)
            print(f"Loaded {len(memory_changes)} memory changes from {cl_log_file}")

            related_packets = map_packets_to_memory_changes(app_log_file, memory_changes, ip_pod_mapping)
            print(f"Found {len(related_packets)} related packets for memory changes")

            save_related_packets(output_file, related_packets)
            print(f"Saved related packets to {output_file}")

if __name__ == "__main__":
    main()

