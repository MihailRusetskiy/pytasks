import asyncio
import logging
from pprint import pprint
from service.headers import Headers
from json import dumps, loads
from service.job import Job, JobExecutor
from service.server.filters import AuthFilter
import random, string


_LOGGER = logging.getLogger(__name__)

REQUEST_METHODS = frozenset(
    {"GET", "POST", "PUT", "DELETE"}
)


#======================================#
# HTTP Response and Request Structures #
#======================================#

class Request:
    """Structure used to store server requests."""

    __slots__ = ("method", "path", "query", "headers")

    def __init__(self, method="GET", path="/", query=None, headers=None):
        self.method = method
        self.path = path
        self.query = query or {}
        self.headers = headers or Headers()

    def __repr__(self):
        fields = (
            "{0}: {1!r}".format(name, getattr(self, name))
            for name in self.__slots__
        )
        return "".join(("Request(", ", ".join(fields), ")"))


class Response:
    """Structure used to store server responses."""

    __slots__ = ("status", "headers")

    def __init__(self, status, headers=None):
        self.status = status
        self.headers = Headers()
        self.headers.update(headers)

    def __repr__(self):
        fields = (
            "{0}: {1!r}".format(name, getattr(self, name))
            for name in self.__slots__
        )
        return "".join(("Response(", ", ".join(fields), ")"))


#======================================#
# Connection and Protocol base classes #
#======================================#

class ConnectionLogger(logging.LoggerAdapter):
    """A logging adapter used to log message associated with connection
    peername.
    """
    def __init__(self, logger, peername):
        super().__init__(logger, {"peername": peername})

    def process(self, msg, kwargs):
        tmp = "@{0[0]}:{0[1]}\n{1}".format(self.extra["peername"], msg)
        return tmp, kwargs


class Connection:
    """Interface for connections initiated in ``Server``.

    Attributes:
    :server: The server that have created this connection.
    :reader: The sream for reading data from the remote client.
    :writer: The stream for sending data to the remote client.
    :peername: A (host, port) tuple associated to the client, as returned
        by ``Socket.getpeername``.
    """

    def __init__(self, server, reader, writer, peername, logger=_LOGGER):
        """Initialize the connection."""
        self._server = server
        self._reader = reader
        self._writer = writer
        self._peername = peername
        self._logger = ConnectionLogger(logger, self.peername)

    @property
    def server(self):
        return self._server

    @property
    def reader(self):
        return self._reader

    @property
    def writer(self):
        return self._writer

    @property
    def peername(self):
        return self._peername

    @property
    def logger(self):
        return self._logger

    @property
    def _loop(self):
        """Shortcut property that returns server's loop."""
        return self._server._loop

    async def listen(self):
        """ This method is executed when the client connects to the
        server and returns when the connection should be closed.
        """
        raise NotImplementedError

    def close(self):
        """Close the connection."""
        if not self.writer.is_closing():
            self.writer.close()


class ProtocolHandler:
    """This class defines the layer between ``RequestHandler`` and
    ``Connection``. It will handle the reception of the request, the
    delegation to a request handler, receiving the payload of the
    request and sending the response.

    Attributes:
    :connection: The connection that created this transport.
    :request: The current request.
    :body_reader: The current body reader, used to read the request
        payload.
    :handler: The current handler, chosen from the current request.
    :response: The response sent, may be sent by the handler, or an
        error sent by the transport.
    :error: The current HTTP error, is None if there is no error.
    """

    def __init__(self, connection):
        """Initialize the transport."""
        self._connection = connection

        self._request = None
        self._body_reader = None
        self._handler = None
        self._response = None
        self._error = None

    @property
    def request(self):
        return self._request

    @property
    def context(self):
        return self._server.context

    @property
    def body_reader(self):
        return self._body_reader

    @property
    def handler(self):
        return self._handler

    @property
    def response(self):
        return self._response

    @property
    def error(self):
        return self._error

    #------------------------------------#
    # Shortcuts to connection attributes #
    #------------------------------------#

    @property
    def _loop(self):
        return self._connection._loop

    @property
    def _server(self):
        return self._connection._server

    @property
    def _logger(self):
        return self._connection._logger

    @property
    def _reader(self):
        return self._connection._reader

    @property
    def _writer(self):
        return self._connection._writer

    @property
    def _peername(self):
        return self._connection._peername

    #------------------#
    # Abstract methods #
    #------------------#

    async def send_response(self, status, headers=None, body=None):
        """Send an HTTP response to the remote client.

        Arguments:
        :status: The HTTP status of the response.
        :headers: A collection of header fields sent in the response.
        :body: the response payload body.
        """
        raise NotImplementedError

    async def send_error(self, code, headers=None, **kwargs):
        """Shortcut used to send HTTP errors to the client."""
        assert 400 <= code < 600
        await self.send_response(code, headers)

    async def process_request(self):
        """Process a single request, then returns."""
        raise NotImplementedError


#=================#
# Request handler #
#=================#

class MetaRequestHandler(type):
    """
    Metaclass for all user-defined request handlers.

    Populate the methods attribute of the request handler in order to
    easily acces to handler's allowed methods.
    """
    def __init__(cls, name, bases, namespace):
        methods = set()

        for method in REQUEST_METHODS:
            method_handler = getattr(cls, method.lower(), None)
            if method_handler and asyncio.iscoroutinefunction(method_handler):
                methods.add(method.lower())

        cls.methods = frozenset(methods)


