#!/bin/bash

echo "🔥  delete All log in scanning system"

rm -rf ./application/app_log
rm -rf ./application/pcap
rm -rf ./application/preapp_log
rm -rf ./cluster/cl_log


wait

echo "🔥  delete All log completed."


