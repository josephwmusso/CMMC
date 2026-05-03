"""
SHA-256 hashing pipeline for CMMC evidence artifacts.
Generates individual hashes and CMMC-format manifests compatible with eMASS upload.
"""
import hashlib
import json
import os
from datetime import datetime, timezone


def hash_file(file_path: str, chunk_size: int = 8192) -> str:
    """Compute SHA-256 hash of a file. Returns hex digest."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def hash_artifact(file_path: str) -> dict:
    """Hash a single artifact and return full metadata."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Artifact not found: {file_path}")

    return {
        "filename": os.path.basename(file_path),
        "file_path": file_path,
        "sha256": hash_file(file_path),
        "algorithm": "SHA-256",
        "file_size": os.path.getsize(file_path),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def verify_hash(file_path: str, expected_hash: str) -> bool:
    """Verify a file's SHA-256 matches the expected hash."""
    actual = hash_file(file_path)
    return actual == expected_hash


def generate_manifest(artifacts: list[dict], org_name: str = "Unknown") -> str:
    """
    Generate CMMC-format hash manifest for eMASS upload.

    Format per line: SHA256  <hash>  <filename>
    Ends with a manifest-of-manifests hash to prove integrity.
    """
    now = datetime.now(timezone.utc).isoformat()

    header_lines = [
        f"# CMMC Evidence Hash Manifest",
        f"# Organization: {org_name}",
        f"# Generated: {now}",
        f"# Algorithm: SHA-256",
        f"# Artifact Count: {len(artifacts)}",
        f"#",
    ]

    artifact_lines = []
    for a in sorted(artifacts, key=lambda x: x["filename"]):
        artifact_lines.append(f"SHA256  {a['sha256']}  {a['filename']}")

    # Hash the artifact section itself (manifest-of-manifests)
    artifact_block = "\n".join(artifact_lines)
    manifest_hash = hashlib.sha256(artifact_block.encode("utf-8")).hexdigest()

    footer_lines = [
        f"---",
        f"# Manifest Integrity Hash",
        f"SHA256  {manifest_hash}  MANIFEST_INTEGRITY",
        f"# End of manifest",
    ]

    all_lines = header_lines + artifact_lines + footer_lines
    return "\n".join(all_lines)


def save_manifest(manifest_text: str, output_dir: str, org_name: str = "export") -> str:
    """Save manifest to a timestamped file. Returns the file path."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = org_name.replace(" ", "_")
    filename = f"MANIFEST_{safe_name}_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(manifest_text)
    return filepath


def hash_dict(d: dict) -> str:
    """SHA-256 hex digest of a dict via canonical JSON serialization.

    Matches the audit-chain canonical-bytes pattern (json.dumps with
    sort_keys=True, default=str). Use for content hashes of dict-shaped
    evidence payloads or anywhere a stable digest of structured data
    is needed.
    """
    payload = json.dumps(d, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()