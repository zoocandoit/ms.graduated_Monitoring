import os
import subprocess
import re

pcap_directory = "./pcap"
txt_directory = "./preapp_log"

os.makedirs(txt_directory, exist_ok=True)

def remove_line_numbers(log_file):
    temp_file = log_file + ".tmp"
    with open(log_file, 'r') as infile, open(temp_file, 'w') as outfile:
        for line in infile:
            cleaned_line = re.sub(r'^\s*\d+\s+', '', line)
            outfile.write(cleaned_line)
    os.replace(temp_file, log_file)

for filename in os.listdir(pcap_directory):
    if filename.endswith(".pcap"):
        pcap_path = os.path.join(pcap_directory, filename)
        txt_filename = f"{filename}.log"
        txt_path = os.path.join(txt_directory, txt_filename)

        command = f"tshark -r {pcap_path} -t ud -T text > {txt_path}"
        try:
            subprocess.run(command, shell=True, check=True)
            print(f"Converted {pcap_path} to {txt_path}")

            remove_line_numbers(txt_path)
            print(f"Removed line numbers from {txt_path}")

        except subprocess.CalledProcessError as e:
            print(f"Error converting {pcap_path}: {e}")

