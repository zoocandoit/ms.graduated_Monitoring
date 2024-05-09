#!/bin/bash

echo "🔥  Start scanning system"

python3 ./cluster/cluster_scan.py &
echo $! > cluster_scan_pid.txt

python3 ./application/application_scan.py &
echo $! > application_scan_pid.txt



#wait

echo "🔥  Scanning has completed."

rm -rf cluster_scan_pid.txt application_scan_pid.txt

