import os
import re
from datetime import datetime

precl_log_directory = './precl_log'
app_log_directory = '../application/app_log'
cl_log_directory = './cl_log'

def load_packet_timestamps(app_log_file):
    timestamps = []
    timestamp_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)')
    
    with open(app_log_file, 'r') as f:
        for line in f:
            match = timestamp_pattern.search(line)
            if match:
                timestamps.append(datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S.%f"))
    return timestamps

def detect_memory_changes(precl_log_file, packet_timestamps):
    changes = []
    memory_pattern = re.compile(r'"memory_usage":\s*(\d+\.?\d*)')
    timestamp_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)')
    last_memory_usage = None

    with open(precl_log_file, 'r') as f:
        for line in f:
            timestamp_match = timestamp_pattern.search(line)
            memory_match = memory_pattern.search(line)
            
            if timestamp_match and memory_match:
                log_time = datetime.strptime(timestamp_match.group(1), "%Y-%m-%d %H:%M:%S.%f")
                memory_usage = float(memory_match.group(1))
                
                if last_memory_usage is not None and any(pkt_time >= log_time for pkt_time in packet_timestamps):
                    memory_change = abs(memory_usage - last_memory_usage)
                    if memory_change > 0:
                        changes.append(line)
                
                last_memory_usage = memory_usage
    
    return changes

def save_changes(cl_log_file, changes):
    with open(cl_log_file, 'w') as f:
        for change in changes:
            f.write(change)

def main():
    if not os.path.exists(cl_log_directory):
        os.makedirs(cl_log_directory)

    for app_log_filename in os.listdir(app_log_directory):
        if app_log_filename.startswith('app_') and app_log_filename.endswith('.pcap.log'):
            app_log_file = os.path.join(app_log_directory, app_log_filename)
            pod_specific_name = app_log_filename.split('app_')[1].replace('.pcap.log', '')
            precl_filename = f'precl_{pod_specific_name}.log'
            precl_log_file = os.path.join(precl_log_directory, precl_filename)
            cl_filename = f'cl_{pod_specific_name}.log'
            cl_log_file = os.path.join(cl_log_directory, cl_filename)

            packet_timestamps = load_packet_timestamps(app_log_file)
            print(f"Loaded {len(packet_timestamps)} packet timestamps from {app_log_file}")

            if os.path.exists(precl_log_file):
                changes = detect_memory_changes(precl_log_file, packet_timestamps)
                print(f"Detected {len(changes)} changes from {precl_log_file}")

                save_changes(cl_log_file, changes)
                print(f"Saved changes to {cl_log_file}")
            else:
                print(f"File not found: {precl_log_file}")

if __name__ == "__main__":
    main()

