import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode


BASE_URL = "http://127.0.0.1:8080/api/v2"


def api_get(endpoint, params=None, api_key=""):
    url = f"{BASE_URL}/{endpoint}"

    if params:
        url += "?" + urlencode(params)

    request = Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "qBittorrent Speed Monitor"
        }
    )

    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def api_post(endpoint, params=None, api_key=""):
    url = f"{BASE_URL}/{endpoint}"

    data = None
    if params:
        data = urlencode(params).encode("utf-8")

    request = Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "qBittorrent Speed Monitor"
        }
    )

    with urlopen(request, timeout=10) as response:
        return response.read().decode("utf-8")


def get_torrents(api_key):
    return api_get(
        "torrents/info",
        {"filter": "downloading"},
        api_key
    )