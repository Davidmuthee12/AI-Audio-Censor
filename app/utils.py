def slugify(value: str) -> str:
    """
    Convert a string to a slug format.

    This function converts the input string to lowercase, replaces spaces with hyphens,
    and removes any characters that are not alphanumeric, hyphens or periods.
    """
    import re

    value = value.lower()
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^a-z0-9.\-]", "", value)
    return value
