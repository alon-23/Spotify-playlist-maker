"""Spotify Web API helpers (stdlib only)."""

import json
import time
import urllib.error
import urllib.parse
import urllib.request

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"
SCOPE = "playlist-modify-private"
BATCH_SIZE = 100


class TokenExpired(Exception):
    """Raised when Spotify returns 401 so the caller can refresh."""


def build_authorize_url(client_id, redirect_uri):
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": SCOPE,
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"


def _token_request(form):
    data = urllib.parse.urlencode(form).encode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def exchange_code(client_id, client_secret, code, redirect_uri):
    return _token_request(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        }
    )


def refresh_access(client_id, client_secret, refresh_token):
    return _token_request(
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }
    )


def api_request(method, url, access_token, body=None, retries=4):
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(retries):
        headers = {"Authorization": f"Bearer {access_token}"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as err:
            if err.code == 401:
                raise TokenExpired()
            if err.code == 429:
                wait = int(err.headers.get("Retry-After", "1") or "1")
                time.sleep(wait)
                continue
            detail = err.read().decode(errors="replace")
            raise RuntimeError(f"Spotify {err.code}: {detail}") from err
    raise RuntimeError("Spotify rate limit: gave up after retries")


def get_me(access_token):
    return api_request("GET", f"{API_BASE}/me", access_token)


def search_track(access_token, query):
    params = urllib.parse.urlencode({"q": query, "type": "track", "limit": 1})
    result = api_request("GET", f"{API_BASE}/search?{params}", access_token)
    items = result.get("tracks", {}).get("items", [])
    return items[0] if items else None


def create_playlist(access_token, name, public=False):
    body = {"name": name, "public": public}
    return api_request("POST", f"{API_BASE}/me/playlists", access_token, body)


def unfollow_playlist(access_token, playlist_id):
    api_request("DELETE", f"{API_BASE}/playlists/{playlist_id}/followers", access_token)


def add_tracks(access_token, playlist_id, uris):
    for i in range(0, len(uris), BATCH_SIZE):
        chunk = uris[i : i + BATCH_SIZE]
        api_request(
            "POST",
            f"{API_BASE}/playlists/{playlist_id}/items",
            access_token,
            {"uris": chunk},
        )
