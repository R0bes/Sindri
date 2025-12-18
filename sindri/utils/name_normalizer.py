"""Helper functions to normalize project names for PEP 508 compliance."""

import re


def normalize_project_name(name: str) -> str:
    """
    Normalize project name to be PEP 508 compliant.
    
    PEP 508 requires:
    - Only ASCII letters, digits, underscores, hyphens, and periods
    - Must begin and end with ASCII letters or digits
    
    Args:
        name: Original project name
        
    Returns:
        Normalized project name
    """
    if not name:
        return "project"
    
    # Convert to lowercase
    normalized = name.lower()
    
    # Replace invalid characters with hyphens
    # Keep only: letters, digits, underscores, hyphens, periods
    normalized = re.sub(r"[^a-z0-9._-]", "-", normalized)
    
    # Remove consecutive hyphens/periods
    normalized = re.sub(r"[-.]+", "-", normalized)
    
    # Remove leading/trailing hyphens, periods, underscores
    normalized = normalized.strip(".-_")
    
    # Ensure it starts and ends with a letter or digit
    if not normalized:
        return "project"
    
    # If it doesn't start with a letter/digit, prepend a letter
    if not normalized[0].isalnum():
        normalized = "p" + normalized
    
    # If it doesn't end with a letter/digit, append a digit
    if not normalized[-1].isalnum():
        normalized = normalized + "0"
    
    return normalized

