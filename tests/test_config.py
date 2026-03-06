import os
import importlib
from pathlib import Path
from unittest.mock import patch
import docling_lib.config

def test_config_env_vars():
    new_upload = "/tmp/custom_uploads"
    new_output = "/tmp/custom_output"

    # Test that environment variables are picked up
    with patch.dict(os.environ, {"DOCLING_UPLOAD_DIR": new_upload, "DOCLING_OUTPUT_DIR": new_output}):
        importlib.reload(docling_lib.config)
        assert docling_lib.config.UPLOAD_DIR == Path(new_upload)
        assert docling_lib.config.OUTPUT_DIR == Path(new_output)

    # Reset to default and verify default values
    if "DOCLING_UPLOAD_DIR" in os.environ:
        del os.environ["DOCLING_UPLOAD_DIR"]
    if "DOCLING_OUTPUT_DIR" in os.environ:
        del os.environ["DOCLING_OUTPUT_DIR"]

    importlib.reload(docling_lib.config)
    assert docling_lib.config.UPLOAD_DIR == Path("uploads")
    assert docling_lib.config.OUTPUT_DIR == Path("output")
