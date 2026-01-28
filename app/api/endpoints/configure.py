"""
Configuration endpoint for mapping jobs.
"""
import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import get_db_session
from app.models.job import Upload, Configuration
from app.schemas.configure import ConfigureRequest, ConfigureResponse, ProviderInfo
from app.services.check_repository import get_check_repository

router = APIRouter()


@router.post("/configure", response_model=ConfigureResponse)
async def configure_mapping(
    request: ConfigureRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Configure field mappings and providers for a mapping job.
    """
    # Verify upload exists
    upload = await db.get(Upload, request.upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    # Verify all providers exist and collect check counts
    check_repo = get_check_repository()
    provider_infos = []
    total_checks = 0

    for provider in request.providers:
        if not check_repo.provider_exists(provider):
            providers = check_repo.list_providers()
            provider_names = [p["name"] for p in providers]
            raise HTTPException(
                status_code=400,
                detail=f"Provider '{provider}' not found. Available: {', '.join(provider_names)}"
            )
        check_count, _ = check_repo.get_checks(provider)
        provider_infos.append(ProviderInfo(name=provider, check_count=check_count))
        total_checks += check_count

    # Create configuration record
    config_id = str(uuid.uuid4())
    config = Configuration(
        id=config_id,
        upload_id=request.upload_id,
        framework_name=request.framework_name,
        framework_version=request.framework_version,
        framework_full_name=request.framework_full_name,
        framework_description=request.framework_description,
        providers=request.providers,  # Store as JSON array
        enable_subgroup=request.enable_subgroup,
        field_mappings=request.field_mappings.model_dump() if request.field_mappings else {},
        custom_instructions=request.custom_instructions
    )

    db.add(config)
    await db.commit()

    return ConfigureResponse(
        configuration_id=config_id,
        providers=provider_infos,
        total_checks=total_checks
    )
