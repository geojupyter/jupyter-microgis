import re

import ipykernel


def get_kernel_id() -> str:
    try:
        file = ipykernel.connect.get_connection_file()
    except Exception as e:
        raise RuntimeError(
            f"Failed to get kernel connection file ({e})."
            "Are you sure this code is running in a kernel?",
        ) from e

    match = re.search("kernel-(.*).json", file)

    if not match:
        raise RuntimeError(f"Failed to parse kernel ID from filename: {file}")

    return match.group(1)
