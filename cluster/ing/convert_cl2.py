import re
import os

app_log_directory = '../application/log'
pre_cl_log_directory = './pre_log'
cl_log_directory = './log'

def extract_timestamps(app_log_file):
    timestamps = set()
    timestamp_pattern = re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+')

    with open(app_log_file, 'r') as f:
        for line in f:
            match = timestamp_pattern.search(line)
            if match:
                timestamps.add(match.group(0))
    return timestamps

def filter_logs(pre_cl_log_file, timestamps, cl_log_file):
    with open(pre_cl_log_file, 'r') as pre_cl, open(cl_log_file, 'w') as cl:
        for line in pre_cl:
            match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+', line)
            if match:
                log_timestamp = match.group(0)
                if log_timestamp in timestamps:
                    cl.write(line)

def generate_cl_filename(pre_cl_filename):
    return pre_cl_filename.replace('pre_cl_', 'cl_')

def main():
    if not os.path.exists(cl_log_directory):
        os.makedirs(cl_log_directory)

    for app_log_filename in os.listdir(app_log_directory):
        if app_log_filename.startswith('app_') and app_log_filename.endswith('.pcap.log'):
            app_log_file = os.path.join(app_log_directory, app_log_filename)
            
            pod_specific_name = app_log_filename.split('app_')[1].replace('.pcap.log', '')  
            pre_cl_filename = f'pre_cl_{pod_specific_name}.log'
            pre_cl_log_file = os.path.join(pre_cl_log_directory, pre_cl_filename)
            
            cl_filename = generate_cl_filename(pre_cl_filename)
            cl_log_file = os.path.join(cl_log_directory, cl_filename)
            
            timestamps = extract_timestamps(app_log_file)
            print(f"Extracted {len(timestamps)} timestamps from {app_log_file}")
            
            if os.path.exists(pre_cl_log_file):
                filter_logs(pre_cl_log_file, timestamps, cl_log_file)
                print(f"Filtered logs saved to {cl_log_file}")
            else:
                print(f"File not found: {pre_cl_log_file}")

if __name__ == "__main__":
    main()

