import asyncio
from service.server import Server
from service.server.handlers import JobsRequestHandler, StatusRequestHandler, ResultRequestHandler,\
    AuthorizeRequestHandler
import socket, ssl

loop = asyncio.get_event_loop()

routes = [
    (r"/api/jobs", JobsRequestHandler),
    (r"/api/statuses", StatusRequestHandler),
    (r"/api/results", ResultRequestHandler),
    (r"/api/get_token", AuthorizeRequestHandler),
]

#ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
#ssl_context.load_cert_chain(certfile="./certs/li-nux_tk.crt", keyfile="./certs/li-nux.tk.key")


server = Server(routes, loop=loop)
loop.run_until_complete(server.listen(port=8000))

try:
      loop.run_forever()
except KeyboardInterrupt:
      pass
except Exception:
      pass

server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
