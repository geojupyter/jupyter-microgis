from jupyter_server.serverapp import ServerApp

from jupyter_server_titiler.constants import (
    LAB_EXTENSION_NAME,
    SERVER_EXTENSION_NAME,
)
from jupyter_server_titiler.titiler import TiTilerServer

__all__ = ["TiTilerServer"]

try:
    from jupyter_server_titiler._version import __version__
except ImportError:
    # Fallback when using the package in dev mode without installing
    # in editable mode with pip:
    # <https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs>
    import warnings

    warnings.warn(
        f"Importing '{SERVER_EXTENSION_NAME}' outside a proper installation."
        " It's highly recommended to install the package from a stable release or"
        " in editable mode.",
        stacklevel=2,
    )
    __version__ = "dev"


def _jupyter_labextension_paths() -> list[dict[str, str]]:
    return [
        {
            "src": "labextension",
            "dest": LAB_EXTENSION_NAME,
        },
    ]


def _jupyter_server_extension_points() -> list[dict[str, str]]:
    return [
        {
            "module": SERVER_EXTENSION_NAME,
        },
    ]


def _load_jupyter_server_extension(server_app: ServerApp) -> None:
    """Registers the API routes to receive HTTP requests from the frontend extension.

    Parameters
    ----------
    server_app: Jupyter server application instance

    """
    server_app.log.info(f"Registered '{SERVER_EXTENSION_NAME}' server extension")
