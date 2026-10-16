"""Flask app: local Spotify playlist maker."""

import os
import time

from flask import Flask, jsonify, redirect, request, send_from_directory

import config
import csv_tracks
import spotify

REDIRECT_URI = "http://127.0.0.1:5000/callback"
SEARCH_DELAY_SECONDS = 0.2

app = Flask(__name__)


def _valid_token():
    """Return a live access token, refreshing if needed."""
    cfg = config.load_config()
    token = cfg.get("access_token")
    expiry = cfg.get("token_expiry", 0)
    if token and time.time() < expiry:
        return token
    refresh_token = cfg.get("refresh_token")
    if not refresh_token:
        raise RuntimeError("Not connected to Spotify. Click Connect first.")
    data = spotify.refresh_access(cfg["client_id"], cfg["client_secret"], refresh_token)
    _store_token(cfg, data)
    return data["access_token"]


def _store_token(cfg, data):
    cfg["access_token"] = data["access_token"]
    cfg["token_expiry"] = time.time() + data.get("expires_in", 3600) - 60
    if data.get("refresh_token"):
        cfg["refresh_token"] = data["refresh_token"]
    config.save_config(cfg)


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/api/status")
def status():
    cfg = config.load_config()
    return jsonify(
        {
            "has_credentials": bool(cfg.get("client_id") and cfg.get("client_secret")),
            "connected": bool(cfg.get("refresh_token")),
        }
    )


@app.post("/api/config")
def set_config():
    body = request.get_json(force=True)
    client_id = (body.get("client_id") or "").strip()
    client_secret = (body.get("client_secret") or "").strip()
    if not client_id or not client_secret:
        return jsonify({"error": "Client ID and Secret are required"}), 400
    cfg = config.load_config()
    cfg["client_id"] = client_id
    cfg["client_secret"] = client_secret
    config.save_config(cfg)
    return jsonify({"ok": True})


@app.get("/login")
def login():
    cfg = config.load_config()
    if not (cfg.get("client_id") and cfg.get("client_secret")):
        return redirect("/?error=missing_credentials")
    return redirect(spotify.build_authorize_url(cfg["client_id"], REDIRECT_URI))


@app.get("/callback")
def callback():
    error = request.args.get("error")
    if error:
        return redirect(f"/?error={error}")
    code = request.args.get("code")
    if not code:
        return redirect("/?error=no_code")
    cfg = config.load_config()
    data = spotify.exchange_code(
        cfg["client_id"], cfg["client_secret"], code, REDIRECT_URI
    )
    _store_token(cfg, data)
    return redirect("/?connected=1")


@app.post("/api/import")
def import_tracks():
    try:
        token = _valid_token()
    except RuntimeError as err:
        return jsonify({"error": str(err)}), 400
    body = request.get_json(force=True)
    try:
        rows = csv_tracks.parse_csv(body.get("csv", ""))
    except ValueError as err:
        return jsonify({"error": str(err)}), 400
    if not rows:
        return jsonify({"error": "No tracks found in CSV"}), 400

    matched, misses = [], []
    for row in rows:
        query = csv_tracks.build_query(row)
        try:
            track = spotify.search_track(token, query)
        except spotify.TokenExpired:
            token = _valid_token()
            track = spotify.search_track(token, query)
        if track:
            matched.append(
                {
                    "track": row["track"],
                    "artist": row["artist"],
                    "matched_name": track["name"],
                    "matched_artist": ", ".join(a["name"] for a in track["artists"]),
                    "uri": track["uri"],
                }
            )
        else:
            misses.append(
                {"track": row["track"], "artist": row["artist"], "search_url": _search_url(row)}
            )
        time.sleep(SEARCH_DELAY_SECONDS)

    return jsonify({"matched": matched, "misses": misses, "total": len(rows)})


@app.post("/api/create")
def create_playlist():
    try:
        token = _valid_token()
    except RuntimeError as err:
        return jsonify({"error": str(err)}), 400
    body = request.get_json(force=True)
    name = (body.get("name") or "").strip() or "Imported Playlist"
    uris = body.get("uris") or []
    if not uris:
        return jsonify({"error": "No matched tracks to add"}), 400

    try:
        playlist = spotify.create_playlist(token, name)
        spotify.add_tracks(token, playlist["id"], uris)
    except spotify.TokenExpired:
        token = _valid_token()
        playlist = spotify.create_playlist(token, name)
        spotify.add_tracks(token, playlist["id"], uris)

    return jsonify(
        {
            "name": name,
            "count": len(uris),
            "url": playlist["external_urls"]["spotify"],
        }
    )


def _search_url(row):
    from urllib.parse import quote

    return f"https://open.spotify.com/search/{quote(row['track'] + ' ' + row['artist'])}"


if __name__ == "__main__":
    app.run(port=5000, debug=True)
