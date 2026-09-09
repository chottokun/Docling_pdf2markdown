# Testing & Quality Assurance Guide

Language: [English](TESTING.md) | [日本語](../TESTING.md)

This guide covers running the test suite, real-data verification, Docker tests, and security regression checks.

---

## 1. Running the Test Suite

Execute the complete test suite (360+ unit and integration tests) using `uv`:

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_converter.py

# Run with verbose output and coverage
uv run pytest -v --cov=src
```

---

## 2. Real-Data & Integration Testing

Test document conversion against real sample files (`.pdf`, `.docx`, `.pptx`, `.xlsx`) located in `tests/test_data/`:

```bash
# Run real data conversion check
uv run python scripts/verify_real_data.py

# Run FastAPI real-data E2E API check
uv run python tests/e2e_real_api_check.py
```

---

## 3. Docker Container E2E Verification

Validate containerized API endpoints, CORS handling, rate limiting, file downloads, and Prometheus metrics:

```bash
# 1. Start Docker container
docker compose up -d --build

# 2. Run container E2E verification
uv run python tests/e2e_docker_check.py
```

---

## 4. Security Regression Tests

Security tests cover protection against:
- **Path Traversal**: `tests/test_path_traversal.py`, `tests/test_output_security.py`
- **Log Injection**: `tests/repro_log_injection_fix.py`, `tests/verify_log_injection_fix.py`
- **DoS & File Size Limits**: `tests/test_dos_protection.py`
- **Rate Limiting & Authentication**: `tests/test_security_auth_rate_limit.py`
- **CORS Configuration**: `tests/test_cors_security.py`

Run security tests specifically:
```bash
uv run pytest tests/test_security*.py tests/test_path_traversal.py tests/test_dos_protection.py
```
