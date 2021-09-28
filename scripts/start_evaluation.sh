#!/bin/bash

echo "Be careful with the cluster file system... the evaluation script stores and loads the head checkpoints"

MEMORY=40960
GPU=GeForceRTX2080Ti
FINGERPRINT=$1

for frac in 0.15 0.3 0.5 
do
for size in 10K 100K 1M 10M
do 
    bsub -o bert_eval_$frac$size.log -n 8 -W 02:00 -R "rusage[mem=$MEMORY, ngpus_excl_p=1]" -R "select[gpu_model0==$GPU]" python exp/evaluate/selfattn/moleculenet.py --overwrite '{"use_min" : true, "fingerprint" : "'$FINGERPRINT'"}' --wandb_project moleculenet10-size --model bert$frac-$size-euler 
done
done 

for frac in 0.15 0.3 0.5 
do
for size in 10M
do 
    bsub -o bert_eval_$frac$size.log -n 8 -W 02:00 -R "rusage[mem=$MEMORY, ngpus_excl_p=1]" -R "select[gpu_model0==$GPU]" python exp/evaluate/selfattn/moleculenet.py --overwrite '{"use_min" : true, "fingerprint" : "'$FINGERPRINT'"}' --wandb_project moleculenet10-size --model bert2$frac-$size-euler 
done
done 

for size in 10K 100K 1M 10M
do 
    bsub -o rnd2min_eval_$size.log -n 8 -W 02:00 -R "rusage[mem=$MEMORY, ngpus_excl_p=1]" -R "select[gpu_model0==$GPU]" python exp/evaluate/selfattn/moleculenet.py --overwrite '{"use_min" : false, "fingerprint" : "'$FINGERPRINT'"}' --wandb_project moleculenet10-size --model rnd2min-$size-euler 
done

for size in 10M
do 
    bsub -o rnd2min_eval_$size.log -n 8 -W 02:00 -R "rusage[mem=$MEMORY, ngpus_excl_p=1]" -R "select[gpu_model0==$GPU]" python exp/evaluate/selfattn/moleculenet.py --overwrite '{"use_min" : false, "fingerprint" : "'$FINGERPRINT'"}' --wandb_project moleculenet10-size --model rnd2min2-$size-euler 
done

