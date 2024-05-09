#!/bin/bash

echo "🔥  Stopping the scanning processes..."

if [ -f cluster_scan_pid.txt ]; then
    kill $(cat cluster_scan_pid.txt)
    echo "Cluster scan process stopped."
    rm cluster_scan_pid.txt
else
    echo "Cluster scan PID file not found."
fi


if [ -f application_scan_pid.txt ]; then
    kill $(cat application_scan_pid.txt)
    echo "Application scan process stopped."
    rm application_scan_pid.txt
else
    echo "Application scan PID file not found."
fi

echo "🔥  All processes have been stopped."

