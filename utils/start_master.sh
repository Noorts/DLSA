#!/bin/bash

sbatch --time=00:15:00 --job-name=dlsa_m --nodes=1 ~/DLSA/utils/master.sh | awk '{print $4}' | xargs -I {} sh -c 'while [ ! -e "slurm-{}.out" ]; do sleep 1; done; cat "slurm-{}.out" | head --lines 1 | awk "{print \$2}" | awk -F "/" "{print \$1}"'

if [ $? -eq 0 ]; then
        echo "Master started!"
    else
        echo "Starting master failed."
fi
