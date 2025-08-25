import re
from typing import Tuple

from .config import (
    YOUTUBE_DESCRIPTION_MAX_LENGTH,
    YOUTUBE_MAX_CONSECUTIVE_CAPS,
    YOUTUBE_MAX_PUNCTUATION,
    YOUTUBE_TITLE_MAX_LENGTH,
)


def is_nonempty(s: str) -> bool:
    """Check if a string is non-empty after trimming whitespace."""
    return bool(s and s.strip())


def validate_youtube_title(title: str) -> Tuple[bool, str]:
    """
    Validate YouTube title according to YouTube's requirements.
    Returns (is_valid, error_message)
    """
    if not is_nonempty(title):
        return False, "Title is required"

    title = title.strip()

    if len(title) < 1:
        return False, "Title must be at least 1 character"

    if len(title) > YOUTUBE_TITLE_MAX_LENGTH:
        return False, f"Title must be {YOUTUBE_TITLE_MAX_LENGTH} characters or less"

    # Check for excessive special characters or spam patterns
    if re.search(rf"[A-Z]{{{YOUTUBE_MAX_CONSECUTIVE_CAPS},}}", title):  # Excessive caps
        return (
            False,
            f"Title contains too many consecutive capital letters "
            f"(max: {YOUTUBE_MAX_CONSECUTIVE_CAPS})",
        )

    if (
        title.count("!") > YOUTUBE_MAX_PUNCTUATION
        or title.count("?") > YOUTUBE_MAX_PUNCTUATION
    ):
        return (
            False,
            f"Title contains too many punctuation marks "
            f"(max: {YOUTUBE_MAX_PUNCTUATION})",
        )

    return True, ""


def validate_youtube_description(description: str) -> Tuple[bool, str]:
    """
    Validate YouTube description according to YouTube's requirements.
    Returns (is_valid, error_message)
    """
    if not is_nonempty(description):
        return False, "Description is required"

    description = description.strip()

    if len(description) < 1:
        return False, "Description must be at least 1 character"

    if len(description) > YOUTUBE_DESCRIPTION_MAX_LENGTH:
        return (
            False,
            f"Description must be {YOUTUBE_DESCRIPTION_MAX_LENGTH} characters or less",
        )

    return True, ""


def can_upload(title: str, description: str) -> bool:
    """Check if both title and description are valid for YouTube upload."""
    title_valid, _ = validate_youtube_title(title)
    desc_valid, _ = validate_youtube_description(description)
    return title_valid and desc_valid


def get_validation_errors(title: str, description: str) -> list[str]:
    """Get all validation errors for title and description."""
    errors = []

    title_valid, title_error = validate_youtube_title(title)
    if not title_valid:
        errors.append(f"Title: {title_error}")

    desc_valid, desc_error = validate_youtube_description(description)
    if not desc_valid:
        errors.append(f"Description: {desc_error}")

    return errors
