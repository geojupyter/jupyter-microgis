import httpx
import tornado
from jupyter_server.base.handlers import APIHandler
from jupyter_server.serverapp import ServerWebApplication
from jupyter_server.utils import url_path_join

from jupyter_server_titiler._routes.registry import register_server, registry
from jupyter_server_titiler.constants import ENDPOINT_BASE
from jupyter_server_titiler.server import TiTilerServer


class TiTilerRegistryRouteHandler(APIHandler):
    """Handle displaying and updating the registry of running TiTiler servers.

    There can be 0-1 TiTiler servers per kernel.
    A GET request will return links to the running TiTiler servers by kernel ID.
    A POST request will register a new TiTiler server to a kernel ID.
    """

    @tornado.web.authenticated
    async def get(self) -> None:
        """Return a list of all registered TiTiler servers."""
        servers = [
            {"kernel_id": key, "server_port": value} for key, value in registry.items()
        ]
        # TODO: Return in a more RESTy style with links/refs to the running servers.
        # The end-user doesn't care about the port.
        self.finish({"servers": servers})

    @tornado.web.authenticated
    async def post(self) -> None:
        """Register a kernel's TiTiler server port.

        Expected JSON body:

        ```json
        {
            "kernel_id": "{kernel_id}",
            "server_port": {server_port},
        }
        ```
        """
        data = self.get_json_body()
        if not data:
            raise RuntimeError("Received empty POST body")

        kernel_id = data["kernel_id"]
        server_port = data["server_port"]
        # TODO: Better validation / error handling

        register_server(kernel_id, server_port)

        self.log.debug(
            f"Registered TiTiler server in {kernel_id=} on port {server_port=}",
        )
        self.finish({"status": "registered", "registration": data})


class TiTilerServerProxyRouteHandler(APIHandler):
    """Proxy incoming requests to TiTiler servers.

    Gets the URL of the tile server from the running instance. Forwards the `path` and
    `params` component of the incoming request to the TiTiler server, then returns the
    response from TiTiler.
    """

    @tornado.web.authenticated
    async def get(self, path: str) -> None:
        """Proxy the incoming request to the relevant TiTiler server."""
        params = {key: val[0].decode() for key, val in self.request.arguments.items()}

        server = TiTilerServer()
        await server.start_tile_server()

        get_url = f"{server._tile_server_url}/{path}"  # noqa: SLF001

        # Proxy the incoming request to TiTiler's FastAPI service
        async with httpx.AsyncClient() as client:
            r = await client.get(get_url, params=params)

            content_type = r.headers.get("content-type")
            if content_type:
                self.set_header("Content-Type", content_type)

            self.set_status(r.status_code)
            self.write(r.content)
            await self.flush()


def setup_routes(web_app: ServerWebApplication) -> None:
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]

    titiler_registry_pattern = url_path_join(base_url, ENDPOINT_BASE)
    titiler_registry_pattern2 = url_path_join(base_url, ENDPOINT_BASE, "/")
    titiler_proxy_pattern = url_path_join(base_url, ENDPOINT_BASE, "(.*)")

    routes = [
        (titiler_registry_pattern, TiTilerRegistryRouteHandler),
        (titiler_registry_pattern2, TiTilerRegistryRouteHandler),
        (titiler_proxy_pattern, TiTilerServerProxyRouteHandler),
    ]

    web_app.add_handlers(host_pattern, routes)
