"""
Application constants and mappings.
"""

# Standardized provider display names for output JSON
PROVIDER_DISPLAY_NAMES = {
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "github": "GitHub",
    "kubernetes": "Kubernetes",
    "m365": "M365",
    "nhn": "NHN",
    "oraclecloud": "OracleCloud",
    "alibabacloud": "alibabacloud",
}


def get_provider_display_name(provider_key: str) -> str:
    """
    Get the standardized display name for a provider.

    Args:
        provider_key: The provider key (e.g., 'aws', 'azure')

    Returns:
        The standardized display name (e.g., 'AWS', 'Azure')
    """
    return PROVIDER_DISPLAY_NAMES.get(provider_key.lower(), provider_key)
