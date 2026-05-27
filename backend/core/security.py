"""Input sanitization, prompt-injection detection, and file validation.

This module is the single place that decides what counts as safe user input.
Two principles guide it:

1. **Sanitize, don't trust.** Every user-provided string is length-checked and
   stripped before it reaches the LLM or the database.
2. **Detect, log, but rarely block.** Prompt-injection phrases are flagged for
   monitoring rather than rejected outright — a legitimate CV may genuinely
   contain words like "system" or "instructions". The real defense is the
   delimited prompt structure in :func:`wrap_user_content`, not keyword bans.
"""

import logging
import re

logger = logging.getLogger("deployme.security")

# Sentinel tags used to fence user content inside LLM prompts. The model is
# instructed (in the system prompt) to treat everything between them as data.
USER_CONTENT_OPEN = "<user_content>"
USER_CONTENT_CLOSE = "</user_content>"

# PDF magic bytes — every valid PDF starts with "%PDF-".
PDF_MAGIC = b"%PDF-"
MAX_PDF_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_PDF_MIME = {"application/pdf", "application/x-pdf"}

# Phrases commonly seen in prompt-injection attempts. Used for *logging only*.
_INJECTION_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"ignore (all|any|the)?\s*(previous|prior|above)\s+instructions",
        r"disregard (all|any|the)?\s*(previous|prior|above)",
        r"forget (everything|all|your) (instructions|prompt)",
        r"you are now (a|an|in)\b",
        r"\bsystem prompt\b",
        r"\bdeveloper mode\b",
        r"act as (a|an)\b",
        r"</?\s*user_content\s*>",  # attempts to forge our own delimiters
        r"\bjailbreak\b",
    )
]


class FileValidationError(ValueError):
    """Raised when an uploaded file fails validation. Message is user-safe."""


def sanitize_text(text: str, *, max_length: int, field_name: str = "input") -> str:
    """Strip whitespace and enforce a maximum length on a user string.

    Args:
        text: The raw user-provided string.
        max_length: Maximum allowed length after stripping.
        field_name: Name used in the error message (kept generic, no internals).

    Returns:
        The stripped string.

    Raises:
        ValueError: If the stripped string exceeds ``max_length``.
    """
    cleaned = text.strip()
    if len(cleaned) > max_length:
        raise ValueError(
            f"{field_name} is too long (max {max_length} characters)."
        )
    return cleaned


def detect_injection_patterns(text: str) -> list[str]:
    """Return a list of injection-pattern names found in ``text``.

    This never modifies or blocks the input. Callers should log a flag when the
    result is non-empty so suspicious activity can be monitored.
    """
    return [p.pattern for p in _INJECTION_PATTERNS if p.search(text)]


def log_if_suspicious(text: str, *, context: str) -> None:
    """Log (at WARNING) when ``text`` matches known injection patterns.

    Only the matched pattern names and a short context label are logged — never
    the full user text, which may contain personal data from a CV.
    """
    matches = detect_injection_patterns(text)
    if matches:
        logger.warning(
            "Possible prompt-injection content flagged in %s (patterns: %s)",
            context,
            ", ".join(matches),
        )


def wrap_user_content(text: str) -> str:
    """Fence user text in delimiters for safe inclusion in an LLM prompt.

    Any literal occurrence of our delimiter tags inside the user text is
    neutralized first, so a malicious CV cannot "close" the fence early and
    smuggle instructions back into the system context.
    """
    neutralized = text.replace(USER_CONTENT_OPEN, "< user_content >").replace(
        USER_CONTENT_CLOSE, "< /user_content >"
    )
    return f"{USER_CONTENT_OPEN}\n{neutralized}\n{USER_CONTENT_CLOSE}"


def validate_pdf_upload(
    *, filename: str, content_type: str | None, data: bytes
) -> None:
    """Validate an uploaded PDF three ways: extension, MIME type, magic bytes.

    Args:
        filename: The client-supplied filename.
        content_type: The client-supplied MIME type (may be ``None``).
        data: The raw file bytes.

    Raises:
        FileValidationError: If any check fails. The message is safe to return
            to the client (no internal paths or library details).
    """
    if not filename.lower().endswith(".pdf"):
        raise FileValidationError("Only .pdf files are accepted.")

    if content_type is not None and content_type.lower() not in ALLOWED_PDF_MIME:
        raise FileValidationError("File does not appear to be a PDF.")

    if len(data) == 0:
        raise FileValidationError("The uploaded file is empty.")

    if len(data) > MAX_PDF_BYTES:
        raise FileValidationError("File is too large (max 5 MB).")

    if not data.startswith(PDF_MAGIC):
        raise FileValidationError("File is not a valid PDF.")
