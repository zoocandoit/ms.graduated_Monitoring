import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from datetime import datetime
import json
from kubernetes import client, config
from prometheus_client import start_http_server
import time, requests
from tabulate import tabulate

class MonitorLogger:
    def __init__(self, log_directory, max_bytes=10485760, backup_count=5, buffer_size=10):
        self.buffer = []
        self.buffer_size = buffer_size
        start_time = datetime.now().strftime("%Y%m%d_%H%M%S.%f")[:-3]
        log_filename = f"cluster_{start_time}.log"
        os.makedirs(log_directory, exist_ok=True)
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
        print(f"Error fetching metrics for pod {pod_name}: {e}")
        return 0, 0

def monitor_application_workload(namespace, application, logger):
    print(f"Workload_scan '{application}' session start.")
    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        previous_pods = set(get_pod_names(v1.list_namespaced_pod(namespace, label_selector=f'app={application}')))
        start_http_server(8000)

        log_interval = 0.01
        message_interval = 5
        last_message_time = time.time()

        while True:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            if time.time() - last_message_time >= message_interval:
                print("Collecting Workload log")
                last_message_time = time.time()

            pods = v1.list_namespaced_pod(namespace, label_selector=f'app={application}')
            current_pods = get_pod_names(pods)
            for pod_name in current_pods:
                cpu_usage, memory_usage = get_pod_metrics(pod_name)
                node_name = v1.read_namespaced_pod(pod_name, namespace).spec.node_name
                logger.log(current_time, pod_name, node_name, cpu_usage, memory_usage)

            time.sleep(log_interval)

    except KeyboardInterrupt:
        print("Monitoring interrupted by user.")
    finally:
        print(f"Log files have been created in the directory: {logger.logger.handlers[0].baseFilename}")
        print("Workload_scan session ended.")

if __name__ == "__main__":
    logger = MonitorLogger("./log", buffer_size=7)
    monitor_application_workload("teastore", "teastore", logger)

