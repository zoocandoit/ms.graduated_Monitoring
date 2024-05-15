import os
import re

log_dir = './preapp_log'
output_dir = './app_log'

def filter_http_methods(log_file, output_file, methods=["GET", "POST", "PUT"]):
    pattern = re.compile(r'\b(?:' + '|'.join(methods) + r')\b')
    with open(log_file, 'r') as file, open(output_file, 'w') as outfile:
        for line in file:
            if pattern.search(line):
                outfile.write(line)

def process_logs(log_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for log_file in os.listdir(log_dir):
        if log_file.endswith('.log'):
            input_file_path = os.path.join(log_dir, log_file)
            output_file_path = os.path.join(output_dir, log_file.replace('.log', '.filtered.log'))
            filter_http_methods(input_file_path, output_file_path)
            print(f"Filtered log created: {output_file_path}")

if __name__ == "__main__":
    process_logs(log_dir, output_dir)

