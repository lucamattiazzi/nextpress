from nextpress.entities import Route


def sort_routes(routes: list[Route]) -> list[Route]:
    return sorted(
        routes,
        key=lambda r: len(r.params),
    )


def extract_route_params(route: Route, path: str) -> dict[str, str]:
    if match := route.pattern.fullmatch(path):
        return match.groupdict()
    return {}


def find_best_route(routes: list[Route], method: str, path: str) -> Route | None:
    sorted_routes = sort_routes(routes)
    for route in sorted_routes:
        if route.method != method and route.method != "*":
            continue
        if route.pattern.fullmatch(path):
            return route

    return None
