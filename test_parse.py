"""Unit checks for CSV parsing and search-query building."""

from csv_tracks import build_query, parse_csv

SAMPLE = (
    "Track,Artist,Album,Spotify Search URL\n"
    "Dancing Queen,ABBA,ABBA Gold,https://open.spotify.com/search/Dancing%20Queen%20ABBA\n"
    "Wannabe,Spice Girls,Spice,https://open.spotify.com/search/Wannabe%20Spice%20Girls\n"
)


def test_parses_rows():
    rows = parse_csv(SAMPLE)
    assert len(rows) == 2
    assert rows[0] == {"track": "Dancing Queen", "artist": "ABBA"}
    assert rows[1]["artist"] == "Spice Girls"


def test_tolerant_headers():
    rows = parse_csv("Song Name,Artist\nAfrica,Toto\n")
    assert rows == [{"track": "Africa", "artist": "Toto"}]


def test_missing_columns_raises():
    try:
        parse_csv("foo,bar\n1,2\n")
    except ValueError:
        return
    raise AssertionError("expected ValueError for missing track/artist columns")


def test_skips_blank_tracks():
    assert parse_csv("Track,Artist\n,ABBA\nReal Song,ABBA\n") == [
        {"track": "Real Song", "artist": "ABBA"}
    ]


def test_build_query():
    assert build_query({"track": "Dancing Queen", "artist": "ABBA"}) == '"Dancing Queen" "ABBA"'


def test_add_tracks_uses_items_endpoint():
    """Spotify's Feb 2026 migration: /tracks returns 403; must use /items."""
    import spotify

    calls = []
    original = spotify.api_request
    spotify.api_request = lambda method, url, token, body=None: calls.append(url)
    try:
        spotify.add_tracks("tok", "PID", ["spotify:track:a", "spotify:track:b"])
    finally:
        spotify.api_request = original
    assert calls == ["https://api.spotify.com/v1/playlists/PID/items"], calls


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok {name}")
    print("all checks passed")
