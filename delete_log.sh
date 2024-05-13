#!/bin/bash

echo "🔥  delete All log in scanning system"

rm -rf ./application/app_log
rm -rf ./application/pcap
rm -rf ./cluster/precl_log
rm -rf ./cluster/cl_log
rm -rf ./pod/pod_communication_counts.csv


wait

echo "🔥  delete All log completed."


