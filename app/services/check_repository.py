"""
Service for managing the provider check repository.
"""
import json
import logging
from pathlib import Path
from typing import List, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


class CheckRepository:
    """
    Manages access to security checks organized by provider.

    Check files are stored in:
    providers/{provider}/services/{service}/{check_id}/{check_id}.metadata.json
    """

    def __init__(self, providers_dir: Path):
        # Ensure we have an absolute path
        self.providers_dir = Path(providers_dir).resolve()
        logger.info(f"CheckRepository initialized with providers_dir: {self.providers_dir}")

    def list_providers(self) -> List[dict]:
        """
        List all available providers with their check counts.

        Returns:
            List of provider info dicts with name, display_name, check_count
        """
        providers = []

        if not self.providers_dir.exists():
            logger.warning(f"Providers directory does not exist: {self.providers_dir}")
            return providers

        for provider_dir in self.providers_dir.iterdir():
            if not provider_dir.is_dir():
                continue

            # Skip hidden directories and non-provider folders
            if provider_dir.name.startswith('.') or provider_dir.name.startswith('_'):
                continue

            # Get check count by scanning services directory
            services_dir = provider_dir / "services"
            check_count = 0
            if services_dir.exists():
                # Recursively find all *.metadata.json files
                metadata_files = list(services_dir.rglob("*.metadata.json"))
                check_count = len(metadata_files)
                logger.debug(f"Provider {provider_dir.name}: found {check_count} checks in {services_dir}")

            # Try to load metadata if exists
            metadata_file = provider_dir / "_metadata.json"
            display_name = provider_dir.name.upper()

            if metadata_file.exists():
                try:
                    metadata = json.loads(metadata_file.read_text(encoding='utf-8'))
                    display_name = metadata.get("display_name", display_name)
                except (json.JSONDecodeError, IOError):
                    pass

            providers.append({
                "name": provider_dir.name,
                "display_name": display_name,
                "check_count": check_count
            })

        return sorted(providers, key=lambda x: x["name"])

    def provider_exists(self, provider: str) -> bool:
        """Check if a provider exists."""
        provider_dir = self.providers_dir / provider
        return provider_dir.exists() and provider_dir.is_dir()

    def get_checks(
        self,
        provider: str,
        search: Optional[str] = None,
        service: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[int, List[dict]]:
        """
        Get all checks for a provider.

        Args:
            provider: Provider name (aws, gcp, azure, etc.)
            search: Optional search string to filter by name/description
            service: Optional service name to filter by
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            Tuple of (total_count, list_of_checks)
        """
        provider_dir = self.providers_dir / provider / "services"

        if not provider_dir.exists():
            return 0, []

        checks = []

        # Recursively find all *.metadata.json files
        for metadata_file in provider_dir.rglob("*.metadata.json"):
            try:
                check_data = json.loads(metadata_file.read_text(encoding='utf-8'))

                # Apply service filter
                if service and check_data.get("ServiceName", "").lower() != service.lower():
                    continue

                # Apply search filter
                if search:
                    search_lower = search.lower()
                    searchable = f"{check_data.get('CheckID', '')} {check_data.get('CheckTitle', '')} {check_data.get('Description', '')}"
                    if search_lower not in searchable.lower():
                        continue

                checks.append(check_data)

            except (json.JSONDecodeError, IOError):
                continue

        # Sort by CheckID
        checks.sort(key=lambda x: x.get("CheckID", ""))

        # Get total before pagination
        total = len(checks)

        # Apply pagination
        checks = checks[offset:offset + limit]

        return total, checks

    def get_check_by_id(self, provider: str, check_id: str) -> Optional[dict]:
        """Get a specific check by ID."""
        provider_dir = self.providers_dir / provider / "services"

        if not provider_dir.exists():
            return None

        # Search for the check
        for metadata_file in provider_dir.rglob(f"{check_id}.metadata.json"):
            try:
                return json.loads(metadata_file.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, IOError):
                continue

        return None

    def get_checks_for_prompt(self, provider: str) -> str:
        """
        Format all checks for inclusion in Claude prompt.

        Returns a formatted string listing all checks with their key info.
        """
        _, checks = self.get_checks(provider, limit=10000)

        if not checks:
            return f"No checks found for provider: {provider}"

        lines = []
        for check in checks:
            line = f"- {check.get('CheckID', 'unknown')}: {check.get('CheckTitle', 'No title')}"
            service = check.get('ServiceName')
            severity = check.get('Severity')

            extra = []
            if service:
                extra.append(f"Service: {service}")
            if severity:
                extra.append(f"Severity: {severity}")

            if extra:
                line += f" ({', '.join(extra)})"

            lines.append(line)

        return "\n".join(lines)

    def validate_check_ids(self, provider: str, check_ids: List[str]) -> tuple[List[str], List[str]]:
        """
        Validate a list of check IDs.

        Returns:
            Tuple of (valid_ids, invalid_ids)
        """
        _, all_checks = self.get_checks(provider, limit=10000)
        all_check_ids = {c.get("CheckID") for c in all_checks}

        valid = [cid for cid in check_ids if cid in all_check_ids]
        invalid = [cid for cid in check_ids if cid not in all_check_ids]

        return valid, invalid


    def debug_info(self) -> dict:
        """
        Get detailed debug information about the repository.

        Returns:
            Dictionary with debug information
        """
        info = {
            "providers_dir": str(self.providers_dir),
            "providers_dir_exists": self.providers_dir.exists(),
            "providers_dir_is_dir": self.providers_dir.is_dir() if self.providers_dir.exists() else False,
            "providers": [],
            "errors": []
        }

        if not self.providers_dir.exists():
            info["errors"].append(f"Providers directory does not exist: {self.providers_dir}")
            return info

        # List all items in providers directory
        try:
            all_items = list(self.providers_dir.iterdir())
            info["providers_dir_contents"] = [str(item) for item in all_items]
        except Exception as e:
            info["errors"].append(f"Error listing providers_dir: {e}")
            return info

        # Check each provider
        for provider_dir in self.providers_dir.iterdir():
            if not provider_dir.is_dir():
                continue
            if provider_dir.name.startswith('.') or provider_dir.name.startswith('_'):
                continue

            provider_info = {
                "name": provider_dir.name,
                "path": str(provider_dir),
                "services_dir_exists": False,
                "check_count": 0,
                "sample_files": []
            }

            services_dir = provider_dir / "services"
            provider_info["services_dir"] = str(services_dir)
            provider_info["services_dir_exists"] = services_dir.exists()

            if services_dir.exists():
                # List service folders
                try:
                    service_folders = [d.name for d in services_dir.iterdir() if d.is_dir()]
                    provider_info["service_folders"] = service_folders[:10]  # First 10
                    provider_info["total_service_folders"] = len(service_folders)
                except Exception as e:
                    provider_info["error"] = f"Error listing services: {e}"

                # Find metadata files
                try:
                    metadata_files = list(services_dir.rglob("*.metadata.json"))
                    provider_info["check_count"] = len(metadata_files)
                    provider_info["sample_files"] = [str(f) for f in metadata_files[:5]]

                    # Try to read first file
                    if metadata_files:
                        try:
                            first_file = metadata_files[0]
                            content = json.loads(first_file.read_text(encoding='utf-8'))
                            provider_info["sample_check"] = {
                                "file": str(first_file),
                                "CheckID": content.get("CheckID"),
                                "CheckTitle": content.get("CheckTitle")
                            }
                        except Exception as e:
                            provider_info["sample_read_error"] = str(e)
                except Exception as e:
                    provider_info["glob_error"] = str(e)

            info["providers"].append(provider_info)

        return info


# Singleton instance
_repository: Optional[CheckRepository] = None


def get_check_repository() -> CheckRepository:
    """Get the singleton check repository instance."""
    global _repository
    if _repository is None:
        from app.config import get_settings
        settings = get_settings()
        _repository = CheckRepository(settings.providers_dir)
    return _repository


def reset_check_repository():
    """Reset the singleton instance (useful for testing or after config changes)."""
    global _repository
    _repository = None
