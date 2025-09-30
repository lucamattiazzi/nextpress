import re

from nextpress.types import Route


def get_best_routes(pattern: str, routes: list[Route]) -> list[Route]:
    exact_matches = [route for route in routes if route.match == pattern]
    if exact_matches:
        return exact_matches
    regex_matches = [route for route in routes if re.search(pattern, route.match)]
    if regex_matches:
        return regex_matches
    return []
