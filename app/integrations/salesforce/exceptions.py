"""Custom exceptions for Salesforce operations."""


class SalesforceError(Exception):
    """Base exception for Salesforce operations."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class SalesforceRecordNotFound(SalesforceError):
    """Record not found (404)."""

    def __init__(self, object_type: str, record_id: str):
        super().__init__(
            f"{object_type} record not found: {record_id}",
            status_code=404,
        )


class SalesforceValidationError(SalesforceError):
    """Invalid data or malformed request (400)."""

    def __init__(self, message: str, errors: list | None = None):
        self.errors = errors or []
        super().__init__(message, status_code=400)


class SalesforcePermissionError(SalesforceError):
    """Permission denied (403)."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, status_code=403)


class SalesforceSessionExpired(SalesforceError):
    """Session/token expired (401)."""

    def __init__(self, message: str = "Session expired"):
        super().__init__(message, status_code=401)
