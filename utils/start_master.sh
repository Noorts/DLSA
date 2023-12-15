#!/bin/bash

sbatch_output=$(sbatch --time=00:15:00 --job-name=dlsa_m --nodes=1 ~/DLSA/utils/master.sh)
if [ $? -eq 0 ]; then
        echo "Master started!"
    else
        echo "Starting master failed."
fi
echo $sbatch_output | awk '{print $4}' | xargs -I {} sh -c 'while [ ! -e "slurm-{}.out" ]; do sleep 1; done; cat "slurm-{}.out" | head --lines 1'
echo $sbatch_output | grep "Submitted batch job"
