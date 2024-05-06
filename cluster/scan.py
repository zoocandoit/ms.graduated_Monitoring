from kubernetes import client, config
from prometheus_client import start_http_server, Gauge
import time, requests
from tabulate import tabulate
from datetime import datetime

def print_separator():
    print("=" * 50)



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



def format_cpu_usage(cpu_usage):
    return f"{cpu_usage:.2f} mCore"



def format_memory_usage(memory_usage):
    return f"{memory_usage / (1024 * 1024):.2f} MB"



def monitor_application_workload(namespace, application):
    config.load_kube_config()
    v1 = client.CoreV1Api()
    previous_pods = set(get_pod_names(v1.list_namespaced_pod(namespace, label_selector=f'app={application}')))
    start_http_server(8000)

    while True:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print_separator()
        print(f"Monitoring {application} workload ({current_time})")
        print_separator()

        pods = v1.list_namespaced_pod(namespace, label_selector=f'app={application}')
        current_pods = get_pod_names(pods)

        # Detect new pods after the first iteration
        if previous_pods:
            new_pods = set(current_pods) - previous_pods
            for pod_name in new_pods:
                print(f"New Pod Detected: {pod_name}")
                # Wait for Prometheus to collect metrics for new pods
                time.sleep(30)

        # Detect terminated pods
        terminated_pods = previous_pods - set(current_pods)
        for pod_name in terminated_pods:
            print(f"Pod Terminated: {pod_name}")

        table = []
        for pod_name in current_pods:
            cpu_usage, memory_usage = get_pod_metrics(pod_name)
            formatted_cpu_usage = format_cpu_usage(cpu_usage)
            formatted_memory_usage = format_memory_usage(memory_usage)

            node_name = v1.read_namespaced_pod(pod_name, namespace).spec.node_name

            table.append([pod_name, node_name, formatted_cpu_usage, formatted_memory_usage])

        headers = ["Pod", "Node", "CPU Usage", "Memory Usage"]
        print(tabulate(table, headers=headers, tablefmt="grid"))

        # Regular monitoring interval
        time.sleep(5)

        # Update previous pods
        previous_pods = set(current_pods)




if __name__ == "__main__":
    monitor_application_workload("teastore", "teastore")

