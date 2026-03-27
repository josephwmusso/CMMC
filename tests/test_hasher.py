"""
tests/test_hasher.py

Tests for evidence hashing pipeline.
Run: pytest tests/test_hasher.py -v
"""

import os
import tempfile
import pytest

from src.evidence.hasher import hash_file, hash_artifact, generate_manifest, verify_hash


@pytest.fixture
def tmp_file():
    """Create a temp file with known content, yield its path, then delete."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(b"CMMC evidence content for testing")
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def empty_file():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        path = f.name
    yield path
    os.unlink(path)


class TestHashFile:
    def test_returns_hex_string(self, tmp_file):
        result = hash_file(tmp_file)
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex digest is always 64 chars

    def test_deterministic(self, tmp_file):
        assert hash_file(tmp_file) == hash_file(tmp_file)

    def test_different_content_different_hash(self, tmp_file):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"completely different content")
            other = f.name
        try:
            assert hash_file(tmp_file) != hash_file(other)
        finally:
            os.unlink(other)

    def test_empty_file(self, empty_file):
        # SHA-256 of empty string is well-known
        result = hash_file(empty_file)
        assert result == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_nonexistent_file_raises(self):
        with pytest.raises(FileNotFoundError):
            hash_file("/nonexistent/path/file.txt")


class TestHashArtifact:
    def test_returns_full_metadata(self, tmp_file):
        result = hash_artifact(tmp_file)
        assert result["filename"] == os.path.basename(tmp_file)
        assert result["file_path"] == tmp_file
        assert len(result["sha256"]) == 64
        assert result["algorithm"] == "SHA-256"
        assert result["file_size"] > 0
        assert "timestamp" in result

    def test_file_size_matches(self, tmp_file):
        result = hash_artifact(tmp_file)
        assert result["file_size"] == os.path.getsize(tmp_file)

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            hash_artifact("/does/not/exist.pdf")


class TestVerifyHash:
    def test_valid_hash_returns_true(self, tmp_file):
        good_hash = hash_file(tmp_file)
        assert verify_hash(tmp_file, good_hash) is True

    def test_wrong_hash_returns_false(self, tmp_file):
        assert verify_hash(tmp_file, "a" * 64) is False

    def test_tampered_file_detected(self, tmp_file):
        original_hash = hash_file(tmp_file)
        # Tamper the file
        with open(tmp_file, "ab") as f:
            f.write(b" TAMPERED")
        assert verify_hash(tmp_file, original_hash) is False


class TestGenerateManifest:
    def test_manifest_contains_all_artifacts(self):
        artifacts = [
            {"filename": "policy.pdf", "sha256": "a" * 64, "algorithm": "SHA-256", "file_size": 1024},
            {"filename": "config.xlsx", "sha256": "b" * 64, "algorithm": "SHA-256", "file_size": 2048},
        ]
        manifest = generate_manifest(artifacts, org_name="Test Org")
        assert "policy.pdf" in manifest
        assert "config.xlsx" in manifest
        assert "a" * 64 in manifest
        assert "b" * 64 in manifest
        assert "Test Org" in manifest

    def test_manifest_is_string(self):
        artifacts = [
            {"filename": "test.pdf", "sha256": "c" * 64, "algorithm": "SHA-256", "file_size": 512},
        ]
        result = generate_manifest(artifacts, org_name="Org")
        assert isinstance(result, str)
        assert len(result) > 0
