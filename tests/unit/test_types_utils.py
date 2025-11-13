from typing import Any

import pytest
from pydantic import BaseModel

from nextpress.entities import Request, Response
from nextpress.utils.types import (
    extract_query_params,
    extract_request_type,
    extract_response_type,
)


class TestExtractQueryParams:
    def test_empty_query_string(self):
        result = extract_query_params(b"")
        assert result == {}

    def test_single_param(self):
        result = extract_query_params(b"key=value")
        assert result == {"key": "value"}

    def test_multiple_params(self):
        result = extract_query_params(b"key1=value1&key2=value2")
        assert result == {"key1": "value1", "key2": "value2"}

    def test_param_with_multiple_values(self):
        result = extract_query_params(b"key=value1&key=value2")
        assert result == {"key": ["value1", "value2"]}

    def test_url_encoded_params(self):
        result = extract_query_params(b"name=John%20Doe&age=30")
        assert result == {"name": "John Doe", "age": "30"}

    def test_mixed_single_and_multiple_values(self):
        result = extract_query_params(b"single=value&multi=a&multi=b&another=test")
        assert result == {"single": "value", "multi": ["a", "b"], "another": "test"}


class UserData(BaseModel):
    name: str
    age: int


class TestExtractRequestType:
    def test_no_request_annotation(self):
        async def handler():
            pass

        result = extract_request_type([handler])
        assert result == Any

    def test_request_without_generic(self):
        async def handler(request: Request):
            pass

        result = extract_request_type([handler])
        assert result == Any

    def test_request_with_generic_type(self):
        async def handler(request: Request[UserData]):
            pass

        result = extract_request_type([handler])
        assert result == UserData

    def test_multiple_handlers_same_type(self):
        async def handler1(request: Request[UserData]):
            pass

        async def handler2(request: Request[UserData]):
            pass

        result = extract_request_type([handler1, handler2])
        assert result == UserData

    def test_multiple_handlers_mixed_types_raises_error(self):
        class OtherData(BaseModel):
            value: str

        async def handler1(request: Request[UserData]):
            pass

        async def handler2(request: Request[OtherData]):
            pass

        with pytest.raises(TypeError, match="multiple different types"):
            extract_request_type([handler1, handler2])

    def test_handlers_with_and_without_types(self):
        async def handler1(request: Request[UserData]):
            pass

        async def handler2(request: Request):
            pass

        result = extract_request_type([handler1, handler2])
        assert result == UserData


class ResponseData(BaseModel):
    message: str


class TestExtractResponseType:
    def test_no_response_annotation(self):
        async def handler():
            pass

        result = extract_response_type([handler])
        assert result == Any

    def test_response_without_generic(self):
        async def handler(response: Response):
            pass

        result = extract_response_type([handler])
        assert result == Any

    def test_response_with_generic_type(self):
        async def handler(response: Response[ResponseData]):
            pass

        result = extract_response_type([handler])
        assert result == ResponseData

    def test_multiple_handlers_same_type(self):
        async def handler1(response: Response[ResponseData]):
            pass

        async def handler2(response: Response[ResponseData]):
            pass

        result = extract_response_type([handler1, handler2])
        assert result == ResponseData

    def test_multiple_handlers_mixed_types_raises_error(self):
        class OtherResponse(BaseModel):
            data: str

        async def handler1(response: Response[ResponseData]):
            pass

        async def handler2(response: Response[OtherResponse]):
            pass

        with pytest.raises(TypeError, match="multiple different types"):
            extract_response_type([handler1, handler2])
