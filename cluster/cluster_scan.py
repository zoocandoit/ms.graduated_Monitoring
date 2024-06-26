import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
import json
from kubernetes import client, config
from prometheus_client import start_http_server
import time
import requests

class MonitorLogger:
    def __init__(self, log_directory, max_bytes=10485760, backup_count=5, buffer_size=10):
        self.buffer = {}
        self.buffer_size = buffer_size
        os.makedirs(log_directory, exist_ok=True)
        self.loggers = {}
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.log_directory = log_directory

    def get_logger(self, pod_name):
        if pod_name not in self.loggers:
            log_filename = f"cl_{pod_name}.log"
            logger = logging.getLogger(f"MonitorLogger_{pod_name}")
            logger.setLevel(logging.INFO)
            handler = RotatingFileHandler(
                filename=os.path.join(self.log_directory, log_filename),
                maxBytes=self.max_bytes,
                backupCount=self.backup_count
            )
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            self.loggers[pod_name] = logger
            self.buffer[pod_name] = []
        return self.loggers[pod_name]

    def log(self, timestamp, pod_name, node_name, memory_usage):
        log_data = {
            "timestamp": timestamp,
            "pod_name": pod_name,
            "node_name": node_name,
            "memory_usage": memory_usage
        }
        log_message = json.dumps(log_data)
        
        if pod_name not in self.buffer:
            self.buffer[pod_name] = []
        buffer = self.buffer[pod_name]
        buffer.append(log_message)
        
        if len(buffer) >= self.buffer_size:
            logger = self.get_logger(pod_name)
            for message in buffer:
                logger.info(message)
            buffer.clear()

    def flush_all(self):
        for pod_name in self.buffer:
            buffer = self.buffer[pod_name]
            if buffer:
                logger = self.get_logger(pod_name)
                for message in buffer:
                    logger.info(message)
                buffer.clear()

    def close_all(self):
        for logger in self.loggers.values():
            handlers = logger.handlers[:]
            for handler in handlers:
                handler.close()
                logger.removeHandler(handler)

def get_pod_names(pods):
    return [pod.metadata.name for pod in pods.items]

def get_pod_metrics(pod_name):
    prometheus_url = "http://localhost:32758"
    query_memory = f'sum(container_memory_working_set_bytes{{pod="{pod_name}"}}) by (pod)'

    try:
        response_memory = requests.get(f"{prometheus_url}/api/v1/query", params={"query": query_memory})
        response_memory.raise_for_status()


        result = response_memory.json()["data"]["result"]
        if not result:
            raise Exception("Empty or unexpected response from Prometheus for memory usage")

        memory_usage = float(result[0]["value"][1])
        return memory_usage

    except Exception as e:
        print(f"Error fetching metrics for pod {pod_name}: {e}")
        return 0

def monitor_cluster_workload(namespace, application, logger, session_duration):
    print(f"Cluster_scan session for '{application}' started. (Duration: {session_duration}s)")
    session_start_time = time.time()
    log_interval = 1
    message_interval = 5
    last_message_time = time.time()
    known_pods = set()

    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        start_http_server(8000)

        while time.time() - session_start_time < session_duration:
            current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")
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
                    memory_usage = get_pod_metrics(pod_name)
                    node_name = v1.read_namespaced_pod(pod_name, namespace).spec.node_name
                    logger.log(current_time, pod_name, node_name, memory_usage)
                except client.exceptions.ApiException as e:
                    if e.status == 404:
                        print(f"Cluster_Error: Pod {pod_name} not found or no longer exists.")
                    else:
                        print(f"Cluster_Unexpected error for pod {pod_name}: {e}")
            time.sleep(log_interval)

    except KeyboardInterrupt:
        print("Cluster_scan interrupted by user.")
    finally:
        logger.flush_all()
        print("Cluster_scan session ended.")
        print(f"Cluster_scan logs have been created: {logger.log_directory}")

if __name__ == "__main__":
    output_directory = "./cluster/cl_log"
    session_duration = 120
    logger = MonitorLogger(output_directory, buffer_size=10)
    namespace = "teastore"
    application = "teastore"
    monitor_cluster_workload(namespace, application, logger, session_duration)

