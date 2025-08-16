#!/usr/bin/env python3
"""
AI-CRM Exception Hierarchy
Standardized exception handling for the CRM system.
"""

from typing import Any


class CRMError(Exception):
    """Base CRM exception class."""

    def __init__(
        self,
        message: str,
        error_code: str = "CRM_ERROR",
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error_code": self.error_code,
            "error_message": self.message,
            "details": self.details,
        }


class ConfigurationError(CRMError):
    """Configuration-related errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "CONFIGURATION_ERROR", details)


class ValidationError(CRMError):
    """Data validation errors."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if field:
            details["field"] = field
        super().__init__(message, "VALIDATION_ERROR", details)


class APIError(CRMError):
    """YouGile API related errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict[str, Any] | None = None,
    ):
        details = {}
        if status_code:
            details["status_code"] = status_code
        if response_data:
            details["response_data"] = response_data
        super().__init__(message, "API_ERROR", details)


class AuthenticationError(APIError):
    """API authentication errors."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 401)
        self.error_code = "AUTHENTICATION_ERROR"


class AuthorizationError(APIError):
    """API authorization errors."""

    def __init__(self, message: str = "Authorization denied"):
        super().__init__(message, 403)
        self.error_code = "AUTHORIZATION_ERROR"


class ResourceNotFoundError(APIError):
    """Resource not found errors."""

    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} with ID '{resource_id}' not found"
        super().__init__(message, 404)
        self.error_code = "RESOURCE_NOT_FOUND"
        self.details.update(
            {"resource_type": resource_type, "resource_id": resource_id}
        )


class RateLimitError(APIError):
    """API rate limit exceeded errors."""

    def __init__(self, retry_after: int | None = None):
        message = "API rate limit exceeded"
        super().__init__(message, 429)
        self.error_code = "RATE_LIMIT_ERROR"
        if retry_after:
            self.details["retry_after"] = retry_after


