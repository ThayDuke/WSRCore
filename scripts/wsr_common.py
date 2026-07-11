import os
import sys
sys.dont_write_bytecode = True
import json
import hashlib
import tempfile

# Standardized exit codes
EXIT_SUCCESS = 0
EXIT_FAIL_FINDING = 1
EXIT_INVALID_ARGS = 2
EXIT_IO_TRANSACTION_ERROR = 3
EXIT_SAFETY_REJECTION = 4

def get_package_root():
    """Find package root based on this script's location."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(current_dir)

def load_manifest(package_root):
    """Load and parse manifest file strictly using UTF-8."""
    manifest_path = os.path.join(package_root, "WSR_MANIFEST.json")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        # strict loading
        return json.load(f)

def validate_relative_path(path_str):
    """Check that path is relative and does not escape via dot-dots."""
    normalized = os.path.normpath(path_str)
    if os.path.isabs(normalized) or normalized.startswith("..") or "/../" in normalized.replace('\\', '/') or normalized.endswith("/..") or normalized.startswith("../"):
        return False
    return True

def safe_resolve_path(package_root, relative_path):
    """Resolve a relative path within the package root and verify containment using realpath/commonpath."""
    if not validate_relative_path(relative_path):
        raise ValueError(f"Path escape attempt or absolute path detected: {relative_path}")
        
    abs_base = os.path.realpath(package_root)
    abs_target = os.path.realpath(os.path.join(abs_base, relative_path))
    
    # Verify path containment using commonpath to prevent sibling prefix issues
    try:
        common = os.path.commonpath([abs_base, abs_target])
    except ValueError as e:
        raise ValueError(f"Path resolution error (drive mismatch or invalid format): {e}")
        
    if common != abs_base:
        raise ValueError(f"Resolved path lies outside base directory: {relative_path}")
        
    # Symlink safety gate: reject symlink operations
    if os.path.islink(abs_target) or os.path.islink(os.path.join(abs_base, relative_path)):
        raise ValueError(f"Symlinks or junctions are rejected for security: {relative_path}")
        
    return abs_target

def calculate_sha256(filepath):
    """Calculate SHA-256 checksum of a file in binary mode."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def atomic_write_text(filepath, content, encoding="utf-8"):
    """Write text content to a file atomically via temporary file replacement."""
    dir_name = os.path.dirname(filepath)
    os.makedirs(dir_name, exist_ok=True)
    
    # Write to a temporary file in the same directory to ensure same filesystem for atomic replace
    fd, temp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="\n") as f:
            f.write(content)
        # Atomic rename
        os.replace(temp_path, filepath)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e

def print_json_report(report_dict):
    """Output standardized JSON report to stdout."""
    print(json.dumps(report_dict, indent=2, ensure_ascii=False))

def format_alert(alert_type, title, message=None):
    """Format GitHub-style alerts."""
    lines = [f"> [!{alert_type.upper()}]", f"> {title}"]
    if message:
        for msg_line in message.split("\n"):
            lines.append(f"> {msg_line}")
    return "\n".join(lines)
