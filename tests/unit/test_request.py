import pytest

from nextpress.types import Request


class TestRequest:
    def test_request_initialization(self):
        async def mock_receive():
            return {}

        request = Request(
            method="GET",
            path="/test",
            receive=mock_receive,
            query_params={"key": "value"},
        )

        assert request.method == "GET"
        assert request.path == "/test"
        assert request.receive == mock_receive
        assert request.query_params == {"key": "value"}
        assert request.body is None

    def test_request_with_body(self):
        async def mock_receive():
            return {}

        request = Request(
            method="POST", path="/api", receive=mock_receive, body={"name": "test"}
        )

        assert request.method == "POST"
        assert request.body == {"name": "test"}

    def test_request_defaults(self):
        async def mock_receive():
            return {}

        request = Request(method="GET", path="/", receive=mock_receive)

        assert request.query_params == {}
        assert request.body is None

    @pytest.mark.asyncio
    async def test_get_body_single_chunk(self):
        async def mock_receive():
            return {"body": b"test data", "more_body": False}

        request = Request(method="POST", path="/", receive=mock_receive)
        body = await request.get_body()

        assert body == b"test data"

    @pytest.mark.asyncio
    async def test_get_body_multiple_chunks(self):
        chunks = [
            {"body": b"chunk1", "more_body": True},
            {"body": b"chunk2", "more_body": True},
            {"body": b"chunk3", "more_body": False},
        ]
        chunk_index = 0

        async def mock_receive():
            nonlocal chunk_index
            result = chunks[chunk_index]
            chunk_index += 1
            return result

        request = Request(method="POST", path="/", receive=mock_receive)
        body = await request.get_body()

        assert body == b"chunk1chunk2chunk3"

    @pytest.mark.asyncio
    async def test_get_body_empty(self):
        async def mock_receive():
            return {"body": b"", "more_body": False}

        request = Request(method="POST", path="/", receive=mock_receive)
        body = await request.get_body()

        assert body == b""

    @pytest.mark.asyncio
    async def test_get_body_missing_body_key(self):
        async def mock_receive():
            return {"more_body": False}

        request = Request(method="POST", path="/", receive=mock_receive)
        body = await request.get_body()

        assert body == b""

    def test_request_with_generic_type(self):
        class UserData:
            name: str
            age: int

        async def mock_receive():
            return {}

        request = Request[UserData](method="POST", path="/", receive=mock_receive)

        assert request.method == "POST"
        assert request.body is None
