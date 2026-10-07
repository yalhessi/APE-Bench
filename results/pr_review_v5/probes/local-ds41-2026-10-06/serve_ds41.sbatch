#!/bin/bash
# Serve deepseek-ai/DeepSeek-V4.1-Flash with vLLM on `first`, bound to localhost (the harness runs on
# this host). The weights are downloaded into /tmp (tmpfs) when the job starts, not before: the job
# waits in the queue for a busy node, and a 510 GB copy would hold that much of its RAM meanwhile.
#SBATCH -p first
#SBATCH -A first
#SBATCH --gres=gpu:8
#SBATCH --mem=1000G
#SBATCH --time=08:00:00
#SBATCH -J vllm-ds41
#SBATCH -o /research/projects/proofedit/ya475/localmodel/logs/serve_ds41_%j.log
set -euo pipefail
ROOT=/research/projects/proofedit/ya475/localmodel
# Which vLLM environment serves: VENV=<dir> sbatch serve_ds41.sbatch. vllm-env is 0.30.0;
# vllm031-env is 0.31.0 (DeepGEMM SM120 fixes), tried after 0.30 failed on job 432871.
VENV=${VENV:-$ROOT/vllm-env}
DEST=/tmp/ya475-models/DeepSeek-V4.1-Flash
PORT=${PORT:-8012}
echo "host $(hostname) gpus $CUDA_VISIBLE_DEVICES start $(date -Is)"

if [ ! -f "$DEST/.complete" ]; then
  # HF_HOME on NFS throttles even a download to tmpfs to the NFS read rate (xet's chunk cache);
  # in /tmp with the chunk cache off it ran at up to 1.25 GB/s for the Qwen weights.
  mkdir -p /tmp/ya475-models/hf-home
  t=$(date +%s)
  HF_HOME=/tmp/ya475-models/hf-home HF_XET_CHUNK_CACHE_SIZE_BYTES=0 \
    /research/projects/proofedit/ya475/APE-Bench/ape/bin/hf download deepseek-ai/DeepSeek-V4.1-Flash \
    --local-dir "$DEST"
  touch "$DEST/.complete"
  echo "download took $(( $(date +%s) - t ))s; $(du -sh "$DEST" | cut -f1)"
fi

export HF_HUB_OFFLINE=1
export VLLM_CACHE_ROOT=$ROOT/cache/vllm XDG_CACHE_HOME=$ROOT/cache/xdg
export TRITON_CACHE_DIR=$ROOT/cache/triton TORCHINDUCTOR_CACHE_DIR=$ROOT/cache/inductor
mkdir -p $VLLM_CACHE_ROOT $XDG_CACHE_HOME $TRITON_CACHE_DIR $TORCHINDUCTOR_CACHE_DIR
# As for Qwen (serve.sbatch): DeepGEMM's SM120 JIT needs a coherent CUDA >= 13 toolkit this node
# lacks, and FlashInfer's sampler JIT-builds on first use.
export VLLM_USE_DEEP_GEMM=0 VLLM_MOE_USE_DEEP_GEMM=0 VLLM_USE_FLASHINFER_SAMPLER=0
# FlashInfer 0.7.1rc4 against the nightly's 0.7.0.post1 pin (the per-layer fix was validated on FlashInfer
# main; vllm#59203 used this switch for the same mismatch).
export FLASHINFER_DISABLE_VERSION_CHECK=1
# DeepSeek V4.1's sparse attention on SM120 has only a FlashInfer backend, and vLLM counts FlashInfer
# as present only with prebuilt cubins or an nvcc on PATH. Job 432149 had neither and died with
# "requires a FlashInfer DSV4 sparse MLA decode specialization for (num_q_heads=8, top_k=128)" -- a
# shape the installed FlashInfer does ship. Fixed by installing flashinfer-cubin and
# flashinfer-jit-cache 0.6.18.post1 (cu130) into the venv; the node's own coherent CUDA 13.0 toolkit
# is on PATH as well, for anything still compiled at startup.
export CUDA_HOME=/usr/local/cuda-13.0
export PATH=$VENV/bin:$CUDA_HOME/bin:$PATH
echo "serving from $DEST with $($VENV/bin/vllm --version 2>/dev/null) ($VENV) at $(date -Is); extra: $*"
exec $VENV/bin/vllm serve "$DEST" --host 127.0.0.1 --port "$PORT" \
  --served-model-name local-deepseek deepseek-ai/DeepSeek-V4.1-Flash --tensor-parallel-size 8 \
  --tool-call-parser deepseek_v41 --reasoning-parser deepseek_v41 --enable-auto-tool-choice \
  --language-model-only --enable-prefix-caching --enable-prompt-tokens-details \
  --max-model-len 262144 "$@"
