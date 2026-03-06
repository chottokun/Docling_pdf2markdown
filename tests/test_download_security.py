import pytest
from src.docling_lib.server import download_file, OUTPUT_DIR
from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import FileResponse

@pytest.mark.asyncio
async def test_download_file_logic_fix():
    # Create a sensitive file in the root for testing
    sensitive_file = Path("sensitive_logic.txt")
    sensitive_file.write_text("logic secret")

    try:
        # file_path = OUTPUT_DIR / ".." / "sensitive_logic.txt"
        # which is "output/../sensitive_logic.txt" -> "sensitive_logic.txt"

        with pytest.raises(HTTPException) as excinfo:
            await download_file("..", "sensitive_logic.txt")

        assert excinfo.value.status_code in [400, 403, 404]
        print(f"FIX VERIFIED: Handler blocked traversal via request_id with {excinfo.value.status_code}")

    finally:
        if sensitive_file.exists():
            sensitive_file.unlink()

@pytest.mark.asyncio
async def test_download_file_logic_fix_filename():
    sensitive_file = Path("sensitive_logic_nested.txt")
    sensitive_file.write_text("logic secret nested")

    test_id = "test_id"
    (OUTPUT_DIR / test_id).mkdir(parents=True, exist_ok=True)

    try:
        # file_path = OUTPUT_DIR / test_id / "../../sensitive_logic_nested.txt"
        with pytest.raises(HTTPException) as excinfo:
            await download_file(test_id, "../../sensitive_logic_nested.txt")

        assert excinfo.value.status_code in [400, 403, 404]
        print(f"FIX VERIFIED: Handler blocked traversal via filename with {excinfo.value.status_code}")

    finally:
        if sensitive_file.exists():
            sensitive_file.unlink()
        if (OUTPUT_DIR / test_id).exists():
            (OUTPUT_DIR / test_id).rmdir()

@pytest.mark.asyncio
async def test_download_file_valid_request():
    test_id = "test_id_valid"
    filename = "result.md"
    request_dir = OUTPUT_DIR / test_id
    request_dir.mkdir(parents=True, exist_ok=True)
    file_path = request_dir / filename
    file_path.write_text("markdown content")

    try:
        response = await download_file(test_id, filename)
        assert isinstance(response, FileResponse)
        assert Path(response.path).resolve() == file_path.resolve()
        print("FIX VERIFIED: Valid request still works")
    finally:
        if file_path.exists():
            file_path.unlink()
        if request_dir.exists():
            request_dir.rmdir()
