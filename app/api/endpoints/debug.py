"""
Debug endpoints for troubleshooting.
"""
from pathlib import Path
from fastapi import APIRouter

from app.config import get_settings, PROJECT_ROOT
from app.services.check_repository import get_check_repository, reset_check_repository

router = APIRouter()


@router.get("/debug/checks")
async def debug_checks():
    """
    Debug endpoint to troubleshoot check repository issues.

    Returns detailed information about:
    - Path configuration
    - Provider directories
    - Check files found
    """
    settings = get_settings()

    # Reset the repository to get fresh state
    reset_check_repository()
    repo = get_check_repository()

    debug_info = {
        "config": {
            "PROJECT_ROOT": str(PROJECT_ROOT),
            "providers_dir_setting": str(settings.providers_dir),
        },
        "repository": repo.debug_info()
    }

    return debug_info


@router.get("/debug/paths")
async def debug_paths():
    """
    Debug endpoint to check all configured paths.
    """
    settings = get_settings()

    paths = {
        "PROJECT_ROOT": {
            "value": str(PROJECT_ROOT),
            "exists": PROJECT_ROOT.exists(),
            "is_dir": PROJECT_ROOT.is_dir()
        },
        "providers_dir": {
            "value": str(settings.providers_dir),
            "exists": settings.providers_dir.exists(),
            "is_dir": settings.providers_dir.is_dir() if settings.providers_dir.exists() else False
        },
        "upload_dir": {
            "value": str(settings.upload_dir),
            "exists": settings.upload_dir.exists()
        },
        "output_dir": {
            "value": str(settings.output_dir),
            "exists": settings.output_dir.exists()
        },
        "prompts_dir": {
            "value": str(settings.prompts_dir),
            "exists": settings.prompts_dir.exists()
        }
    }

    # List contents of providers_dir if it exists
    if settings.providers_dir.exists():
        try:
            contents = []
            for item in settings.providers_dir.iterdir():
                contents.append({
                    "name": item.name,
                    "is_dir": item.is_dir(),
                    "path": str(item)
                })
            paths["providers_dir"]["contents"] = contents
        except Exception as e:
            paths["providers_dir"]["error"] = str(e)

    return paths
