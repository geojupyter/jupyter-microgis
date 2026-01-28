"""Registry for tracking running TiTiler servers running in kernels.

There should be 0 or 1 TiTiler server per kernel.
The registry should be cleaned up as kernels die.
The registry is displayed on the root endpoint of this extension.
"""

from collections.abc import Mapping
from types import MappingProxyType

# Internal mapping between kernel IDs and server ports
_registry: dict[str, int] = {}

# Public immutable view of the kernel -> port mapping
registry: Mapping[str, int] = MappingProxyType(_registry)


def register_server(kernel_id: str, server_port: int) -> None:
    """Register a TiTiler server running in a kernel process."""

    _registry[kernel_id] = server_port


def unregister_server(kernel_id: str) -> None:
    """Remove a kernel from the registry.

    This is called when a kernel shuts down.
    """
    _registry.pop(kernel_id, None)
