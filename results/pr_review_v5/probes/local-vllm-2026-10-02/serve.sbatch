#!/bin/bash
# Serve one model with vLLM on the `first` node, bound to localhost (the harness runs on this host).
# usage: sbatch --gres=gpu:<n> serve.sbatch <hf model id> <port> <tp size> [extra vllm args...]
#SBATCH -p first
#SBATCH --mem=400G
#SBATCH --time=03:00:00
#SBATCH -J vllm-serve
#SBATCH -o /research/projects/proofedit/ya475/localmodel/logs/serve_%j.log
set -euo pipefail
MODEL=$1; PORT=$2; TP=$3; shift 3
ROOT=/research/projects/proofedit/ya475/localmodel
# Home is at quota: every cache vLLM, torch and triton write goes under /research.
export HF_HOME=/research/projects/proofedit/ya475/hf-cache HF_HUB_OFFLINE=1
export VLLM_CACHE_ROOT=$ROOT/cache/vllm XDG_CACHE_HOME=$ROOT/cache/xdg
export TRITON_CACHE_DIR=$ROOT/cache/triton TORCHINDUCTOR_CACHE_DIR=$ROOT/cache/inductor
mkdir -p $VLLM_CACHE_ROOT $XDG_CACHE_HOME $TRITON_CACHE_DIR $TORCHINDUCTOR_CACHE_DIR
# DeepGEMM off, both switches. Its SM120 kernels JIT-compile only under CUDA >= 13.0: the system
# toolkit is 12.9 (job 417881 died on it) and pip's cu13 pieces are mismatched (nvcc 13.4, cccl 13.3;
# job 417886 died on that). vLLM itself auto-disables it for qwen3_5_moe on Blackwell ("E8M0 scale
# format causes accuracy degradation") but only for the dense layers; the MoE path has its own switch.
export VLLM_USE_DEEP_GEMM=0 VLLM_MOE_USE_DEEP_GEMM=0
# FlashInfer's sampler JIT-builds on first use, with ninja and nvcc, against cu13 torch (job 417939
# died on a missing ninja). PyTorch-native sampling avoids the JIT; venv bin on PATH for anything else.
export VLLM_USE_FLASHINFER_SAMPLER=0 PATH=$ROOT/vllm-env/bin:$PATH
echo "host $(hostname) gpus $CUDA_VISIBLE_DEVICES model $MODEL port $PORT tp $TP extra: $*"
exec $ROOT/vllm-env/bin/vllm serve "$MODEL" --host 127.0.0.1 --port "$PORT" \
  --served-model-name local-qwen "$MODEL" --tensor-parallel-size "$TP" \
  --reasoning-parser qwen3 --enable-auto-tool-choice --tool-call-parser qwen3_coder \
  --language-model-only --enable-prefix-caching --enable-prompt-tokens-details \
  "$@"
