"""Per-layer KV block sizes for DeepSeek-V4.1-Flash on SM120 (RTX PRO 6000), applied to an installed vLLM.

Reconstructed from the description in vllm-project/vllm#59203 (xzwgit, 2026-10-07; not yet a PR):
DeepGEMM's arch-12 FP8 paged-MQA logits need exactly 64 states per block, and the indexer sees
`block_size // compress_ratio` states, so no single global block size serves both the cr=1 and the
cr=2 layers. The fix gives each layer `64 * max(1, compress_ratio)` tokens per block (64 states
everywhere) and lets the SM120 backends accept both 64- and 128-token kernel blocks. Every edit is
guarded by `is_device_capability_family(120)`, so other GPUs are unchanged.

Usage: python dsv41_sm120_per_layer_blocks.py <site-packages>/vllm [--check]
Each anchor must match exactly once, or nothing is written.
"""

import sys
from pathlib import Path

SM120 = "current_platform.is_device_capability_family(120)"

EDITS = [
    # 1. The V4.1 indexer backend (indexer.py).
    ("v1/attention/backends/mla/indexer.py",
     '''        return "DEEPSEEK_V41_INDEXER"

    @staticmethod
    def get_supported_kernel_block_sizes(kv_cache_spec=None) -> list[int | MultipleOf]:
        return [64 if current_platform.is_device_capability_family(90) else 128]''',
     '''        return "DEEPSEEK_V41_INDEXER"

    @staticmethod
    def get_supported_kernel_block_sizes(kv_cache_spec=None) -> list[int | MultipleOf]:
        if current_platform.is_device_capability_family(120):
            return [64, 128]  # SM120 per-layer blocks (vllm#59203)
        return [64 if current_platform.is_device_capability_family(90) else 128]'''),
    # 2. The V4.1 sparse MLA backend base (sparse_mla.py).
    ("models/deepseek_v41/sparse_mla.py",
     '''    def get_supported_kernel_block_sizes(kv_cache_spec=None) -> list[int | MultipleOf]:
        return [64 if current_platform.is_device_capability_family(90) else 128]''',
     '''    def get_supported_kernel_block_sizes(kv_cache_spec=None) -> list[int | MultipleOf]:
        if current_platform.is_device_capability_family(120):
            return [64, 128]  # SM120 per-layer blocks (vllm#59203)
        return [64 if current_platform.is_device_capability_family(90) else 128]'''),
    # 3. FLASHINFER_MLA_SPARSE_DSV41 (flashinfer_sparse.py), the only V4.1 attention backend on SM120.
    ("models/deepseek_v41/nvidia/flashinfer_sparse.py",
     '''    def get_supported_kernel_block_sizes(kv_cache_spec=None) -> list[int | MultipleOf]:
        return [128]

    @staticmethod
    def get_name() -> str:''',
     '''    def get_supported_kernel_block_sizes(kv_cache_spec=None) -> list[int | MultipleOf]:
        from vllm.platforms import current_platform

        if current_platform.is_device_capability_family(120):
            return [64, 128]  # SM120 per-layer blocks (vllm#59203)
        return [128]

    @staticmethod
    def get_name() -> str:'''),
    # 4. The compressed-KV (MLA) spec (attention.py).
    ("models/deepseek_v41/attention.py",
     '''        return MLAAttentionSpec(
            block_size=vllm_config.cache_config.block_size,
            num_kv_heads=1,
            head_size=self.head_dim,
            dtype=torch.uint8 if uses_fp8_ds_mla_layout else self.kv_cache_torch_dtype,''',
     '''        return MLAAttentionSpec(
            block_size=(64 * max(1, self.compress_ratio) if current_platform.is_device_capability_family(120)
                        else vllm_config.cache_config.block_size),  # SM120 per-layer blocks (vllm#59203)
            num_kv_heads=1,
            head_size=self.head_dim,
            dtype=torch.uint8 if uses_fp8_ds_mla_layout else self.kv_cache_torch_dtype,'''),
    # 5. The indexer cache spec (attention.py).
    ("models/deepseek_v41/attention.py",
     '''        return MLAAttentionSpec(
            block_size=self.cache_config.block_size,
            num_kv_heads=1,
            head_size=self.head_dim,
            dtype=self.dtype,
            tokens_per_state=self.compress_ratio,''',
     '''        return MLAAttentionSpec(
            block_size=(64 * max(1, self.compress_ratio) if current_platform.is_device_capability_family(120)
                        else self.cache_config.block_size),  # SM120 per-layer blocks (vllm#59203)
            num_kv_heads=1,
            head_size=self.head_dim,
            dtype=self.dtype,
            tokens_per_state=self.compress_ratio,'''),
    # 6. The sliding-window cache (attention.py): the author lists "MLA/indexer/SWA specs".
    ("models/deepseek_v41/attention.py",
     '''            backend_cls=self.swa_backend_cls,
            block_size=32,''',
     '''            backend_cls=self.swa_backend_cls,
            block_size=(64 * max(1, self.compress_ratio) if current_platform.is_device_capability_family(120)
                        else 32),  # SM120 per-layer blocks (vllm#59203)'''),
]


def main() -> int:
    root = Path(sys.argv[1])
    check_only = "--check" in sys.argv[2:]
    texts = {}
    for rel, old, new in EDITS:
        path = root / rel
        text = texts.get(rel) or path.read_text()
        count = text.count(old)
        if count != 1:
            print(f"REFUSED: {rel}: anchor matched {count} times:\n{old[:200]}")
            return 1
        texts[rel] = text.replace(old, new, 1)
    for rel, text in texts.items():
        if "current_platform" not in text.split("class ", 1)[0] and "import current_platform" not in text \
                and "from vllm.platforms import current_platform" not in text:
            print(f"REFUSED: {rel} does not import current_platform")
            return 1
    if check_only:
        print(f"ok: {len(EDITS)} edits apply to {len(texts)} files (not written)")
        return 0
    for rel, text in texts.items():
        (root / rel).write_text(text)
    print(f"applied: {len(EDITS)} edits to {len(texts)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
