from __future__ import annotations


def log_experience(text: str) -> str:
    """Stage-1 behavior: print incoming text and return a confirmation string."""
    clean_text = text.strip()
    print(f"[log_experience] {clean_text}")
    return f"logged(stage1): {clean_text}"


def update_bullet(experience_id: str, bullet: str) -> str:
    """Placeholder for stage-2 implementation."""
    return f"TODO(stage2) update bullet for {experience_id}: {bullet}"
