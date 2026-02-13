#!/usr/bin/env python3
"""
Error Handling - Robust error handling for production

Features:
- Custom exceptions
- Error recovery strategies
- Retry logic
- User-friendly error messages
"""

import logging
import time
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger('error_handling')


# Custom Exceptions

class WitmindError(Exception):
    """Base exception for Witmind"""
    pass


class AgentError(WitmindError):
    """Agent execution error"""
    pass


class ToolError(WitmindError):
    """Tool execution error"""
    pass


class LLMError(WitmindError):
    """LLM API error"""
    pass


class WorkflowError(WitmindError):
    """Workflow execution error"""
    pass


class ValidationError(WitmindError):
    """Input validation error"""
    pass


# Retry decorator

def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Retry decorator with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay on each retry
        exceptions: Tuple of exceptions to catch

    Usage:
        @retry_on_error(max_retries=3, delay=1.0)
        def unreliable_function():
            # Might fail sometimes
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"Failed after {max_retries + 1} attempts: {e}")
                        raise

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                        f"Retrying in {current_delay}s..."
                    )

                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper
    return decorator


# Error context manager

class ErrorHandler:
    """
    Context manager for handling errors with recovery strategies.

    Usage:
        with ErrorHandler(on_error='retry', max_retries=3) as handler:
            # Risky operation
            result = agent.execute_task(task)
    """

    def __init__(
        self,
        on_error: str = 'raise',  # 'raise', 'log', 'ignore'
        max_retries: int = 0,
        fallback: Optional[Callable] = None
    ):
        self.on_error = on_error
        self.max_retries = max_retries
        self.fallback = fallback
        self.error: Optional[Exception] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return True

        self.error = exc_val

        if self.on_error == 'raise':
            return False  # Re-raise

        elif self.on_error == 'log':
            logger.error(f"Error occurred: {exc_val}", exc_info=True)
            return True  # Suppress

        elif self.on_error == 'ignore':
            return True  # Suppress

        return False


# Error messages

class ErrorMessages:
    """User-friendly error messages"""

    @staticmethod
    def llm_api_error(provider: str, error: str) -> str:
        """LLM API error message"""
        return f"""
❌ LLM API Error ({provider})

Error: {error}

Possible solutions:
1. Check your API key is valid
2. Verify you have credits/quota remaining
3. Check network connection
4. Try again in a few moments

For {provider} status: https://status.{provider}.com
"""

    @staticmethod
    def tool_error(tool_name: str, error: str) -> str:
        """Tool execution error message"""
        return f"""
❌ Tool Error ({tool_name})

Error: {error}

This tool failed to execute. Please check:
1. File paths are correct
2. Permissions are adequate
3. Dependencies are installed
"""

    @staticmethod
    def agent_timeout(agent_id: str, timeout: int) -> str:
        """Agent timeout error message"""
        return f"""
⏱️ Agent Timeout

Agent '{agent_id}' exceeded maximum execution time ({timeout}s).

This might mean:
1. Task is too complex (consider breaking it down)
2. Agent is stuck in a loop
3. Network is slow

Try:
- Simplify the task
- Increase timeout
- Check agent logs for details
"""

    @staticmethod
    def workflow_blocked(stage_id: str, dependencies: list) -> str:
        """Workflow blocked error message"""
        return f"""
🚫 Workflow Blocked

Stage '{stage_id}' cannot run because these stages haven't completed:
{', '.join(dependencies)}

Check why those stages failed or are still running.
"""


# Validation helpers

def validate_task(task: dict) -> None:
    """Validate task structure"""
    required_fields = ['type', 'description']

    for field in required_fields:
        if field not in task:
            raise ValidationError(f"Task missing required field: {field}")

    if not isinstance(task.get('inputs', []), list):
        raise ValidationError("Task 'inputs' must be a list")

    if not isinstance(task.get('expected_outputs', []), list):
        raise ValidationError("Task 'expected_outputs' must be a list")


def validate_file_path(path: str, project_root) -> None:
    """Validate file path is safe"""
    from pathlib import Path

    file_path = Path(path)

    # Check for path traversal
    if '..' in str(file_path):
        raise ValidationError(f"Path traversal not allowed: {path}")

    # Check absolute paths
    if file_path.is_absolute():
        raise ValidationError(f"Absolute paths not allowed: {path}")


# Safe execution wrapper

def safe_execute(func: Callable, *args, **kwargs) -> dict:
    """
    Safely execute a function and return structured result.

    Returns:
        {
            'success': bool,
            'result': Any,
            'error': Optional[str]
        }
    """
    try:
        result = func(*args, **kwargs)
        return {
            'success': True,
            'result': result,
            'error': None
        }

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return {
            'success': False,
            'result': None,
            'error': f"Validation failed: {str(e)}"
        }

    except LLMError as e:
        logger.error(f"LLM error: {e}")
        return {
            'success': False,
            'result': None,
            'error': ErrorMessages.llm_api_error('LLM', str(e))
        }

    except ToolError as e:
        logger.error(f"Tool error: {e}")
        return {
            'success': False,
            'result': None,
            'error': str(e)
        }

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            'success': False,
            'result': None,
            'error': f"Unexpected error: {str(e)}"
        }


# Example usage
if __name__ == '__main__':
    # Example 1: Retry on error
    @retry_on_error(max_retries=3, delay=0.1)
    def flaky_function():
        import random
        if random.random() < 0.7:  # 70% chance of failure
            raise Exception("Random failure!")
        return "Success!"

    try:
        result = flaky_function()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Failed: {e}")

    # Example 2: Error context manager
    with ErrorHandler(on_error='log') as handler:
        raise Exception("This will be logged, not raised")

    print("Continued execution after error")

    # Example 3: Validation
    try:
        validate_task({'description': 'Test'})  # Missing 'type'
    except ValidationError as e:
        print(f"Validation error: {e}")
