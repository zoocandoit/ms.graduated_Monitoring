import os
import glob
from neo4j import GraphDatabase
import json

class Neo4jConnection:
    def __init__(self, uri, user, pwd):
        self._driver = GraphDatabase.driver(uri, auth=(user, pwd))

    def close(self):
        self._driver.close()

    def run_query(self, query, parameters=None):
        with self._driver.session() as session:
            result = session.execute_write(self._execute_query, query, parameters)
            return result

    @staticmethod
    def _execute_query(tx, query, parameters):
        result = tx.run(query, parameters)
        return [record for record in result]


def extract_data(log_file_path):
    with open(log_file_path, 'r') as file:
        log_lines = file.readlines()

    for line in log_lines:
        log_part = line.strip().split('- INFO - ')[1]
        log_dict = json.loads(log_part)
        yield {
            "timestamp": log_dict['timestamp'],
            "pod_name": log_dict['pod_name'],
            "node_name": log_dict['node_name'],
            "cpu_usage": log_dict['cpu_usage'],
            "memory_usage": log_dict['memory_usage']
        }

def load_data_to_neo4j(conn, log_file_path):
    query = """
    MERGE (pod:Pod {name: $pod_name})
    MERGE (node:Node {name: $node_name})
    MERGE (pod)-[r:HOSTED_ON]->(node)
    SET r.timestamp = $timestamp, r.cpu_usage = $cpu_usage, r.memory_usage = $memory_usage
    """
    for data in extract_data(log_file_path):
        conn.run_query(query, parameters=data)


def find_latest_log_file(log_directory):
    list_of_files = glob.glob(os.path.join(log_directory, '*.log'))
    if not list_of_files:
        raise Exception("No log files found in the directory.")
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file


uri = "bolt://localhost:7687"
user = "neo4j"
password = "qwer1234"
log_directory = "./log"
log_file_path = find_latest_log_file(log_directory)


conn = Neo4jConnection(uri, user, password)
load_data_to_neo4j(conn, log_file_path)
conn.close()

