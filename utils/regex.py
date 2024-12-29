# utils/regex.py
import re


def is_valid_name(name: str) -> bool:
    """
    Validate the user's name.

    Args:
        name: The name to validate.

    Returns:
        True if the name is valid, otherwise False.
    """
    if not name or len(name) > 50:  # Adjust the maximum length as needed
        return False
    # Check if the name contains only allowed characters (letters, spaces, hyphens)
    if not re.match(r"^[A-Za-z\s\-']+$", name):
        return False
    return True

def validate_phone(phone: str) -> bool:
    """Validate phone number format."""
    pattern = r'^\+?[1-9]\d{1,14}$'
    return bool(re.match(pattern, phone))

def format_phone(phone: str) -> str:
    """Format phone number to E.164 format."""
    # Remove all non-digit characters
    clean_phone = re.sub(r'\D', '', phone)
    # Add + prefix if not present
    return f"+{clean_phone}" if not clean_phone.startswith('+') else clean_phone
