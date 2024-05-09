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
        if self.is_pod_ready(namespace, pod_name):
            self.capture_traffic(namespace, pod_name, duration)
        else:
            print(f"Application_Waiting for pod {pod_name} to be ready. Retrying in 10 seconds...")
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
            print(f"Application_Capture for {pod_name} has been terminated.")
            del self.active_processes[pod_name]



    def terminate_all(self):
        for pod_name in list(self.active_processes.keys()):
            self.terminate_capture(pod_name)
        print("Application_All captures have been terminated.")



def monitor_application_traffic(namespace, application, logger, session_duration):
    config.load_kube_config()
    v1 = client.CoreV1Api()
    known_pods = set()
    session_start_time = time.time()
    message_interval = 5
    last_message_time = time.time()

    print(f"Application_scan session for '{application}' started. (Duration: {session_duration}s)")
    try:
        while time.time() - session_start_time < session_duration:
            if time.time() - last_message_time >= message_interval:
                print("Application_Collecting log")
                last_message_time = time.time()

            pods = v1.list_namespaced_pod(namespace, label_selector=f'app={application}')
            current_pods = set(pod.metadata.name for pod in pods.items)
            
            new_pods = current_pods - known_pods
            deleted_pods = known_pods - current_pods

            for pod in new_pods:
                print(f"Application_New pod detected: {pod}")
                logger.start_capture(namespace, pod, session_duration)

            for pod in deleted_pods:
                print(f"Application_Pod deleted: {pod}")
                logger.terminate_capture(pod)

            known_pods.update(current_pods)
            time.sleep(1)

    except KeyboardInterrupt:
        print("Application_scan interrupted by user.")
        logger.terminate_all()
    finally:
        logger.terminate_all()
        print("Application_scan session ended.")
        print(f"Application_scan logs have been created: {logger.output_directory}")




if __name__ == "__main__":
    output_directory = "./application/log"
    session_duration = 30
    logger = NetworkTrafficLogger(output_directory)
    namespace = "teastore"
    application = "teastore"
    monitor_application_traffic(namespace, application, logger, session_duration)

