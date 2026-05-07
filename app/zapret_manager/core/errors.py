
class DedZapretError(Exception):
    """Base exception for all DedZapret Manager errors."""
    pass


class ConfigError(DedZapretError):
    """Exception raised for configuration-related errors."""
    pass


class StateError(DedZapretError):
    """Exception raised for application state-related errors."""
    pass


class SecurityError(DedZapretError):
    """Exception raised for security-related issues."""
    pass


class SafeExtractError(SecurityError):
    """Exception raised for errors during safe archive extraction."""
    pass


class ProcessExecutionError(DedZapretError):
    """Exception raised when a subprocess command fails."""
    def __init__(self, message, returncode=None, stdout=None, stderr=None):
        super().__init__(message)
        self.message = message
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class AdminRequiredError(DedZapretError):
    """Exception raised when an action requires administrator privileges."""
    pass
