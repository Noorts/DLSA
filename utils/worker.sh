#!/bin/bash

# Enable/disable system utilization metrics (CPU and memory) collection.
enable_sys_metric_collection=true

worker_ip=$(ip a show dev ib0 | grep "inet " | awk '{print $2}' | awk -F "/" "{print \$1}")
echo $worker_ip

if [ "$enable_sys_metric_collection" = true ]; then
    output_filename="slurm-${SLURM_JOB_ID}-sys.out"

    # Store job metadata.
    echo "Job id: ${SLURM_JOB_ID}" > $output_filename
    echo "Worker ip: $worker_ip" >> $output_filename
    echo "Master ip: $1" >> $output_filename
    echo "--" >> $output_filename

    # Collect system utilization metrics (CPU and memory).
    top -b -d 5 | grep --line-buffered "top - " -A 4 >> $output_filename &
fi

go run cmd/worker/main.go "$1:8000"
