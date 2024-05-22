import os

criteria = ["HTTP/1.1 200", "MYSQL"]

def filter_logs(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
        filtered_lines = [line for line in lines if any(criterion.lower() in line.lower() for criterion in criteria)]
    return filtered_lines

log_directory = "./preapp_log"
output_directory = "./app_log"
os.makedirs(output_directory, exist_ok=True)

log_files = [os.path.join(log_directory, file) for file in os.listdir(log_directory) if file.endswith('.log')]

output_paths = {}
for file in log_files:
    filtered_lines = filter_logs(file)
    output_file_path = os.path.join(output_directory, os.path.basename(file).replace('.log', '_filtered.log'))
    with open(output_file_path, 'w') as output_file:
        output_file.writelines(filtered_lines)
    output_paths[file] = output_file_path

output_paths