class TaskError(CRMError):
    """Task-specific errors."""

    def __init__(
        self,
        message: str,
        task_id: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if task_id:
            details["task_id"] = task_id
        super().__init__(message, "TASK_ERROR", details)


class TaskNotFoundError(TaskError):
    """Task not found error."""

    def __init__(self, task_id: str):
        super().__init__(f"Task '{task_id}' not found", task_id)
        self.error_code = "TASK_NOT_FOUND"


class TaskValidationError(TaskError):
    """Task validation errors."""

    def __init__(
        self,
        message: str,
        task_id: str | None = None,
        validation_errors: dict[str, str] | None = None,
    ):
        details = {}
        if validation_errors:
            details["validation_errors"] = validation_errors
        super().__init__(message, task_id, details)
        self.error_code = "TASK_VALIDATION_ERROR"


class AgentError(CRMError):
    """Agent-related errors."""

    def __init__(
        self,
        message: str,
        agent_name: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if agent_name:
            details["agent_name"] = agent_name
        super().__init__(message, "AGENT_ERROR", details)


class AgentNotFoundError(AgentError):
    """Agent not found error."""

    def __init__(self, agent_name: str):
        super().__init__(f"Agent '{agent_name}' not found", agent_name)
        self.error_code = "AGENT_NOT_FOUND"


class AgentUnavailableError(AgentError):
    """Agent unavailable error."""

    def __init__(self, agent_name: str, reason: str = "Agent is currently unavailable"):
        super().__init__(f"Agent '{agent_name}' is unavailable: {reason}", agent_name)
        self.error_code = "AGENT_UNAVAILABLE"
        self.details["reason"] = reason


class PMGatewayError(CRMError):
    """PM Gateway specific errors."""

    def __init__(
        self,
        message: str,
        analysis_type: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if analysis_type:
            details["analysis_type"] = analysis_type
        super().__init__(message, "PM_GATEWAY_ERROR", details)


class WorkflowError(PMGatewayError):
    """Workflow processing errors."""

    def __init__(self, message: str, workflow_step: str | None = None):
        details = {"workflow_step": workflow_step} if workflow_step else {}
        super().__init__(message, "workflow", details)
        self.error_code = "WORKFLOW_ERROR"


class AnalysisError(PMGatewayError):
    """Task analysis errors."""

    def __init__(self, message: str, task_title: str | None = None):
        details = {"task_title": task_title} if task_title else {}
        super().__init__(message, "analysis", details)
        self.error_code = "ANALYSIS_ERROR"


class NetworkError(CRMError):
    """Network and connectivity errors."""

    def __init__(
        self,
        message: str,
        endpoint: str | None = None,
        timeout: float | None = None,
    ):
        details = {}
        if endpoint:
            details["endpoint"] = endpoint
        if timeout:
            details["timeout"] = timeout
        super().__init__(message, "NETWORK_ERROR", details)


class TimeoutError(NetworkError):
    """Request timeout errors."""

    def __init__(self, endpoint: str, timeout: float):
        message = f"Request to {endpoint} timed out after {timeout} seconds"
        super().__init__(message, endpoint, timeout)
        self.error_code = "TIMEOUT_ERROR"


class RetryableError(CRMError):
    """Errors that can be retried."""

    def __init__(
        self,
        message: str,
        retry_after: float | None = None,
        max_retries: int = 3,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        details.update(
            {"retry_after": retry_after, "max_retries": max_retries, "retryable": True}
        )
        super().__init__(message, "RETRYABLE_ERROR", details)


class NonRetryableError(CRMError):
    """Errors that should not be retried."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        details = details or {}
        details["retryable"] = False
        super().__init__(message, "NON_RETRYABLE_ERROR", details)


# Exception mapping for HTTP status codes
HTTP_STATUS_EXCEPTIONS = {
    400: ValidationError,
    401: AuthenticationError,
    403: AuthorizationError,
    404: ResourceNotFoundError,
    429: RateLimitError,
    500: APIError,
    502: NetworkError,
    503: RetryableError,
    504: TimeoutError,
}


def create_api_exception(
    status_code: int, message: str, response_data: dict[str, Any] | None = None
) -> APIError:
    """Create appropriate exception based on HTTP status code."""
    exception_class = HTTP_STATUS_EXCEPTIONS.get(status_code, APIError)

    if status_code == 404:
        # Try to extract resource info for 404 errors
        resource_type = "resource"
        resource_id = "unknown"
        if response_data and "id" in response_data:
            resource_id = response_data["id"]
        return ResourceNotFoundError(resource_type, resource_id)

    elif status_code == 429:
        # Extract retry-after header for rate limits
        retry_after = None
        if response_data and "retry_after" in response_data:
            retry_after = response_data["retry_after"]
        return RateLimitError(retry_after)

    elif status_code in [500, 502, 503, 504]:
        # Server errors are generally retryable
        return RetryableError(message, details={"status_code": status_code})

    else:
        return exception_class(message, status_code, response_data)


def is_retryable_error(error: Exception) -> bool:
    """Check if an error is retryable."""
    if isinstance(error, RetryableError):
        return True
    elif isinstance(error, NonRetryableError):
        return False
    elif isinstance(error, (NetworkError, TimeoutError, RateLimitError)) or (isinstance(error, APIError) and error.details.get("status_code", 0) >= 500):
        return True
    else:
        return False


def get_retry_delay(error: Exception, attempt: int, base_delay: float = 1.0) -> float:
    """Calculate retry delay for retryable errors."""
    if (isinstance(error, RateLimitError) and "retry_after" in error.details) or (isinstance(error, RetryableError) and error.details.get("retry_after")):
        return float(error.details["retry_after"])
    else:
        # Exponential backoff with jitter
        import random

        delay = base_delay * (2**attempt) + random.uniform(0, 1)
        return min(delay, 60.0)  # Cap at 60 seconds
