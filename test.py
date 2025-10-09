import requests


def test_root():
    response = requests.get("http://localhost:8000/")
    assert response.status_code == 200
    assert response.text == "Hello, World!"
    assert "Content-Length" in response.headers
    assert int(response.headers.get("Content-Length")) == len("Hello, World!")


def test_not_found():
    response = requests.get("http://localhost:8000/nonexistent")
    assert response.status_code == 404
    assert response.text == "page not found!"


def test_api_get():
    response = requests.get("http://localhost:8000/api")
    assert response.status_code == 200
    assert response.json() == {"message": "API endpoint accessed with GET method"}
    assert response.headers.get("Content-Type") == "application/json; charset=utf-8"
    assert "Content-Length" in response.headers
    assert int(response.headers.get("Content-Length")) == len(response.text)
    assert response.headers.get("X-Processed-Time") is not None


def test_data_post():
    payload = {"name": "Alice"}
    response = requests.post("http://localhost:8000/data", json=payload)
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, Alice!"}
    assert response.headers.get("Content-Type") == "application/json; charset=utf-8"
    assert "Content-Length" in response.headers
    assert int(response.headers.get("Content-Length")) == len(response.text)


if __name__ == "__main__":
    test_root()
    test_not_found()
    test_api_get()
    test_data_post()
    print("All tests passed!")
