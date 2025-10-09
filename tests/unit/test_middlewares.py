import pytest
import json

from nextpress.types import Request, Response
from nextpress.middlewares import json_body_parser, cors_middleware


class TestJsonBodyParser:
    @pytest.mark.asyncio
    async def test_parses_json_body_for_post(self):
        call_order = []
        body_data = {"name": "Alice", "age": 30}

        async def mock_receive():
            return {
                "body": json.dumps(body_data).encode("utf-8"),
                "more_body": False,
            }

        async def mock_send(data):
            pass

        async def anext():
            call_order.append("next")

        request = Request(method="POST", path="/", receive=mock_receive)
        response = Response(asgi_send=mock_send)

        await json_body_parser(request, response, anext)

        assert request.body == body_data
        assert "next" in call_order

    @pytest.mark.asyncio
    async def test_parses_json_body_for_put(self):
        body_data = {"update": "data"}

        async def mock_receive():
            return {
                "body": json.dumps(body_data).encode("utf-8"),
                "more_body": False,
            }

        async def mock_send(data):
            pass

        async def anext():
            pass

        request = Request(method="PUT", path="/", receive=mock_receive)
        response = Response(asgi_send=mock_send)

        await json_body_parser(request, response, anext)
        assert request.body == body_data

    @pytest.mark.asyncio
    async def test_parses_json_body_for_patch(self):
        body_data = {"patch": "value"}

        async def mock_receive():
            return {
                "body": json.dumps(body_data).encode("utf-8"),
                "more_body": False,
            }

        async def mock_send(data):
            pass

        async def anext():
            pass

        request = Request(method="PATCH", path="/", receive=mock_receive)
        response = Response(asgi_send=mock_send)

        await json_body_parser(request, response, anext)
        assert request.body == body_data

    @pytest.mark.asyncio
    async def test_skips_parsing_for_get_request(self):
        async def mock_receive():
            return {"body": b'{"should": "not parse"}', "more_body": False}

        async def mock_send(data):
            pass

        anext_called = False

        async def anext():
            nonlocal anext_called
            anext_called = True

        request = Request(method="GET", path="/", receive=mock_receive)
        response = Response(asgi_send=mock_send)

        await json_body_parser(request, response, anext)

        assert request.body is None
        assert anext_called is True

    @pytest.mark.asyncio
    async def test_skips_parsing_for_delete_request(self):
        async def mock_receive():
            return {"body": b'{"should": "not parse"}', "more_body": False}

        async def mock_send(data):
            pass

        async def anext():
            pass

        request = Request(method="DELETE", path="/", receive=mock_receive)
        response = Response(asgi_send=mock_send)

        await json_body_parser(request, response, anext)
        assert request.body is None

    @pytest.mark.asyncio
    async def test_handles_empty_body(self):
        async def mock_receive():
            return {"body": b"", "more_body": False}

        async def mock_send(data):
            pass

        anext_called = False

        async def anext():
            nonlocal anext_called
            anext_called = True

        request = Request(method="POST", path="/", receive=mock_receive)
        response = Response(asgi_send=mock_send)

        await json_body_parser(request, response, anext)

        assert request.body is None
        assert anext_called is True

    @pytest.mark.asyncio
    async def test_returns_400_for_invalid_json(self):
        sent_data = []

        async def mock_receive():
            return {"body": b"invalid json {", "more_body": False}

        async def mock_send(data):
            sent_data.append(data)

        async def anext():
            pass

        request = Request(method="POST", path="/", receive=mock_receive)
        response = Response(asgi_send=mock_send)

        await json_body_parser(request, response, anext)

        # Check that status was set to 400
        assert sent_data[0]["status"] == 400
        # Check that error response was sent
        body = json.loads(sent_data[1]["body"].decode("utf-8"))
        assert body == {"error": "Invalid JSON"}

    @pytest.mark.asyncio
    async def test_handles_complex_json(self):
        body_data = {
            "nested": {"key": "value", "array": [1, 2, 3]},
            "boolean": True,
            "null": None,
        }

        async def mock_receive():
            return {
                "body": json.dumps(body_data).encode("utf-8"),
                "more_body": False,
            }

        async def mock_send(data):
            pass

        async def anext():
            pass

        request = Request(method="POST", path="/", receive=mock_receive)
        response = Response(asgi_send=mock_send)

        await json_body_parser(request, response, anext)
        assert request.body == body_data


class TestCorsMiddleware:
    @pytest.mark.asyncio
    async def test_adds_cors_headers(self):
        async def mock_send(data):
            pass

        anext_called = False

        async def anext():
            nonlocal anext_called
            anext_called = True

        request = Request(method="GET", path="/", receive=lambda: None)
        response = Response(asgi_send=mock_send)

        await cors_middleware(request, response, anext)

        headers_dict = dict(response._headers_buffer)
        assert headers_dict[b"Access-Control-Allow-Origin"] == b"*"
        assert (
            headers_dict[b"Access-Control-Allow-Methods"]
            == b"GET, POST, PUT, DELETE, OPTIONS"
        )
        assert (
            headers_dict[b"Access-Control-Allow-Headers"]
            == b"Content-Type, Authorization"
        )
        assert anext_called is True

    @pytest.mark.asyncio
    async def test_handles_options_preflight(self):
        sent_data = []

        async def mock_send(data):
            sent_data.append(data)

        anext_called = False

        async def anext():
            nonlocal anext_called
            anext_called = True

        request = Request(method="OPTIONS", path="/api", receive=lambda: None)
        response = Response(asgi_send=mock_send)

        await cors_middleware(request, response, anext)

        # Should set status to 204
        assert sent_data[0]["status"] == 204

        # Should NOT call anext for OPTIONS
        assert anext_called is False

        # Should still have CORS headers
        headers_dict = dict(response._headers_buffer) if response._headers_buffer else dict(sent_data[0]["headers"])
        assert b"Access-Control-Allow-Origin" in headers_dict

    @pytest.mark.asyncio
    async def test_passes_through_non_options_requests(self):
        async def mock_send(data):
            pass

        methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]

        for method in methods:
            anext_called = False

            async def anext():
                nonlocal anext_called
                anext_called = True

            request = Request(method=method, path="/", receive=lambda: None)
            response = Response(asgi_send=mock_send)

            await cors_middleware(request, response, anext)

            assert anext_called is True, f"anext not called for {method}"

    @pytest.mark.asyncio
    async def test_cors_headers_set_before_handler(self):
        handler_headers = []

        async def mock_send(data):
            pass

        async def anext():
            # Capture headers at the time anext is called
            handler_headers.extend(response._headers_buffer)

        request = Request(method="GET", path="/", receive=lambda: None)
        response = Response(asgi_send=mock_send)

        await cors_middleware(request, response, anext)

        # Verify CORS headers were set before handler ran
        assert len(handler_headers) > 0
        headers_dict = dict(handler_headers)
        assert b"Access-Control-Allow-Origin" in headers_dict