class RequestHandler(AuthFilter):
    """Base class for all user defined request handlers.

    Each method defined in a sublass of this class that have the same
    name as an HTTP method will be called to handle this HTTP method.
    """

    @classmethod
    def allowed_methods(cls):
        return frozenset(
            method for method in REQUEST_METHODS
            if hasattr(cls, method.lower())
        )

    def __init__(self, protocol):
        self._protocol = protocol
        self.request = protocol.request
        self.body_reader = protocol.body_reader
        self.context = protocol.context

    def send_response(self, status, headers=None, body=None):
        """A shortcut to the protocol ``send_response`` method."""
        assert self.request is self._protocol.request

        if isinstance(body, str):
            body = body.encode("utf-8")

        return self._protocol.send_response(status, headers, body)

    def send_error(self, status, headers=None, **kwargs):
        """A shortcut to the protocol ``send_response`` method."""
        assert self.request is self._protocol.request
        return self._protocol.send_error(status, headers, **kwargs)


def fill_context(context):
    job = {'job_id': 1, 'command': 'ifconfig', 'created': '2016-08-09T18:31:42.201'}
    job1 = {'job_id': 1, 'command': 'ping', 'created': '2016-08-09T18:31:42.202'}
    jobs = []
    jobs.append(job)
    jobs.append(job1)
    context['jobs'] = jobs

    status = {'status_id': 1, 'done': False}
    statuses = []
    statuses.append(status)
    context['statuses'] = statuses

    result = {
          "result_id": 1,
          "duration": 0.3345,
          "competed": "2016-08-19T15:31:42.201",
          "stdout": "",
          "stderr": "cp: cannot stat ‘/tmp/file’: No such file or directory",
          "exit_code": 1
        }
    results = []
    results.append(result)
    context['results'] = results
    return context


class JobsRequestHandler(RequestHandler):
    async def get(self):
        segment = self.request.path.split('/')[-1]
        if segment.isdigit():             #if have id
            job = Job.get_job(self.context, int(segment))
            if job:
                self.send_response(200, Headers(content_type="application/json"), dumps(job))
            else: await self.send_error(404, Headers(content_type="application/json"))
        if 'query' in self.request.query: #if have search query
            jobs = Job.search_job_by_command(self.context, self.request.query['query'])
            self.send_response(200, Headers(content_type="application/json"), dumps(jobs))
        else:                             #return all records
            await self.send_response(200, Headers(content_type="application/json"), dumps(Job.get_jobs(self.context)))

    async def post(self):
        if 'application/json' in self.request.headers.get('content-type', None):
            data = loads(self.body_reader._reader._buffer.decode('utf-8'))
            if 'command' in data:
                self.context = Job.add_job(self.context, data['command'])
        else: await self.send_error(406, Headers(content_type="application/json"))

    async def delete(self):
        if 'application/json' in self.request.headers.get('content-type', None):
            data = loads(self.body_reader._reader._buffer.decode('utf-8'))
            res = Job.remove_job(self.context, int(data.get('job_id', 0)))
            if res:
                self.context = res
                await self.send_response(200, Headers(content_type="application/json"),\
                                             dumps('Deleted: /api/jobs/' + data.get('job_id', 0)))
            else: await self.send_error(404, Headers(content_type="application/json"))
        else: await self.send_error(406, Headers(content_type="application/json"))


class StatusRequestHandler(RequestHandler):
    async def get(self):
        segment = self.request.path.split('/')[-1]
        if segment.isdigit():  # if have id
            job_status = Job.get_job_status(self.context, int(segment))
            if job_status:
                if not 'Location' in job_status:
                    JobExecutor.do_job(self.context, job_status)
                    await self.send_response(200, Headers(content_type="application/json"), dumps(job_status))
                else: await self.send_response(303, Headers(content_type="application/json"), dumps(job_status))
            else:
                await self.send_error(404, Headers(content_type="application/json"))
        else:  # return all records
            await self.send_response(200, Headers(content_type="application/json"),\
                                     dumps(Job.get_job_statuses(self.context)))


class ResultRequestHandler(RequestHandler):
    async def get(self):
        segment = self.request.path.split('/')[-1]
        if segment.isdigit():  # if have id
            job_result = Job.get_job_result(self.context, int(segment))
            if job_result:
                await self.send_response(200, Headers(content_type="application/json"), dumps(job_result))
            else:
                await self.send_error(404, Headers(content_type="application/json"))
        else:  # return all records
            await self.send_response(200, Headers(content_type="application/json"), \
                                     dumps(Job.get_job_results(self.context)))

    async def delete(self):
        if 'application/json' in self.request.headers.get('content-type', None):
            data = loads(self.body_reader._reader._buffer.decode('utf-8'))
            res = Job.remove_job_result(self.context, data.get('result_id', 0))
            if res:
                self.context = res
                await self.send_response(200, Headers(content_type="application/json"),\
                                             dumps('Deleted: /api/results/' + data.get('result_id', 0)))
            else: await self.send_error(400, Headers(content_type="application/json"))
        else: await self.send_error(406, Headers(content_type="application/json"))


class AuthorizeRequestHandler(RequestHandler):
    def do_filter(self):
        return True

    async def post(self):
        if 'application/json' in self.request.headers.get('content-type', None):
            data = loads(self.body_reader._reader._buffer.decode('utf-8'))
            if data.get('username', None) and data.get('password', None):
                token = ''.join(random.choice(string.ascii_lowercase) for i in range(5))
                self.context['authorized_users'].append(token)
                await self.send_response(200, Headers(content_type="application/json"),\
                                         dumps({'auth_token': token}))
            else: await self.send_error(403, Headers(content_type="application/json"))
        else: await self.send_error(406, Headers(content_type="application/json"))
