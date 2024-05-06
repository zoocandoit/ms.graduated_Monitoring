from kubernetes import client, config
from prometheus_client import start_http_server, Gauge
import time, requests

def print_separator():
    print("=" * 50)

def get_pod_names(pods):
    return [pod.metadata.name for pod in pods.items]

def get_pod_metrics(pod_name):
    prometheus_url = "http://localhost:31085"
    query_cpu = f'sum(rate(container_cpu_usage_seconds_total{{pod="{pod_name}"}}[1m])) by (pod)'
    query_memory = f'sum(container_memory_working_set_bytes{{pod="{pod_name}"}}) by (pod)'
    response_cpu = requests.get(f"{prometheus_url}/api/v1/query", params={"query": query_cpu})
    response_memory = requests.get(f"{prometheus_url}/api/v1/query", params={"query": query_memory})

    cpu_usage = float(response_cpu.json()["data"]["result"][0]["value"][1])
    memory_usage = float(response_memory.json()["data"]["result"][0]["value"][1])

    return cpu_usage, memory_usage

def format_cpu_usage(cpu_usage):
    return f"{cpu_usage:.2f} mCore"

def format_memory_usage(memory_usage):
    return f"{memory_usage / (1024 * 1024):.2f} MB"

def monitor_application_workload(namespace, application):
    config.load_kube_config()
    v1 = client.CoreV1Api()
    previous_pods = []

    start_http_server(8000)

    while True:
        print_separator()
        print(f"Monitoring {application} workload")
        print_separator()

        pods = v1.list_namespaced_pod(namespace, label_selector=f'app={application}')
        current_pods = get_pod_names(pods)

        for pod_name in current_pods:
            if pod_name not in previous_pods:
                print(f"New Pod Detected: {pod_name}")

        for pod_name in previous_pods:
            if pod_name not in current_pods:
                print(f"Pod Terminated: {pod_name}")

        for pod_name in current_pods:
            cpu_usage, memory_usage = get_pod_metrics(pod_name)
            formatted_cpu_usage = format_cpu_usage(cpu_usage)
            formatted_memory_usage = format_memory_usage(memory_usage)
            print(f"Pod: {pod_name}, CPU Usage: {formatted_cpu_usage}, Memory Usage: {formatted_memory_usage}")

        previous_pods = current_pods
        time.sleep(10)

if __name__ == "__main__":
    monitor_application_workload("teastore", "teastore")

