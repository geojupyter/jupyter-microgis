# Routes

It's **very important** to understand that the routing behavior runs in a separate
Python process from the actual TiTiler _server_, which runs in a kernel.

**This directory contains all the router-side things.**
It should stand on its own and not rely on state of any names outside this directory.
In particular, don't instantiate a `TiTilerServer` in any modules in this directory.
That happens in the kernel **only**.

Because the `TiTilerServer` is running in a kernel alongside the data, the data doesn't
need to be serialized to be sent from the kernel to the TiTiler server.
As a consequence of this architecture we may have multiple TiTiler servers running if
the user is working in multiple Notebooks simultaneously!


## This means the router has no idea about what TiTiler servers are running and on what ports

We need to solve for this.


### Passing the server URL/port as query parameters?

One option to solve this is for the consumer (e.g. ipyleaflet) to send a `server_url` or
`server_port` as a URL query parameter along with each request.

```
/titiler/<uuid>/<etc.>/?server_port=43212&<etc.>
```

The only downside of this that I can see is that the reason we're doing this might not
be clear to developers.
I know it wasn't immediately clear to me when reading the code of `jupytergis-tiler`,
which this extension is based on.


### Keep a registry of running servers?

Another option is for the router to keep a registry of running servers, and route to the
correct server depending on the requested dataset.

A major downside of this approach is that the registry would grow forever unless we
write code to somehow clean it up.
How would we know when registry entries need to be cleaned up?


### Why do we need a router at all?

Why can't we directly hit the server from the consumer in the Notebook?
E.g. ipyleaflet would add a layer hosted at `localhost:43212/<uuid>/<etc.>`?

**Because the JupyterLab might not be running on `localhost`, and the client/consumer
(e.g. `leaflet.js`) will likely be running in the user's browser.
The TiTiler server doesn't exist on `localhost` if JupyterLab isn't running on
`localhost`.**
