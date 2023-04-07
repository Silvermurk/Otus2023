# -*- coding: utf-8 -*-
import logging
import pathlib
import re
import socket
import multiprocessing
from http.client import HTTPConnection

import pytest

from dz4.HttpServer import httpd


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as _socket:
        _socket.bind(("", 0))
        _socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return _socket.getsockname()[1]


class TestHttpServer:
    host = 'localhost'
    document_root = PATH = pathlib.Path(__file__).parent
    n_workers = 4

    @pytest.fixture(autouse=True)
    def setup(self):
        # pylint:disable=attribute-defined-outside-init
        logger = logging.getLogger()
        logger.disabled = True

        self.port = find_free_port()
        self.server = multiprocessing.Process(
            target=httpd.serve_forever,
            args=(self.host,
                  self.port,
                  self.document_root,
                  self.n_workers))
        self.server.daemon = True
        self.server.start()
        self.conn = HTTPConnection(self.host, self.port, timeout=10)

    def teardown(self):
        self.conn.close()
        self.server.terminate()

    def test_empty_request(self):
        """
        Send empty request
        """
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.connect((self.host, self.port))
        _socket.sendall(b"\n")
        _socket.close()

    def test_server_header(self):
        """
        Server handler test
        """
        self.conn.request("GET", "/httptest/")
        result = self.conn.getresponse()
        result.read()
        server = result.getheader("Server")
        assert server is not None

    def test_directory_index(self):
        """
        Directory index test
        """
        self.conn.request("GET", "/httptest/folder/")
        result = self.conn.getresponse()
        data = result.read()
        length = result.getheader("Content-Length")
        assert result.status == 200
        assert length == '29'
        assert len(data) == 29
        assert data == b"<html>Test index file</html>\n"

    def test_index_not_found(self):
        """
        Directory index file not present test
        """
        self.conn.request("GET", "/httptest/no_index_folder/")
        result = self.conn.getresponse()
        result.read()
        assert result.status == 404

    def test_file_not_found(self):
        """
        Absent file should return 404 test
        """
        self.conn.request("GET", "/httptest/no_such_file.html")
        result = self.conn.getresponse()
        result.read()
        assert result.status == 404

    def test_file_in_nested_folders(self):
        """
        Test nested folder get test
        """
        self.conn.request("GET", "/httptest/deep_1/deep_2/deep_3/bottom.txt")
        result = self.conn.getresponse()
        data = result.read()
        length = result.getheader("Content-Length")
        assert result.status == 200
        assert length == '23'
        assert len(data) == 23
        assert data == b"You are very very deep\n"

    def test_file_with_trailing_slash(self):
        """
        Bad file path with extra slash
        """
        self.conn.request("GET", "/httptest/folder/page.html/")
        result = self.conn.getresponse()
        result.read()
        assert result.status == 404

    def test_file_with_query_string(self):
        """
        Query string after file name test
        """
        self.conn.request(
            "GET", "/httptest/folder/page.html?arg1=SomeValue&arg2=ValueSome")
        result = self.conn.getresponse()
        data = result.read()
        length = result.getheader("Content-Length")
        assert result.status == 200
        assert length == '52'
        assert len(data) == 52
        assert data == b"<html><body>Some sample html page ^_^</body></html>\n"

    def test_file_with_spaces(self):
        """
        File with spaces in name test
        """
        self.conn.request("GET", "/httptest/file%20with%20spaces.txt")
        result = self.conn.getresponse()
        data = result.read()
        length = result.getheader("Content-Length")
        assert result.status == 200
        assert length == '10'
        assert len(data) == 10
        assert data == b"Some Text\n"

    def test_file_urlencoded(self):
        """
        Url encoded test
        """
        self.conn.request("GET", "/httptest/folder/%70%61%67%65%2e%68%74%6d%6c")
        result = self.conn.getresponse()
        data = result.read()
        length = result.getheader("Content-Length")
        assert result.status == 200
        assert length == '52'
        assert len(data) == 52
        assert data == b"<html><body>Some sample html page ^_^</body></html>\n"

    def test_large_file(self):
        """
        Large file downloaded correctly
        """
        self.conn.request("GET", "/httptest/wikipedia_russia.html")
        result = self.conn.getresponse()
        data = result.read()
        length = result.getheader("Content-Length")
        assert result.status == 200
        assert length == '954824'
        assert len(data) == 954824
        assert b"Wikimedia Foundation, Inc." in data

    def test_document_root_escaping(self):
        """
        Document root escaping forbidden
        """
        self.conn.request(
            "GET",
            "/httptest/../../../../../../../../../../../../../etc/passwd",
            )
        result = self.conn.getresponse()
        result.read()
        assert result.status in (400, 403, 404)

    def test_file_with_dot_in_name(self):
        """
        File with two dots in name
        """
        self.conn.request("GET", "/httptest/text..txt")
        result = self.conn.getresponse()
        data = result.read()
        length = result.getheader("Content-Length")
        assert result.status == 200
        assert b"hello" in data
        assert length == '5'

    def test_post_method(self):
        """
        Post method forbidden
        """
        self.conn.request("POST", "/httptest/folder/page.html")
        result = self.conn.getresponse()
        result.read()
        assert result.status in (400, 405)

    def test_head_method(self):
        """
        Head method support
        """
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.connect((self.host, self.port))
        _socket.send(b"HEAD /httptest/folder/page.html HTTP/1.0\r\n\r\n")
        data = bytearray()
        while 1:
            buf = _socket.recv(1024)
            if not buf:
                break
            data += buf
        _socket.close()

        data = data.decode("utf-8")
        assert data.find("\r\n\r\n") > 0, "no empty line with CRLF found"
        (head, body) = re.split("\r\n\r\n", data, 1)
        headers = head.split("\r\n")
        assert len(headers) > 0, "no headers found"
        status_line = headers.pop(0)
        (proto, code, status) = status_line.split(" ")
        header = {}
        for _key, _value in enumerate(headers):
            (name, value) = re.split(r"\s*:\s*", _value, 1)
            header[name] = value
        if int(code) == 200:
            assert int(header["Content-Length"]) == 52
            assert len(body) == 0
        else:
            assert code in (400, 405)

    def test_filetype_html(self):
        """
        Content-Type for .html
        """
        self.conn.request("GET", "/httptest/folder/page.html")
        result = self.conn.getresponse()
        data = result.read()
        length = result.getheader("Content-Length")
        c_type = result.getheader("Content-Type")
        assert result.status == 200
        assert length == '52'
        assert len(data) == 52
        assert c_type == "text/html"

    def test_filetype_css(self):
        """Content-Type for .css
        """
        self.conn.request("GET", "/httptest/splash.css")
        result = self.conn.getresponse()
        data = result.read()
        length = result.getheader("Content-Length")
        c_type = result.getheader("Content-Type")
        assert result.status == 200
        assert length == '98620'
        assert len(data) == 98620
        assert c_type == "text/css"

    def test_filetype_js(self):
        """Content-Type for .js
        """
        self.conn.request("GET", "/httptest/jquery-1.9.1.js")
        result = self.conn.getresponse()
        data = result.read()
        length = result.getheader("Content-Length")
        c_type = result.getheader("Content-Type")
        assert result.status == 200
        assert length == '268381'
        assert len(data) == 268381
        assert c_type in ("application/x-javascript",
                          "application/javascript",
                          "text/javascript")

    def test_filetype_jpg(self):
        """
        Content-Type for .jpg
        """
        self.conn.request("GET", "/httptest/160313.jpg")
        result = self.conn.getresponse()
        data = result.read()
        length = result.getheader("Content-Length")
        c_type = result.getheader("Content-Type")
        assert result.status == 200
        assert length == '267037'
        assert len(data) == 267037
        assert c_type == "image/jpeg"

    def test_filetype_jpeg(self):
        """Content-Type for .jpeg
        """
        self.conn.request("GET", "/httptest/ef35c.jpeg")
        result = self.conn.getresponse()
        data = result.read()
        length = result.getheader("Content-Length")
        c_type = result.getheader("Content-Type")
        assert result.status == 200
        assert length == '160462'
        assert len(data) == 160462
        assert c_type == "image/jpeg"

    def test_filetype_png(self):
        """
        Content-Type for .png
        """
        self.conn.request("GET", "/httptest/logo.v2.png")
        result = self.conn.getresponse()
        data = result.read()
        length = result.getheader("Content-Length")
        c_type = result.getheader("Content-Type")
        assert result.status == 200
        assert length == '1754'
        assert len(data) == 1754
        assert c_type == "image/png"

    def test_filetype_gif(self):
        """
        Content-Type for .gif
        """
        self.conn.request("GET", "/httptest/pic_ask.gif")
        result = self.conn.getresponse()
        data = result.read()
        length = result.getheader("Content-Length")
        c_type = result.getheader("Content-Type")
        assert result.status == 200
        assert length == '1747'
        assert len(data) == 1747
        assert c_type == "image/gif"

    def test_filetype_swf(self):
        """
        Content-Type for .swf
        """
        self.conn.request("GET", "/httptest/b16261023.swf")
        result = self.conn.getresponse()
        data = result.read()
        length = result.getheader("Content-Length")
        c_type = result.getheader("Content-Type")
        assert result.status == 200
        assert length == '35344'
        assert len(data) == 35344
        assert c_type == "application/x-shockwave-flash"
