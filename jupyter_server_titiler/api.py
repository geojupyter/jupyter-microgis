import uuid
from asyncio import Event, Lock, Task, create_task
from functools import partial
from typing import Any, Optional, Self
from urllib.parse import urlencode

from anycorn import Config, serve
from anyio import connect_tcp, create_task_group
from fastapi import FastAPI
from fastapi.routing import APIRoute

from xarray import DataArray
from rio_tiler.io.xarray import XarrayReader
from titiler.core.factory import TilerFactory
from titiler.core.algorithm import algorithms as default_algorithms
from titiler.core.algorithm import BaseAlgorithm
from titiler.core.dependencies import DefaultDependency

from jupyter_server_titiler.constants import ENDPOINT_BASE


class TiTilerServer:
    """A singleton class to manage a TiTiler FastAPI server instance.

    Shamelessly stolen from jupytergis-tiler.

    https://github.com/geojupyter/jupytergis-tiler/blob/main/src/jupytergis/tiler/gis_document.py
    """

    _instance: Optional[Self] = None
    _app: FastAPI

    def __new__(cls) -> Self:
        if cls._instance is None:
            print("New TiTilerServer instance created")
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._tile_server_task: Task | None = None
        self._tile_server_started = Event()
        self._tile_server_shutdown = Event()
        self._tile_server_lock = Lock()

    @classmethod
    async def reset(cls) -> None:
        if not cls._instance:
            raise RuntimeError(f"{cls.__name__} not initialized")

        await cls._instance.stop_tile_server()
        if cls._instance._tile_server_task:
            await cls._instance._tile_server_task

        del cls._instance
        cls._instance = None

    @property
    def routes(self) -> list[dict[str, Any]]:
        return [
            {"path": route.path, "name": route.name}
            for route in self._app.router.routes
            if isinstance(route, APIRoute)
        ]

    async def start_tile_server(self) -> None:
        async with self._tile_server_lock:
            if not self._tile_server_started.is_set():
                self._tile_server_task = create_task(self._start_tile_server())
                await self._tile_server_started.wait()

    async def add_data_array(
        self,
        data_array: DataArray,
        name: str,
        colormap_name: str = "viridis",
        rescale: tuple[float, float] | None = None,
        scale: int = 1,
        opacity: float = 1,
        algorithm: BaseAlgorithm | None = None,
        **params,
    ) -> str:
        await self.start_tile_server()

        _params = {
            "scale": str(scale),
            "colormap_name": colormap_name,
            "reproject": "max",
            **params,
        }
        if rescale is not None:
            _params["rescale"] = f"{rescale[0]},{rescale[1]}"
        if algorithm is not None:
            _params["algorithm"] = "algorithm"
        source_id = str(uuid.uuid4())

        self._include_tile_server_router(source_id, data_array, algorithm)

        url = (
            f"/{ENDPOINT_BASE}/{source_id}/tiles/WebMercatorQuad/"
            + "{z}/{x}/{y}.png?"
            + urlencode(_params)
        )
        return url

    async def stop_tile_server(self) -> None:
        async with self._tile_server_lock:
            if self._tile_server_started.is_set():
                self._tile_server_shutdown.set()

    async def _start_tile_server(self) -> None:
        self._app = FastAPI(
            openapi_url="/",
            docs_url=None,
            redoc_url=None,
        )

        config = Config()
        config.bind = "127.0.0.1:0"

        async with create_task_group() as tg:
            binds = await tg.start(
                partial(
                    serve,
                    self._app,  # type: ignore[arg-type]
                    config,
                    shutdown_trigger=self._tile_server_shutdown.wait,  # type: ignore[arg-type]
                    mode="asgi",
                )
            )

            self._tile_server_url = binds[0]

            host, _port = binds[0][len("http://") :].split(":")
            port = int(_port)
            while True:
                try:
                    await connect_tcp(host, port)
                except OSError:
                    pass
                else:
                    self._tile_server_started.set()
                    break

    def _include_tile_server_router(
        self,
        source_id: str,
        data_array: DataArray,
        algorithm: BaseAlgorithm | None = None,
    ) -> None:
        algorithms = default_algorithms
        if algorithm is not None:
            algorithms = default_algorithms.register({"algorithm": algorithm})

        tiler = TilerFactory(
            router_prefix=f"/{source_id}",
            reader=XarrayReader,
            path_dependency=lambda: data_array,
            reader_dependency=DefaultDependency,
            process_dependency=algorithms.dependency,
        )
        self._app.include_router(tiler.router, prefix=f"/{source_id}")


# async def explore(*args: list[DataArray | Dataset]):
async def explore(da: DataArray) -> str:
    """Explore xarray DataArrays and Datasets in a map widget.

    This function must be called with await in a Jupyter notebook:
        await explore(data_array)

    TODO: Support any number of Xarray objects
    """
    titiler_server = TiTilerServer()
    return await titiler_server.add_data_array(da, name="my_da")

    # TODO: Display a widget
    # TODO: What if there are multiple widgets?
    # TODO: Clean up when widgets clean up
