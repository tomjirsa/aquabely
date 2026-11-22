import hashlib
from pathlib import Path

FORMAT_PLACEHOLDER = "— choose a format —"


def needs_format_choice(detected) -> bool:
    """True when detection failed and the user must pick a format explicitly."""
    return detected is None


def format_options(format_ids, detected):
    """Selectbox options: a leading None placeholder only when detection failed."""
    return [None, *format_ids] if needs_format_choice(detected) else list(format_ids)


def write_if_changed(dest: Path, data: bytes) -> bool:
    """Write data to dest only if missing or different. Returns True if written."""
    if dest.exists() and dest.read_bytes() == data:
        return False
    dest.write_bytes(data)
    return True


def upload_path(inbox: Path, data: bytes) -> Path:
    """Inbox path for uploaded bytes: named by content hash, never by user input."""
    return inbox / f"{hashlib.sha256(data).hexdigest()}.pdf"
