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
        self.active_processes = {}

    def start_capture(self, namespace, pod_name, duration):
        # 파드 상태를 확인하고 Running 상태가 될 때까지 재시도
        if self.is_pod_ready(namespace, pod_name):
            self.capture_traffic(namespace, pod_name, duration)
        else:
            print(f"Waiting for pod {pod_name} to be ready. Retrying in 10 seconds...")
            threading.Timer(10, self.start_capture, args=[namespace, pod_name, duration]).start()

    def capture_traffic(self, namespace, pod_name, duration):
        start_time = datetime.now().strftime("%Y%m%d_%H%M%S.%f")[:-3]
        output_file = os.path.join(self.output_directory, f"{pod_name}_{start_time}.pcap")
        command = f"kubectl sniff {pod_name} -n {namespace} -o {output_file}"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        timer = threading.Timer(duration, lambda: self.terminate_capture(pod_name))
        timer.start()
        self.active_processes[pod_name] = (process, timer)

    def is_pod_ready(self, namespace, pod_name):
        v1 = client.CoreV1Api()
        pod = v1.read_namespaced_pod(pod_name, namespace)
        return pod.status.phase == "Running" and all(container.ready for container in pod.status.container_statuses)

    def terminate_capture(self, pod_name):
        if pod_name in self.active_processes:
            process, timer = self.active_processes[pod_name]
            timer.cancel()
            if process.poll() is None:
                process.terminate()
            print(f"Capture for {pod_name} has been terminated.")
            del self.active_processes[pod_name]

    def terminate_all(self):
        for pod_name in list(self.active_processes.keys()):
            self.terminate_capture(pod_name)
        print("All captures have been terminated.")

def monitor_pod_traffic(namespace, application, logger, duration):
    config.load_kube_config()
    v1 = client.CoreV1Api()
    known_pods = set()
    session_start_time = time.time()
    message_interval = 5
    last_message_time = time.time()

    print(f"Application_scan session for '{application}' started. (Duration: {duration}s)")
    try:
        while time.time() - session_start_time < duration:
            if time.time() - last_message_time >= message_interval:
                print("Collecting Application log")
                last_message_time = time.time()

            pods = v1.list_namespaced_pod(namespace, label_selector=f'app={application}')
            current_pods = set(pod.metadata.name for pod in pods.items)
            
            new_pods = current_pods - known_pods
            deleted_pods = known_pods - current_pods

            for pod in new_pods:
                print(f"Starting traffic capture for new pod: {pod}")
                logger.start_capture(namespace, pod, duration)

            for pod in deleted_pods:
                logger.terminate_capture(pod)

            known_pods.update(current_pods)
            time.sleep(1)

    except KeyboardInterrupt:
        print("Application_scan interrupted by user.")
        logger.terminate_all()
    finally:
        logger.terminate_all()
        print(f"Traffic logs have been created in the directory: {logger.output_directory}")
        print("Application_scan session ended.")

if __name__ == "__main__":
    output_directory = "./log"
    duration = 300
    logger = NetworkTrafficLogger(output_directory)
    namespace = "teastore"
    application = "teastore"
    monitor_pod_traffic(namespace, application, logger, duration)
