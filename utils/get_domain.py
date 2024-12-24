def extract_domain(full_string):
    """
    Extracts the domain from a string of the format `ads.google.com	`.

    Parameters:
        full_string (str): The full string containing subdomains and domain.

    Returns:
        str: The extracted domain (e.g., `google.com`).
    """
    parts = full_string.split('.')
    if len(parts) >= 2:
        domain = '.'.join(parts[-2:])
        return domain
    return ""  # Return an empty string if the input is malformed
