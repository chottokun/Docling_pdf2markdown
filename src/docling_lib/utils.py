def sanitize_log_message(message: str) -> str:
    """
    Sanitizes a message for logging by replacing newline characters with spaces.
    This prevents log injection vulnerabilities.
    """
    if not isinstance(message, str):
        message = str(message)
    return message.replace("\n", " ").replace("\r", " ")
