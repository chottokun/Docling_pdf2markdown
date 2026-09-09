# Unique Features (Technical Deep Dive)

Language: [English](FEATURES.md) | [日本語](../FEATURES.md)

This project implements key technical extensions on top of standard `docling` to deliver enterprise-grade performance, safety, and reliability.

---

## 1. Robust Security Layer

### Path Traversal Sandboxing
Path verification utilizes OS-level canonical path resolution rather than simple string matching.
- **Logic**: `Path(output_dir).resolve().is_relative_to(Path.cwd().resolve())`
- **Effect**: Even if an attacker passes relative paths such as `../../etc/passwd`, access outside the current working directory is strictly rejected.
- **Worker Isolation**: Temporary directories inside child worker processes are restricted within `output_dir`, maintaining strict sandbox protection.

### Injection Protection
- **Log Injection**: The `sanitize_log_message` utility is applied across all logging sites to replace `\n` and `\r` characters from user-controlled input with spaces.
- **YAML Frontmatter Injection**: Frontmatter metadata formatting sanitizes document names to prevent malicious YAML structural modification.

### API Security
- **Authentication**: When `DOCLING_API_KEY` is configured, mandatory `X-API-Key` verification is enforced across endpoints.
- **Rate Limiting**: An IP-based rate limiter using FastAPI dependency injection (`RATE_LIMIT_REQUESTS` / `RATE_LIMIT_WINDOW`) periodically cleans memory every 10 minutes to prevent leaks.

---

## 2. Performance and Scalability

### Multi-Process Parallel Execution (`ProcessPoolExecutor`)
Docling conversion tasks involve PyTorch and C++ extensions whose performance can be bottlenecked by Python's Global Interpreter Lock (GIL) when using threading.
- **Solution**: Conversions run in isolated processes via `ProcessPoolExecutor(mp_context='spawn')`.
- **Effect**: Eliminates event-loop blocking caused by CPU-heavy tasks, maintaining server responsiveness during concurrent document conversions.

### Dynamic Memory-Aware Semaphore (`get_dynamic_semaphore_limit`)
- **Problem**: Bursts of concurrent requests could trigger Out-of-Memory (OOM) killer terminations due to per-process model memory usage (1.5GB–4GB).
- **Dynamic Throttle**: Utilizes `psutil.virtual_memory()` to compute safe concurrency limits based on available RAM, controlling worker task entry with an `asyncio.Semaphore`.
- **Event Loop Tracking**: Binds dynamically to the active event loop to prevent loop incompatibility errors in multi-threaded test environments.

### Model Instance LRU Caching (`ThreadSafeModelPool`)
Instantiating `docling.DocumentConverter` repeatedly incurs heavy model loading overhead.
- **Solution**: Uses a thread-safe `ThreadSafeModelPool` (LRU cache).
- **Intelligent Cache Invalidation**: Generates new converter instances only when heavy options (e.g. `image_scale`, `do_ocr`, `do_formula`) change.

### Memory Optimization
- **Streaming I/O & Non-blocking File Writes (`aiofiles`)**: Streams file uploads in 1MB chunks to temporary disk files without loading entire payloads into RAM.
- **VLM Prefetching**: Prefetches VLM image captions asynchronously in parallel background threads.

### Dynamic GPU Compatibility Probe & Safe Fallback
- **Context**: Even if `torch.cuda.is_available()` returns `True`, mismatched GPU architectures (Compute Capability < 7.5) can cause asynchronous CUDA kernel crashes when loading models.
- **Dynamic Probe**: `is_cuda_compatible()` verifies Compute Capability >= 7.5 and executes a lightweight tensor operation probe on the GPU. If mismatched, it automatically falls back to `AcceleratorDevice.CPU`. See [GPU_TESTING.md](GPU_TESTING.md) for details.

---

## 3. Advanced Parsing Pipeline (v2.x Compatible)

- **Formula Extraction (LaTeX)**: Leverages `PdfPipelineOptions.do_formula_enrichment` to convert formulas into LaTeX code blocks.
- **Flexible Image Link Formatting (`EnhancedDoclingConverter`)**: Outputs CommonMark image links (`![image](path)`) by default while supporting Obsidian tags (`![[...]]`) and direct image saving to `assets_dir`.
- **Structured Tables**: Preserves merged table cells via HTML `<table>` elements with `colspan` and `rowspan` using `HTMLTableMarkdownSerializer`.
- **OCR & Layout Analysis**: Supports `RapidOCR` and environment-specific OCR engines.

---

## 4. Observability and Testing

- **Comprehensive Test Suite**:
  - Security regression tests (CORS, DoS, Path Traversal).
  - Multi-process parallel execution and load stress tests.
  - End-to-end verification on real-world sample documents.
- **Structured Logging**: Outputs structured logs across all conversion stages for easier debugging.
