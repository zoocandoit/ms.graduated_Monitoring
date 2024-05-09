import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
import json
from kubernetes import client, config
from prometheus_client import start_http_server
import time, requests

class MonitorLogger:
    def __init__(self, log_directory, max_bytes=10485760, backup_count=5, buffer_size=10):
        self.buffer = []
        self.buffer_size = buffer_size
        start_time = datetime.now().strftime("%Y%m%d_%H%M%S.%f")[:-3]
        log_filename = f"cluster_{start_time}.log"
        os.makedirs(log_directory, exist_ok=True)
        self.output_directory = output_directory

        self.logger = logging.getLogger(f"MonitorLogger_{start_time}")
        self.logger.setLevel(logging.INFO)
        handler = RotatingFileHandler(
            filename=os.path.join(log_directory, log_filename),
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)


    def log(self, timestamp, pod_name, node_name, cpu_usage, memory_usage):
        log_message = json.dumps({
            "timestamp": timestamp,
            "pod_name": pod_name,
            "node_name": node_name,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage
        })
        self.buffer.append(log_message)
        if len(self.buffer) >= self.buffer_size:
            for message in self.buffer:
                self.logger.info(message)
            self.buffer.clear()



def get_pod_names(pods):
    return [pod.metadata.name for pod in pods.items]



def get_pod_metrics(pod_name):
    prometheus_url = "http://localhost:31085"
    query_cpu = f'sum(rate(container_cpu_usage_seconds_total{{pod="{pod_name}"}}[1m])) by (pod)'
    query_memory = f'sum(container_memory_working_set_bytes{{pod="{pod_name}"}}) by (pod)'

    try:
        response_cpu = requests.get(f"{prometheus_url}/api/v1/query", params={"query": query_cpu})
        response_memory = requests.get(f"{prometheus_url}/api/v1/query", params={"query": query_memory})
        if not response_cpu.json()["data"]["result"] or not response_memory.json()["data"]["result"]:
            raise Exception("Empty or unexpected response from Prometheus")
        cpu_usage = float(response_cpu.json()["data"]["result"][0]["value"][1])
        memory_usage = float(response_memory.json()["data"]["result"][0]["value"][1])
        return cpu_usage, memory_usage

    except Exception as e:
        #print(f"Error fetching metrics for pod {pod_name}: {e}")
        return 0, 0




def monitor_cluster_workload(namespace, application, logger, session_duration):
    print(f"Cluster_scan session for '{application}' started. (Duration: {session_duration}s)")
    session_start_time = time.time()
    log_interval = 0.01
    message_interval = 5
    last_message_time = time.time()
    known_pods = set()

    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        start_http_server(8000)

        while time.time() - session_start_time < session_duration:
            current_time = datetime.now().strftime("%Y%m%d-%H%M%S.%f")[:-3]
            if time.time() - last_message_time >= message_interval:
                print("Cluster_Collecting log")
                last_message_time = time.time()

            pods = v1.list_namespaced_pod(namespace, label_selector=f'app={application}')
            current_pods = get_pod_names(pods)
            current_pods_set = set(current_pods)

            new_pods = current_pods_set - known_pods
            for pod in new_pods:
                print(f"Cluster_New pod detected: {pod}")

            deleted_pods = known_pods - current_pods_set
            for pod in deleted_pods:
                print(f"Cluster_Pod deleted: {pod}")

            known_pods = current_pods_set
            
            for pod_name in current_pods:
                try:
                    cpu_usage, memory_usage = get_pod_metrics(pod_name)
                    node_name = v1.read_namespaced_pod(pod_name, namespace).spec.node_name
                    logger.log(current_time, pod_name, node_name, cpu_usage, memory_usage)
                except client.exceptions.ApiException as e:
                    if e.status == 404:
                        print(f"Cluster_Error: Pod {pod_name} not found or no longer exists.")
                    else:
                        print(f"Cluster_Unexpected error for pod {pod_name}: {e}")
            time.sleep(log_interval)

    except KeyboardInterrupt:
        print("Cluster_scan interrupted by user.")
    finally:
        print("Cluster_scan session ended.")       
        print(f"Cluster_scan logs have been created: {logger.output_directory}")





if __name__ == "__main__":
    output_directory = "./cluster/log"
    session_duration = 30
    logger = MonitorLogger(output_directory, buffer_size=10)
    namespace = "teastore"
    application = "teastore"
    monitor_cluster_workload(namespace, application, logger, session_duration)
