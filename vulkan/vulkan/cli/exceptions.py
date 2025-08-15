class VulkanCliException(Exception):
    """Base exception for CLI errors."""


class ComponentNotFoundException(VulkanCliException):
    """Raised when a component is not found."""
