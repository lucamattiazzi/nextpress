from functools import partial
from typing import Any, Callable
from urllib.parse import parse_qs


def _extract_class_generic_type(param_name: str, handlers: list[Callable]) -> type:
    all_types = set()

    for handler in handlers:
        class_instance = handler.__annotations__.get(param_name)
        if not class_instance:
            continue
        if not hasattr(class_instance, "__pydantic_generic_metadata__"):
            continue
        types = class_instance.__pydantic_generic_metadata__.get("args")
        if not types or len(types) == 0:
            continue
        all_types.add(types[0])

    if not all_types:
        return Any
    if len(all_types) == 1:
        return all_types.pop()

    raise TypeError(f"You cannot have multiple different types for {param_name}")


def extract_response_type(handlers: list[Callable]) -> type:
    return partial(_extract_class_generic_type, "response")(handlers)


def extract_request_type(handlers: list[Callable]) -> type:
    return partial(_extract_class_generic_type, "request")(handlers)


def extract_query_params(query_string: bytes) -> dict[str, str]:
    query_params = {}
    if not query_string:
        return query_params
    parsed_qs = parse_qs(query_string.decode("utf-8"))
    for key, value in parsed_qs.items():
        if len(value) == 1:
            query_params[key] = value[0]
        else:
            query_params[key] = value
    return query_params
