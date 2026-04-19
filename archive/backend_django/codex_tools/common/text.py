"""
codex_tools.common.text
=======================
Universal tools for working with text.
Framework-agnostic (does not depend on Django).
"""


def normalize_name(name: str) -> str:
    """
    Brings first/last name to a standard form: 'Ivan' or 'Ivan-Ivanovich'.
    """
    if not name:
        return ""

    # Remove extra spaces and Capitalize
    parts = name.strip().split("-")
    normalized_parts = [p.strip().capitalize() for p in parts if p.strip()]

    return "-".join(normalized_parts)


def clean_string(text: str) -> str:
    """Removes extra spaces and invisible characters."""
    if not text:
        return ""
    return " ".join(text.split())
