#!/bin/bash

echo "🔥  delete All log in scanning system"

rm -rf ./application/log
rm -rf ./application/pcap
rm -rf ./cluster/log


wait

echo "🔥  delete All log completed."


