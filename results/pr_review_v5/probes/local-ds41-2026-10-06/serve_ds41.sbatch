#!/bin/bash
# Serve deepseek-ai/DeepSeek-V4.1-Flash with vLLM on `first`, bound to localhost (the harness runs on
# this host). Start it with a bare `sbatch serve_ds41.sbatch`: the patched nightly, its attention
# backend, DSpark and a 1M context are the defaults (2026-10-07); ~12 min to serving (8 to download,
# 4 to load). The weights are downloaded into /tmp (tmpfs) when the job starts, not before: the job
# waits in the queue for a busy node, and a 510 GB copy would hold that much of its RAM meanwhile.
# /tmp is tmpfs, so the copy is node RAM for as long as it sits there, and vLLM neither maps nor holds the
# shards once loaded: deleting them while job 432906 served (2026-10-07 08:13) gave the node back 476 GB
# with the server unaffected. Delete *.safetensors and .complete once serving; the next start downloads
# again (493 s). /research is NFS v3 on one TCP connection: 2026-10-08 single-stream direct reads ran
# 0.61-0.95 GB/s in 16 MB requests, 228 MB/s in 128 KB (the rsize) and 15 MB/s in 4 KB, so the old
# ~75 MB/s was small-request access (xet's chunk cache, mmap faults), not a cap. Even read well it is no
# faster than the download, which runs near the one 10 Gb/s link both share (1.25 GB/s); the node's local NVMe,
# /data/local, is root-only.
#SBATCH -p first
#SBATCH -A first
#SBATCH --gres=gpu:8
#SBATCH --mem=900G
#SBATCH --time=08:00:00
#SBATCH -J vllm-ds41
#SBATCH -o /research/projects/proofedit/ya475/localmodel/logs/serve_ds41_%j.log
set -euo pipefail
ROOT=/research/projects/proofedit/ya475/localmodel
# Which vLLM environment serves: VENV=<dir> sbatch serve_ds41.sbatch. The default, vllm-nightly-env
# (0.31.1rc1.dev29), carries the SM120 per-layer block patch (patch/ beside the probe README) and is the
# only one that serves V4.1 on first's GPUs; vllm-env (0.30.0) and vllm031-env (0.31.0) do not.
VENV=${VENV:-$ROOT/vllm-nightly-env}
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
# DeepGEMM is ON (vLLM's default) since job 432885: off, the dense FP8 layers fell to FlashInfer's
# mxfp8_gemm, which autotuned for 50+ minutes without finishing, and MoE fell to Marlin. Its JIT
# now has what it needs (CUDA 13.0 toolkit, gcc 13), as in the validated vllm#59203 stack.
export VLLM_USE_FLASHINFER_SAMPLER=0
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
# The shards are node RAM (tmpfs) and unused once loaded, so they go as soon as the server answers;
# KEEP_WEIGHTS=1 keeps them for a quick restart (4 min against ~12).
if [ "${KEEP_WEIGHTS:-0}" != 1 ]; then
  ( until curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null 2>&1; do sleep 30; done
    rm -f "$DEST/.complete" "$DEST"/*.safetensors
    echo "serving; weight shards deleted from $DEST at $(date -Is)" ) &
fi
# 262144 until 2026-10-07. With each turn's thinking kept in the prompt (5fd560ab), a high-effort
# session adds ~8k tokens a turn and would pass it near turn 25-30; the model takes 1,048,576.
MAX_LEN=${MAX_LEN:-1048576}
# Speculative decoding with the checkpoint's own DSpark draft, on by default since 2026-10-07: 55.6
# tokens/s per session against ~36 at 15 sessions, a rep in 34.5 min against 45-53, the same reviews
# (results/pr_review_v5/probes/local-ds41-2026-10-06/README.md). vLLM refuses it without
# num_speculative_tokens. SPEC=0 serves without it.
SPEC_ARGS=()
if [ "${SPEC:-1}" = 1 ]; then
  SPEC_ARGS=(--speculative-config '{"method":"dspark","num_speculative_tokens":5}')
fi
echo "serving from $DEST with $($VENV/bin/vllm --version 2>/dev/null) ($VENV) at $(date -Is); max len $MAX_LEN; spec ${SPEC:-1}; extra: $*"
exec $VENV/bin/vllm serve "$DEST" --host 127.0.0.1 --port "$PORT" \
  --served-model-name local-deepseek deepseek-ai/DeepSeek-V4.1-Flash --tensor-parallel-size 8 \
  --tool-call-parser deepseek_v41 --reasoning-parser deepseek_v41 --enable-auto-tool-choice \
  --language-model-only --enable-prefix-caching --enable-prompt-tokens-details \
  --max-model-len "$MAX_LEN" "${SPEC_ARGS[@]}" \
  --kv-cache-dtype fp8 --attention-config '{"backend":"FLASHINFER_MLA_SPARSE_DSV41","indexer_kv_dtype":"fp8"}' \
  --no-enable-flashinfer-autotune "$@"
