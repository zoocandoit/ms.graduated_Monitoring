import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
import json

class MonitorLogger:
    def __init__(self, log_directory, max_bytes=10485760, backup_count=5):
        start_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_filename = f"monitoring_{start_time}.log"
        
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
        self.logger.info(log_message)
