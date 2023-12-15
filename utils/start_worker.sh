#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <number_of_workers> <ip_address (0.0.0.0)>"
    exit 1
fi

if [ "$1" -eq 1 ]; then
    echo "Starting $1 worker."
else
    echo "Starting $1 workers."
fi

for ((i = 1; i <= "$1"; i++)); do
    sbatch --time=00:15:00 --job-name="dlsa_w_$i" --nodes=1 ~/DLSA/utils/worker.sh $2
done
