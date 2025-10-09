import pytest


@pytest.fixture(autouse=True)
def reset_routes():
    """Reset routes between tests to avoid state pollution"""
    from nextpress import Nextpress

    # Store original routes
    original_routes = Nextpress.routes

    yield

    # Reset routes after test
    Nextpress.routes = []
