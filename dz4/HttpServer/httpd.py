import datetime
import logging
import socket
import threading
import time
import urllib.parse
from pathlib import Path
from typing import Tuple

from .types import HTTPMethod, HTTPRequest, HTTPResponse, HTTPStatus

ALLOWED_CONTENT_TYPES = {
    ".html": "text/html",
    ".js": "application/javascript",
    ".css": "text/css",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".swf": "application/x-shockwave-flash",
    ".txt": "text/plain"}
BACKLOG = 10
REQUEST_SOCKET_TIMEOUT = 10
REQUEST_CHUNK_SIZE = 1024
REQUEST_MAX_SIZE = 8 * 1024

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname).1s %(message)s",
    datefmt="%Y.%m.%d %H:%M:%S")


class HTTPException(Exception):
    pass


def receive(conn: socket.socket) -> bytearray:
    """
    Read raw bytes from socket
    """
    conn.settimeout(REQUEST_SOCKET_TIMEOUT)

    try:
        received = bytearray()

        while True:
            if len(received) > REQUEST_MAX_SIZE:
                break

            if b"\r\n\r\n" in received:
                break

            chunk = conn.recv(REQUEST_CHUNK_SIZE)
            if not chunk:
                break

            received += chunk

    except socket.timeout:
        raise HTTPException(HTTPStatus.REQUEST_TIMEOUT)

    return received


def parse_request(received: bytearray) -> HTTPRequest:
    """
    Parse raw bytes received from a client
    """
    raw_request_line, *_ = received.partition(b"\r\n")
    request_line = str(raw_request_line, "iso-8859-1")

    try:
        raw_method, raw_target, version = request_line.split()
    except ValueError:
        raise HTTPException(HTTPStatus.BAD_REQUEST)

    try:
        method = HTTPMethod[raw_method]
    except KeyError:
        raise HTTPException(HTTPStatus.METHOD_NOT_ALLOWED)

    return HTTPRequest(method=method, target=urllib.parse.unquote(raw_target))


def handle_request(request: HTTPRequest,
                   document_root: Path) -> HTTPResponse:
    """
    Base request handler
    """
    method = request.method
    target = request.clean_target()

    path = Path(document_root, target).resolve()

    if path.is_file() and target.endswith("/"):
        return HTTPResponse.error(HTTPStatus.NOT_FOUND)

    if path.is_dir():
        path /= "index.html"

    if document_root not in path.parents:
        return HTTPResponse.error(HTTPStatus.FORBIDDEN)

    if not path.is_file():
        return HTTPResponse.error(HTTPStatus.NOT_FOUND)

    if path.suffix not in ALLOWED_CONTENT_TYPES:
        return HTTPResponse.error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

    stat = path.stat()
    content_length = stat.st_size
    body = b"" if method is HTTPMethod.HEAD else path.read_bytes()

    return HTTPResponse(
        status=HTTPStatus.OK,
        body=body,
        content_type=ALLOWED_CONTENT_TYPES[path.suffix],
        content_length=content_length,
        )


def send_response(conn: socket.socket,
                  response: HTTPResponse) -> None:
    """
    Base http response handler
    """
    now = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

    headers = (
        f"HTTP/1.1 {response.status}",
        f"Date: {now}",
        f"Content-Type: {response.content_type}",
        f"Content-Length: {response.content_length}",
        f"Server: Fancy-Python-HTTP-Server",
        f"Connection: close",
        f"",
        )

    try:
        raw_response: bytes = "\r\n".join(headers).encode("utf-8")
        raw_response += b"\r\n" + response.body
        conn.sendall(raw_response)
    except socket.timeout:
        pass


def send_error(conn: socket.socket,
               status: HTTPStatus) -> None:
    """
    Send bad request with a proper status error code
    """
    response = HTTPResponse.error(status)
    send_response(conn, response)


def handle_client_connection(conn: socket.socket,
                             address: Tuple,
                             document_root: Path) -> None:
    """
    Handle valid client connection
    """
    logging.debug(f'Connected by: {address}')

    with conn:
        try:
            raw_bytes = receive(conn)
            request = parse_request(raw_bytes)
            response = handle_request(request, document_root)
            logging.info(f'{address}: {request.method} {request.target}')
        except HTTPException as exc:
            status = exc.args[0]
            response = HTTPResponse.error(status)
            logging.info(f'{address}: HTTP exception "{response.status}".')
        except Exception:
            logging.exception(f'{address}: Unexpected error')
            status = HTTPStatus.INTERNAL_SERVER_ERROR
            response = HTTPResponse.error(status)

        try:
            send_response(conn, response)
        except Exception:
            logging.exception(f"{address}: Can't send a response")

    logging.debug(f'{address}: connection closed')


def wait_connection(listening_socket: socket.socket,
                    thread_id: int,
                    document_root: Path) -> None:
    """
    Serve connections forever
    """
    logging.debug(f'Worker-{thread_id} has been started')
    while True:
        try:
            conn, address = listening_socket.accept()
            handle_client_connection(conn, address, document_root)
        except Exception as exception:
            logging.exception("Worker %s has crashed with %s",
                              thread_id,
                              exception)
            return None


def serve_forever(address: str,
                  port: int,
                  document_root:
                  Path, n_workers: int) -> None:
    """
    Open listener socket and start new thread
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as _socket:
        _socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            _socket.bind((address, port))
        except PermissionError:
            logging.error('Permission denied: %s:%s',
                          address,
                          port)
            return
        except OSError:
            logging.error('Invalid address / port: %s:%s',
                          address,
                          port)
            return

        _socket.listen(BACKLOG)

        for i in range(1, n_workers + 1):
            thread = threading.Thread(
                target=wait_connection, args=(_socket, i, document_root)
                )
            thread.daemon = True
            thread.start()

        logging.info(
            f'Running on http://%s:%s/ (Press CTRL+C to quit)',
            address,
            port)

        try:
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            logging.info('Server is stopping.')
            return
