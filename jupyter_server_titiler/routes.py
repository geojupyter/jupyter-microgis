import httpx

from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
import tornado

from jupyter_server_titiler.constants import (
    ENDPOINT_BASE,
    SERVER_EXTENSION_NAME,
)
from jupyter_server_titiler.api import TiTilerServer


class TiTilerRouteHandler(APIHandler):
    """How does this handler work?"""

    @tornado.web.authenticated
    async def get(self, path: str):
        if not path:
            self.finish(
                f"This is the root endpoint of the '{SERVER_EXTENSION_NAME}'"
                " server extension",
                set_content_type="text/plain; charset=UTF-8",
            )
            return

        params = {key: val[0].decode() for key, val in self.request.arguments.items()}

        server = TiTilerServer()
        await server.start_tile_server()
        get_url = f"{server._tile_server_url}/{path}"

        async with httpx.AsyncClient() as client:
            r = await client.get(get_url, params=params)

            self.write(r.content)


def setup_routes(web_app):
    host_pattern = ".*$"

    base_url = web_app.settings["base_url"]

    titiler_route_pattern = url_path_join(base_url, ENDPOINT_BASE, "(.*)")

    routes = [(titiler_route_pattern, TiTilerRouteHandler)]
    web_app.add_handlers(host_pattern, routes)
