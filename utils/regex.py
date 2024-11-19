import re


def isValidName(name):

    if not name or len(name) > 50:  # Adjust the maximum length as needed
        return False
    # Check if the name contains any Cyrillic characters
    if not re.match(r"^[A-Za-z0-9\s\-_\.]+$", name):
        return False
    # Add any additional validation logic here if needed
    return True
