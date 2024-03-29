# -*- coding: utf-8 -*-
"""
Http server method types
"""

import enum

from typing import NamedTuple


class HTTPMethod(enum.Enum):
    """
    Http served methods for this server
    """
    GET = "GET"
    HEAD = "HEAD"

    def __str__(self):
        return self.value


class HTTPStatus(enum.Enum):
    """
    Http status codes
    """
    OK = 200, 'OK'
    BAD_REQUEST = 400, 'Bad Request'
    FORBIDDEN = 403, 'Forbidden'
    NOT_FOUND = 404, 'Not Found'
    METHOD_NOT_ALLOWED = 405, 'Method Not Allowed'
    REQUEST_TIMEOUT = 408, 'Request Timeout'
    ENTITY_TOO_LARGE = 413, 'Entity Too Large'
    UNSUPPORTED_MEDIA_TYPE = 415, 'Unsupported Media Type'
    INTERNAL_SERVER_ERROR = 500, 'Internal Server Error'
    NOT_IMPLEMENTED = 501, 'Not Implemented'
    HTTP_VERSION_NOT_SUPPORTED = 505, 'HTTP Version Not Supported'

    def __str__(self):
        code, message = self.value
        return f'{code} {message}'


class HTTPRequest(NamedTuple):
    """
    Http request model
    """
    method: HTTPMethod
    target: str

    def clean_target(self):
        """
        Cleaning partition method
        """
        return self.target.partition('/')[-1].partition('?')[0]


class HTTPResponse(NamedTuple):
    """
    Http response model
    """
    status: HTTPStatus
    body: bytes
    content_type: str
    content_length: int

    @classmethod
    def error(cls, status: HTTPStatus):
        """
        Error handling method
        """
        body = str(status).encode('utf-8')
        return cls(
            status=status,
            body=body,
            content_type='text/plain',
            content_length=len(body)
            )
