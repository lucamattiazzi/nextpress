import json

import pytest

from nextpress.entities import Response


class TestResponse:
    def test_response_initialization(self):
        async def mock_send(data):
            pass

        response = Response(asgi_send=mock_send)

        assert response.asgi_send == mock_send
        assert response.body is None
        assert response.local_state == {}
        assert response._status_code == 200
        assert response._headers_sent is False
        assert response._response_closed is False
        assert response._is_chunked is False

    def test_set_header(self):
        async def mock_send(data):
            pass

        response = Response(asgi_send=mock_send)
        response.set_header("Content-Type", "application/json")
        response.set_header("X-Custom", "value")

        assert len(response._headers_buffer) == 2
        assert response._headers_buffer[0] == (b"Content-Type", b"application/json")
        assert response._headers_buffer[1] == (b"X-Custom", b"value")

    def test_set_header_after_headers_sent_raises_error(self):
        async def mock_send(data):
            pass

        response = Response(asgi_send=mock_send)
        response._headers_sent = True

        with pytest.raises(RuntimeError, match="Headers already sent"):
            response.set_header("Content-Type", "text/plain")

    def test_set_status_code(self):
        async def mock_send(data):
            pass

        response = Response(asgi_send=mock_send)
        response.set_status_code(404)

        assert response._status_code == 404

    def test_set_status_code_after_headers_sent_raises_error(self):
        async def mock_send(data):
            pass

        response = Response(asgi_send=mock_send)
        response._headers_sent = True

        with pytest.raises(RuntimeError, match="Headers already sent"):
            response.set_status_code(500)

    @pytest.mark.asyncio
    async def test_send_text(self):
        sent_data = []

        async def mock_send(data):
            sent_data.append(data)

        response = Response(asgi_send=mock_send)
        await response.send_text("Hello, World!")

        assert len(sent_data) == 3
        # Headers
        assert sent_data[0]["type"] == "http.response.start"
        assert sent_data[0]["status"] == 200
        headers_dict = dict(sent_data[0]["headers"])
        assert headers_dict[b"Content-Type"] == b"text/plain; charset=utf-8"
        assert headers_dict[b"Content-Length"] == b"13"
        # Body
        assert sent_data[1]["type"] == "http.response.body"
        assert sent_data[1]["body"] == b"Hello, World!"
        assert sent_data[1]["more_body"] is True
        # End
        assert sent_data[2]["more_body"] is False

    @pytest.mark.asyncio
    async def test_send_json(self):
        sent_data = []

        async def mock_send(data):
            sent_data.append(data)

        response = Response(asgi_send=mock_send)
        await response.send_json({"message": "test", "count": 42})

        assert len(sent_data) == 3
        # Headers
        assert sent_data[0]["status"] == 200
        headers_dict = dict(sent_data[0]["headers"])
        assert headers_dict[b"Content-Type"] == b"application/json; charset=utf-8"
        # Body
        body_json = json.loads(sent_data[1]["body"].decode("utf-8"))
        assert body_json == {"message": "test", "count": 42}

    @pytest.mark.asyncio
    async def test_send_bytes(self):
        sent_data = []

        async def mock_send(data):
            sent_data.append(data)

        response = Response(asgi_send=mock_send)
        await response.send_bytes(b"\x00\x01\x02")

        assert len(sent_data) == 3
        headers_dict = dict(sent_data[0]["headers"])
        assert headers_dict[b"Content-Type"] == b"application/octet-stream"
        assert sent_data[1]["body"] == b"\x00\x01\x02"

    @pytest.mark.asyncio
    async def test_send_text_with_custom_status_and_headers(self):
        sent_data = []

        async def mock_send(data):
            sent_data.append(data)

        response = Response(asgi_send=mock_send)
        response.set_status_code(201)
        response.set_header("X-Custom", "test")
        await response.send_text("Created")

        assert sent_data[0]["status"] == 201
        headers_dict = dict(sent_data[0]["headers"])
        assert b"X-Custom" in headers_dict
        assert headers_dict[b"X-Custom"] == b"test"

    @pytest.mark.asyncio
    async def test_write_chunked(self):
        sent_data = []

        async def mock_send(data):
            sent_data.append(data)

        response = Response(asgi_send=mock_send)
        await response.write("chunk1")
        await response.write("chunk2")
        await response.end()

        # Headers with Transfer-Encoding: chunked
        assert sent_data[0]["type"] == "http.response.start"
        headers_dict = dict(sent_data[0]["headers"])
        assert headers_dict[b"Transfer-Encoding"] == b"chunked"

        # Multiple body chunks
        assert sent_data[1]["body"] == b"chunk1"
        assert sent_data[1]["more_body"] is True
        assert sent_data[2]["body"] == b"chunk2"
        assert sent_data[2]["more_body"] is True

    @pytest.mark.asyncio
    async def test_end_without_content(self):
        sent_data = []

        async def mock_send(data):
            sent_data.append(data)

        response = Response(asgi_send=mock_send)
        await response.end()

        assert sent_data[0]["type"] == "http.response.start"
        assert sent_data[1]["type"] == "http.response.body"
        assert sent_data[1]["body"] == b""
        assert sent_data[1]["more_body"] is False
        assert response._response_closed is True

    @pytest.mark.asyncio
    async def test_end_with_content(self):
        sent_data = []

        async def mock_send(data):
            sent_data.append(data)

        response = Response(asgi_send=mock_send)
        await response.end("final content")

        assert sent_data[1]["body"] == b"final content"

    @pytest.mark.asyncio
    async def test_end_idempotent(self):
        sent_data = []

        async def mock_send(data):
            sent_data.append(data)

        response = Response(asgi_send=mock_send)
        await response.end()
        initial_count = len(sent_data)

        # Calling end again should not send more data
        await response.end()
        assert len(sent_data) == initial_count

    @pytest.mark.asyncio
    async def test_headers_not_sent_twice(self):
        sent_data = []

        async def mock_send(data):
            sent_data.append(data)

        response = Response(asgi_send=mock_send)
        await response._send_headers()
        await response._send_headers()

        # Should only have one header message
        header_messages = [d for d in sent_data if d["type"] == "http.response.start"]
        assert len(header_messages) == 1

    def test_response_with_generic_type(self):
        class ResponseData:
            message: str

        async def mock_send(data):
            pass

        response = Response[ResponseData](asgi_send=mock_send)
        assert response.body is None

    def test_local_state(self):
        async def mock_send(data):
            pass

        response = Response(asgi_send=mock_send)
        response.local_state["user_id"] = 123
        response.local_state["authenticated"] = True

        assert response.local_state["user_id"] == 123
        assert response.local_state["authenticated"] is True
