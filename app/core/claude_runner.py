"""
Claude Code CLI subprocess wrapper for mapping operations.

Uses ThreadPoolExecutor for Windows compatibility since asyncio subprocess
doesn't work with the default event loop on Windows.
"""
import asyncio
import subprocess
import json
import re
import logging
from pathlib import Path
from typing import Optional, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor
from app.core.exceptions import ClaudeExecutionError, ClaudeTimeoutError, OutputParsingError
from app.config import get_settings

logger = logging.getLogger(__name__)


class ClaudeCodeRunner:
    """
    Wrapper for executing Claude Code CLI as a subprocess.

    Claude Code is invoked with:
    - --print: Output to stdout
    - --output-format json: Request JSON output
    - --allowedTools: Restrict to safe tools

    Uses ThreadPoolExecutor for Windows compatibility.
    """

    def __init__(self, working_dir: Optional[Path] = None):
        self.settings = get_settings()
        self.working_dir = working_dir or Path.cwd()
        self._executor = ThreadPoolExecutor(max_workers=2)

    async def run_mapping(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        timeout: Optional[int] = None,
        on_progress: Optional[Callable[[str], None]] = None
    ) -> dict:
        """
        Execute Claude Code CLI and capture output.

        Args:
            prompt: The full mapping prompt (passed via stdin)
            system_prompt: Optional system prompt
            timeout: Max execution time in seconds (default from settings)
            on_progress: Optional callback for progress updates

        Returns:
            Parsed JSON output from Claude

        Raises:
            ClaudeTimeoutError: If execution exceeds timeout
            ClaudeExecutionError: If Claude returns non-zero exit code
            OutputParsingError: If output cannot be parsed as JSON
        """
        timeout = timeout or self.settings.claude_timeout

        # Build command (prompt passed via stdin, not as argument)
        cmd = self._build_command(system_prompt)

        logger.info(f"Executing Claude Code with timeout={timeout}s")
        logger.debug(f"Command: {' '.join(cmd)}")
        logger.debug(f"Working directory: {self.working_dir}")
        logger.debug(f"Prompt length: {len(prompt)} chars")

        loop = asyncio.get_event_loop()

        try:
            # Run subprocess in thread pool for Windows compatibility
            # Use lambda to pass prompt as stdin input
            stdout, stderr, returncode = await asyncio.wait_for(
                loop.run_in_executor(
                    self._executor,
                    lambda: self._run_subprocess_sync(cmd, timeout, prompt)
                ),
                timeout=timeout + 30  # Extra buffer for executor overhead
            )

        except asyncio.TimeoutError:
            raise ClaudeTimeoutError(f"Claude Code execution timed out after {timeout} seconds")

        except Exception as e:
            error_msg = str(e)
            if "FileNotFoundError" in error_msg or "No such file" in error_msg:
                raise ClaudeExecutionError(
                    "Claude Code CLI not found. Please ensure 'claude' is installed and in PATH."
                )
            raise ClaudeExecutionError(f"Failed to execute Claude Code: {error_msg}")

        # Check return code
        if returncode != 0:
            logger.error(f"Claude Code failed with code {returncode}")
            logger.error(f"STDERR: {stderr if stderr else '(empty)'}")
            logger.error(f"STDOUT: {stdout[:2000] if stdout else '(empty)'}")
            error_detail = stderr if stderr else stdout[:500] if stdout else "Unknown error"
            raise ClaudeExecutionError(f"Claude Code failed: {error_detail}")

        logger.debug(f"Claude output length: {len(stdout)} chars")
        logger.debug(f"Claude stderr: {stderr[:500] if stderr else 'empty'}")

        return self._extract_json(stdout)

    def _run_subprocess_sync(self, cmd: list, timeout: int, input_text: str = None) -> Tuple[str, str, int]:
        """
        Run subprocess synchronously (called from thread pool).

        Args:
            cmd: Command list to execute
            timeout: Timeout in seconds
            input_text: Text to pass via stdin (the prompt)

        Returns:
            Tuple of (stdout, stderr, returncode)

        Raises:
            TimeoutError: If subprocess times out
            Exception: For other subprocess errors
        """
        try:
            logger.debug(f"Starting subprocess with shell=True on Windows")

            # On Windows, we need shell=True to find 'claude' in PATH
            # Join the command into a string for shell execution
            if isinstance(cmd, list):
                # Properly escape arguments for shell
                cmd_str = subprocess.list2cmdline(cmd)
            else:
                cmd_str = cmd

            result = subprocess.run(
                cmd_str,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.working_dir),
                shell=True,
                input=input_text,  # Pass prompt via stdin
                encoding='utf-8',
                errors='replace'
            )

            return result.stdout, result.stderr, result.returncode

        except subprocess.TimeoutExpired as e:
            logger.error(f"Subprocess timed out after {timeout}s")
            raise TimeoutError(f"Subprocess timed out after {timeout}s")

        except FileNotFoundError as e:
            logger.error(f"Claude CLI not found: {e}")
            raise

        except Exception as e:
            logger.error(f"Subprocess error: {e}")
            raise

    def _build_command(self, system_prompt: Optional[str] = None) -> list:
        """Build the Claude CLI command (prompt passed via stdin)."""
        cmd = ["claude", "--print", "--output-format", "json"]

        # Add allowed tools
        cmd.extend(["--allowedTools", self.settings.claude_allowed_tools])

        # Add system prompt if provided
        if system_prompt:
            cmd.extend(["--system-prompt", system_prompt])

        # Prompt will be passed via stdin, not as argument
        return cmd

    def _extract_json(self, output: str) -> dict:
        """Extract JSON from Claude's output."""
        if not output or not output.strip():
            raise OutputParsingError("Claude returned empty output")

        # First, try parsing entire output as JSON (Claude CLI wrapper format)
        try:
            wrapper = json.loads(output)

            # Check if this is Claude CLI wrapper format
            if isinstance(wrapper, dict) and wrapper.get("type") == "result":
                result_content = wrapper.get("result", "")

                # Check for error
                if wrapper.get("is_error"):
                    raise ClaudeExecutionError(f"Claude returned error: {result_content}")

                # The result might be a JSON string or already parsed
                if isinstance(result_content, dict):
                    return result_content
                elif isinstance(result_content, str):
                    # Try to parse the result string as JSON
                    try:
                        return json.loads(result_content)
                    except json.JSONDecodeError:
                        # Result might contain JSON embedded in text
                        return self._find_json_in_text(result_content)

            # If it's already the mapping format, return it
            if isinstance(wrapper, dict) and "Framework" in wrapper:
                return wrapper

            return wrapper
        except json.JSONDecodeError:
            pass

        # Fallback: try to find JSON in raw text
        return self._find_json_in_text(output)

    def _find_json_in_text(self, text: str) -> dict:
        """Find and extract JSON object from text."""
        # Try regex patterns for JSON blocks
        json_patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'(\{[\s\S]*"Framework"[\s\S]*"Requirements"[\s\S]*\})',
            r'(\{[\s\S]*\})',
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    cleaned = match.strip()
                    if cleaned.startswith('{'):
                        parsed = json.loads(cleaned)
                        if isinstance(parsed, dict):
                            return parsed
                except json.JSONDecodeError:
                    continue

        # Try finding largest {...} block
        depth = 0
        start = -1
        for i, char in enumerate(text):
            if char == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0 and start != -1:
                    try:
                        return json.loads(text[start:i+1])
                    except json.JSONDecodeError:
                        start = -1

        raise OutputParsingError(
            f"Could not extract valid JSON from Claude output. "
            f"Output preview: {text[:500]}..."
        )

    async def health_check(self) -> bool:
        """
        Check if Claude Code CLI is available and working.

        Returns:
            True if Claude is available, False otherwise
        """
        try:
            loop = asyncio.get_event_loop()

            def check_version():
                result = subprocess.run(
                    "claude --version",
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=True
                )
                return result.returncode == 0

            return await asyncio.wait_for(
                loop.run_in_executor(self._executor, check_version),
                timeout=15
            )
        except Exception as e:
            logger.warning(f"Claude health check failed: {e}")
            return False

    def __del__(self):
        """Cleanup thread pool on deletion."""
        try:
            self._executor.shutdown(wait=False)
        except Exception:
            pass


# Singleton instance
_runner: Optional[ClaudeCodeRunner] = None


def get_claude_runner() -> ClaudeCodeRunner:
    """Get the singleton Claude runner instance."""
    global _runner
    if _runner is None:
        _runner = ClaudeCodeRunner()
    return _runner
