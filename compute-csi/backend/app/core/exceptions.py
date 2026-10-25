from __future__ import annotations


class NotFoundError(Exception):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, resource_id: str) -> None:
        self.resource = resource
        self.resource_id = resource_id
        super().__init__(f"{resource} with id '{resource_id}' not found")


class ValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class IntegrationError(Exception):
    """Raised when an external integration call fails."""

    def __init__(self, integration: str, message: str) -> None:
        self.integration = integration
        super().__init__(f"Integration '{integration}' error: {message}")


class WorkflowError(Exception):
    """Raised when a Temporal workflow operation fails."""

    def __init__(self, workflow_id: str, message: str) -> None:
        self.workflow_id = workflow_id
        super().__init__(f"Workflow '{workflow_id}' error: {message}")
