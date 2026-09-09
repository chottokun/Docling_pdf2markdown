# GPU Testing and Acceleration Guide

Language: [English](GPU_TESTING.md) | [日本語](../GPU_TESTING.md)

This document provides technical details on GPU (CUDA) acceleration specifications, performance optimization, VRAM management, automatic fallback mechanisms, and test execution procedures.

---

## 🏎 1. GPU Acceleration Design and Specifications

The Docling document conversion pipeline (PyTorch, RapidOCR, Layout Model, CodeFormula VLM) is engineered to leverage NVIDIA GPU acceleration when available.

### 1.1 CUDA Compatibility Verification and Automatic Fallback (`is_cuda_compatible`)

Upon initialization, the `is_cuda_compatible()` function in `src/docling_lib/converter.py` evaluates the runtime GPU environment:

1. **Environment Variable Check**: If `DOCLING_USE_GPU=False`, the converter immediately executes in CPU mode.
2. **CUDA Availability Check**: Evaluates `torch.cuda.is_available()`.
3. **Compute Capability (CC) Validation**:
   - Modern PyTorch builds require **Compute Capability (CC) >= 7.5** (Turing architecture or newer: RTX 20 series, GTX 1660, Tesla T4, A100, H100, etc.).
   - If an older GPU with CC < 7.5 is detected (e.g., GTX 1060 / `sm_61`), the system logs a warning and **automatically falls back to CPU mode** to prevent kernel crashes or freezes.
4. **Tensor Execution Probe**: Runs a lightweight tensor operation and synchronization test on the CUDA device. GPU mode (`AcceleratorDevice.AUTO`) is selected only upon successful execution.

---

## ⚡ 2. Optimization Settings for GPU Environments

Tune GPU performance using environment variables:

```bash
# Enable GPU acceleration (default: True)
DOCLING_USE_GPU=True

# Enable FlashAttention-2 (for supported GPUs)
DOCLING_CUDA_FLASH_ATTENTION=True

# Max worker processes (adjust according to available VRAM)
DOCLING_MAX_WORKERS=2
```

### 2.1 VRAM Management in Multi-Process Architecture

Because conversions run in separate worker processes via `ProcessPoolExecutor`, each worker initializes its own PyTorch/CUDA context:

- **VRAM Consumption**: Each worker process consumes **~2 GB to 4 GB** of VRAM.
- **Worker Recommendation**: For GPUs with 8 GB VRAM, `DOCLING_MAX_WORKERS=2` is recommended.
- **OOM Protection**: Dynamic memory-aware semaphores (`get_dynamic_semaphore_limit()`) monitor available system memory to regulate concurrent requests safely.

---

## 🧪 3. GPU Test Execution Procedures

### 3.1 Unit and Integration Testing (GPU Enabled)

Run the full test suite with GPU enabled:

```bash
# Execute test suite with GPU enabled
DOCLING_USE_GPU=True uv run pytest
```

### 3.2 Device Verification Testing

Run targeted device verification and fallback tests:

```bash
uv run pytest tests/test_performance_refactorings.py -k test_is_cuda_compatible -v
```

### 3.3 High-Load Concurrency Stress Test

Validate GPU/CPU concurrency and semaphore throttles under parallel load:

```bash
uv run python -c "
import asyncio, time
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from docling_lib.server import create_app

async def main():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test', timeout=180.0) as client:
        test_pdf = Path('tests/test_data/sample1_simple.pdf')
        if not test_pdf.exists():
            print('Sample file not found, skipping benchmark script')
            return
        tasks = [
            client.post('/convert/', files={'file': (f'test_{i}.pdf', open(test_pdf, 'rb'), 'application/pdf')})
            for i in range(4)
        ]
        results = await asyncio.gather(*tasks)
        print([r.status_code for r in results])

asyncio.run(main())
"
```

---

## 🔍 4. Troubleshooting

- **Warning: `NVIDIA GeForce GTX 1060 ... is not compatible`**:
  - The installed PyTorch build does not support the GPU architecture. The engine automatically falls back to CPU mode without failing conversions.
- **CUDA Out of Memory (OOM)**:
  - Lower `DOCLING_MAX_WORKERS` (e.g., `DOCLING_MAX_WORKERS=1`) or force CPU mode with `DOCLING_USE_GPU=False`.
