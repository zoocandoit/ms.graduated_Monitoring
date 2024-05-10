import os
import subprocess


pcap_directory = "./pcap"
txt_directory = "./log"

os.makedirs(txt_directory, exist_ok=True)

for filename in os.listdir(pcap_directory):
    if filename.endswith(".pcap"):
        pcap_path = os.path.join(pcap_directory, filename)
        txt_filename = f"{filename}.log"
        txt_path = os.path.join(txt_directory, txt_filename)


        command = f"tshark -r {pcap_path} -t ad -T text > {txt_path}"
        try:
            subprocess.run(command, shell=True, check=True)
            print(f"Converted {pcap_path} to {txt_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error converting {pcap_path}: {e}")

