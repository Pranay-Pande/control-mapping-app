"""
Background job execution and tracking for mapping operations.
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.job import Job, Upload, Configuration, Batch
from app.models.enums import JobStatus
from app.models.database import async_session_maker
from app.core.claude_runner import get_claude_runner
from app.core.prompt_builder import get_prompt_builder
from app.core.constants import get_provider_display_name
from app.services.check_repository import get_check_repository
from app.services.export_service import get_export_service
from app.schemas.output import MappingOutput

logger = logging.getLogger(__name__)


class JobManager:
    """
    Manages background job execution for control mapping.

    Jobs are executed asynchronously using asyncio.create_task().
    """

    def __init__(self):
        self._running_jobs: Dict[str, asyncio.Task] = {}
        self._running_batches: Dict[str, asyncio.Task] = {}

    async def start_batch(self, batch_id: str, job_ids: List[str]) -> None:
        """
        Start all jobs in a batch.

        Args:
            batch_id: UUID of the batch
            job_ids: List of job UUIDs to start
        """
        if batch_id in self._running_batches:
            logger.warning(f"Batch {batch_id} is already running")
            return

        task = asyncio.create_task(self._execute_batch(batch_id, job_ids))
        self._running_batches[batch_id] = task

        # Clean up when done
        task.add_done_callback(lambda t: self._running_batches.pop(batch_id, None))

        logger.info(f"Started batch {batch_id} with {len(job_ids)} jobs")

    async def _execute_batch(self, batch_id: str, job_ids: List[str]) -> None:
        """Execute all jobs in a batch sequentially."""
        for job_id in job_ids:
            await self._execute_job(job_id)

        # Update batch completion status
        async with async_session_maker() as session:
            batch = await session.get(Batch, batch_id)
            if batch:
                batch.completed_at = datetime.utcnow()
                batch.updated_at = datetime.utcnow()
                await session.commit()

    async def start_job(self, job_id: str) -> None:
        """
        Start a single mapping job in the background.

        Args:
            job_id: UUID of the job to start
        """
        if job_id in self._running_jobs:
            logger.warning(f"Job {job_id} is already running")
            return

        task = asyncio.create_task(self._execute_job(job_id))
        self._running_jobs[job_id] = task

        # Clean up when done
        task.add_done_callback(lambda t: self._running_jobs.pop(job_id, None))

        logger.info(f"Started job {job_id}")

    async def _execute_job(self, job_id: str) -> None:
        """Execute a mapping job."""
        async with async_session_maker() as session:
            try:
                # Load job and related data
                job = await session.get(Job, job_id)
                if not job:
                    logger.error(f"Job {job_id} not found")
                    return

                upload = await session.get(Upload, job.upload_id)
                config = await session.get(Configuration, job.configuration_id)

                if not upload or not config:
                    await self._fail_job(session, job, "Upload or configuration not found")
                    return

                # Update status to running
                await self._update_job_status(
                    session, job,
                    status=JobStatus.RUNNING,
                    message="Starting mapping process..."
                )

                # Build the prompt
                prompt_builder = get_prompt_builder()
                check_repo = get_check_repository()

                # Get checks list for this job's provider (not config.providers)
                checks_list = check_repo.get_checks_for_prompt(job.provider)

                # Get extracted text from upload (already extracted during upload)
                framework_content = upload.extracted_text
                if not framework_content:
                    await self._fail_job(session, job, "No extracted text found for uploaded file")
                    return

                logger.info(f"Job {job_id} ({job.provider}): Using extracted text: {len(framework_content)} chars")

                # Build prompt with embedded content (not file path)
                # This approach passes the text directly to Claude instead of asking it to read files
                user_prompt = prompt_builder.build_simple_prompt(
                    framework_name=config.framework_name,
                    framework_version=config.framework_version,
                    provider=job.provider,  # Use job's provider, not config
                    framework_content=framework_content,
                    checks_list=checks_list,
                    field_mappings=config.field_mappings or {},
                    custom_instructions=config.custom_instructions,
                    framework_full_name=config.framework_full_name,
                    framework_description=config.framework_description,
                    enable_subgroup=config.enable_subgroup
                )
                system_prompt = prompt_builder.system_template

                await self._update_job_status(
                    session, job,
                    percentage=10,
                    message=f"Executing Claude Code for {job.provider}..."
                )

                # Execute Claude
                claude_runner = get_claude_runner()
                result = await claude_runner.run_mapping(
                    prompt=user_prompt,
                    system_prompt=system_prompt
                )

                await self._update_job_status(
                    session, job,
                    percentage=70,
                    message="Processing output..."
                )

                # Standardize the Provider field in the output
                # This ensures consistent provider naming regardless of Claude's output
                result["Provider"] = get_provider_display_name(job.provider)

                # Override the Name field if user provided a framework_full_name
                if config.framework_full_name:
                    result["Name"] = config.framework_full_name

                # Override the Description field if user provided a framework_description
                if config.framework_description:
                    result["Description"] = config.framework_description

                # Remove SubGroup field from output if disabled
                if not config.enable_subgroup and "Requirements" in result:
                    for req in result["Requirements"]:
                        if "SubGroup" in req:
                            del req["SubGroup"]

                # Validate and parse output
                mapping_output = self._validate_output(result)

                # Generate summary
                summary = mapping_output.get_summary()

                await self._update_job_status(
                    session, job,
                    percentage=80,
                    message="Generating output files..."
                )

                # Export to files with framework and provider in filename
                export_service = get_export_service()
                json_path = await export_service.export_json(
                    job_id, result,
                    framework_name=config.framework_name,
                    provider=job.provider
                )
                excel_path = await export_service.export_excel(
                    job_id, result,
                    framework_name=config.framework_name,
                    provider=job.provider
                )

                # Complete the job
                await self._complete_job(
                    session, job,
                    json_path=str(json_path),
                    excel_path=str(excel_path),
                    summary=summary
                )

                logger.info(f"Job {job_id} ({job.provider}) completed successfully")

            except Exception as e:
                logger.exception(f"Job {job_id} failed: {e}")
                if 'job' in locals():
                    await self._fail_job(session, job, str(e))

    def _validate_output(self, result: dict) -> MappingOutput:
        """Validate and parse the mapping output."""
        try:
            return MappingOutput(**result)
        except Exception as e:
            raise ValueError(f"Invalid mapping output format: {e}")

    async def _update_job_status(
        self,
        session: AsyncSession,
        job: Job,
        status: Optional[JobStatus] = None,
        percentage: Optional[int] = None,
        message: Optional[str] = None
    ) -> None:
        """Update job status fields."""
        if status:
            job.status = status.value
        if percentage is not None:
            job.progress_percentage = percentage
        if message:
            job.progress_message = message
        job.updated_at = datetime.utcnow()

        await session.commit()

    async def _complete_job(
        self,
        session: AsyncSession,
        job: Job,
        json_path: str,
        excel_path: str,
        summary: dict
    ) -> None:
        """Mark a job as completed."""
        job.status = JobStatus.COMPLETED.value
        job.progress_percentage = 100
        job.progress_message = "Mapping completed successfully"
        job.output_json_path = json_path
        job.output_excel_path = excel_path
        job.result_summary = summary
        job.completed_at = datetime.utcnow()
        job.updated_at = datetime.utcnow()

        await session.commit()

    async def _fail_job(
        self,
        session: AsyncSession,
        job: Job,
        error_message: str
    ) -> None:
        """Mark a job as failed."""
        job.status = JobStatus.FAILED.value
        job.error_message = error_message
        job.progress_message = "Job failed"
        job.updated_at = datetime.utcnow()

        await session.commit()

    def is_job_running(self, job_id: str) -> bool:
        """Check if a job is currently running."""
        return job_id in self._running_jobs

    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.

        Returns:
            True if job was cancelled, False if not running
        """
        task = self._running_jobs.get(job_id)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            return True
        return False


# Singleton instance
_manager: Optional[JobManager] = None


def get_job_manager() -> JobManager:
    """Get the singleton job manager instance."""
    global _manager
    if _manager is None:
        _manager = JobManager()
    return _manager
