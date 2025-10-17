"""ID generation utilities."""

import time
import uuid


def generate_id(prefix: str = "msg") -> str:
    """Generate a time-based ID."""
    return f"{prefix}_{int(time.time() * 1000)}"


def generate_uuid(prefix: str = "") -> str:
    """Generate a UUID-based ID."""
    uid = uuid.uuid4().hex[:16]
    return f"{prefix}_{uid}" if prefix else uid
