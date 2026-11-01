import httpx


def main() -> None:
    url = "https://jsonplaceholder.typicode.com/posts/1"

    response = httpx.get(url, timeout=10.0)

    print("Status:", response.status_code)
    print("Content-Type:", response.headers.get("content-type"))

    response.raise_for_status()

    data = response.json()
    print("ID:", data["id"])
    print("Title:", data["title"])


if __name__ == "__main__":
    main()