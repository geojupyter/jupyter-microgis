import json

from jupyter_server.base.handlers import JupyterHandler 
from jupyter_server.utils import url_path_join
import tornado

from jupyter_server_titiler.constants import ENDPOINT_BASE


class TiTilerRouteHandler(JupyterHandler):
    """How does this handler work?"""

    @tornado.web.authenticated
    async def get(self, path):
        params = {key: val[0].decode() for key, val in self.request.arguments.items()}
        server_url = params.pop("server_url")
        print(path)
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{server_url}/{path}", params=params)
            self.write(r.content)


def setup_routes(web_app):
    host_pattern = ".*$"

    base_url = web_app.settings["base_url"]
    titiler_route_pattern = url_path_join(base_url, ENDPOINT_BASE)
    routes = [(titiler_route_pattern, TiTilerRouteHandler)]
    web_app.add_handlers(host_pattern, routes)
