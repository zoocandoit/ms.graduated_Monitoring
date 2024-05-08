import subprocess
import os
import threading
import time
from datetime import datetime
from kubernetes import client, config

class NetworkTrafficLogger:
    def __init__(self, output_directory):
        os.makedirs(output_directory, exist_ok=True)
        self.output_directory = output_directory
        self.active_processes = []

    def capture_traffic(self, namespace, pod_name, duration):
        start_time = datetime.now().strftime("%Y%m%d_%H%M%S.%f")[:-3]
        output_file = os.path.join(self.output_directory, f"{pod_name}_{start_time}.pcap")
        command = f"kubectl sniff {pod_name} -n {namespace} -o {output_file}"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.active_processes.append(process)
        timer = threading.Timer(duration, process.terminate)
        timer.start()
        process.wait()
        timer.cancel()

    def terminate_all(self):
        for process in self.active_processes:
            if process.poll() is None:
                process.terminate()
        print("All captures have been terminated.")

def monitor_pod_traffic(namespace, application, logger, duration):
    config.load_kube_config()
    v1 = client.CoreV1Api()
    pods = v1.list_namespaced_pod(namespace, label_selector=f'app={application}')
    session_start_time = time.time()
    session_duration = duration
    last_message_time = time.time()

    message_interval = 5

    print(f"Application_scan session for '{application}' started. (Duration: {session_duration}s)")
    try:
        for pod in pods.items:
            pod_name = pod.metadata.name
            print(f"Starting traffic capture for {pod_name}")
            threading.Thread(target=logger.capture_traffic, args=(namespace, pod_name, duration)).start()

        while threading.active_count() > 1:
            if time.time() - last_message_time >= message_interval:
                print("Collecting Application log")
                last_message_time = time.time()
            time.sleep(1)
        print("All captures have completed.")

    except KeyboardInterrupt:
        print("Application_scan interrupted by user.")
        logger.terminate_all()
    finally:
        print(f"Traffic logs have been created in the directory: {logger.output_directory}")
        print("Application_scan session ended.")

if __name__ == "__main__":
    output_directory = "./log"
    duration = 60
    logger = NetworkTrafficLogger(output_directory)
    namespace = "teastore"
    application = "teastore"
    monitor_pod_traffic(namespace, application, logger, duration)

