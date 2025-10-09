import pytest

from nextpress.utils.asgi import asgi_send_body, asgi_send_headers


class TestAsgiSendBody:
    @pytest.mark.asyncio
    async def test_send_body_with_string(self):
        sent_data = []

        async def mock_send(data):
            sent_data.append(data)

        await asgi_send_body(mock_send, "Hello", more_body=False)

        assert len(sent_data) == 1
        assert sent_data[0]["type"] == "http.response.body"
        assert sent_data[0]["body"] == b"Hello"
        assert sent_data[0]["more_body"] is False

    @pytest.mark.asyncio
    async def test_send_body_with_bytes(self):
        sent_data = []

        async def mock_send(data):
            sent_data.append(data)

        await asgi_send_body(mock_send, b"Hello", more_body=True)

        assert len(sent_data) == 1
        assert sent_data[0]["type"] == "http.response.body"
        assert sent_data[0]["body"] == b"Hello"
        assert sent_data[0]["more_body"] is True

    @pytest.mark.asyncio
    async def test_send_body_with_empty_string(self):
        sent_data = []

        async def mock_send(data):
            sent_data.append(data)

        await asgi_send_body(mock_send, "", more_body=False)

        assert len(sent_data) == 1
        assert sent_data[0]["body"] == b""


class TestAsgiSendHeaders:
    @pytest.mark.asyncio
    async def test_send_headers_with_status_200(self):
        sent_data = []

        async def mock_send(data):
            sent_data.append(data)

        headers = [(b"Content-Type", b"text/plain"), (b"Content-Length", b"5")]
        await asgi_send_headers(mock_send, 200, headers)

        assert len(sent_data) == 1
        assert sent_data[0]["type"] == "http.response.start"
        assert sent_data[0]["status"] == 200
        assert sent_data[0]["headers"] == headers

    @pytest.mark.asyncio
    async def test_send_headers_with_status_404(self):
        sent_data = []

        async def mock_send(data):
            sent_data.append(data)

        headers = []
        await asgi_send_headers(mock_send, 404, headers)

        assert len(sent_data) == 1
        assert sent_data[0]["status"] == 404
        assert sent_data[0]["headers"] == []

    @pytest.mark.asyncio
    async def test_send_headers_with_multiple_headers(self):
        sent_data = []

        async def mock_send(data):
            sent_data.append(data)

        headers = [
            (b"Content-Type", b"application/json"),
            (b"Content-Length", b"42"),
            (b"X-Custom-Header", b"custom-value"),
        ]
        await asgi_send_headers(mock_send, 201, headers)

        assert sent_data[0]["status"] == 201
        assert len(sent_data[0]["headers"]) == 3
