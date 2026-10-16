# Spotify Playlist Maker

A small local web app that reads a CSV of tracks and creates a Spotify playlist
with them. It searches Spotify for each track (name + artist), adds everything it
finds, and lists anything it couldn't match so you can add it manually.

## How it works

1. You register a free Spotify Developer app, get a Client ID + Secret, and paste
   them into the app (stored locally, never committed).
2. You log in with Spotify once (browser OAuth, redirects back to 127.0.0.1).
3. You load your CSV, click **Find tracks**, review matches/misses, name your
   playlist, and click **Create playlist**.

## CSV format

The app looks for a track column and an artist column (case-insensitive), so a
file like this works:

```csv
Track,Artist,Album,Spotify Search URL
Dancing Queen,ABBA,ABBA Gold,https://open.spotify.com/search/Dancing%20Queen%20ABBA
Wannabe,Spice Girls,Spice,https://open.spotify.com/search/Wannabe%20Spice%20Girls
```

Column names containing `track` / `title` / `song` / `name` are treated as the
track; a column containing `artist` is the artist. The trailing search-URL column
is ignored — the app builds its own queries.

## Setup

1. Go to https://developer.spotify.com/dashboard and create an app.
2. In the app settings, add this Redirect URI exactly:
   `http://127.0.0.1:5000/callback`

   Spotify rejects `http://localhost` and any plain `http://` URL. Only loopback
   IP literals (`127.0.0.1` / `[::1]`) are allowed over http, so use `127.0.0.1`,
   not `localhost`.
3. Install and run:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python app.py
   ```

4. Open http://127.0.0.1:5000, paste your Client ID and Secret, and click
   **Connect with Spotify**.

### Run it again later

After the one-time setup, every time you want to use the app:

```bash
cd spotify-playlist-maker
source .venv/bin/activate
python app.py
```

Then open http://127.0.0.1:5000 in your browser. Stop the server with Ctrl+C.

You do **not** need to repeat the venv creation, `pip install`, or credential
entry — your Client ID/Secret and Spotify login are saved locally in
`spotify_maker.json`, and the login is refreshed automatically when it expires.

## Notes

- Your credentials and Spotify tokens live in `spotify_maker.json`, which is
  **gitignored**. Never commit it.
- Playlists are created as **private** by default.
- Spotify search matches the top result for `"<track>" "<artist>"`. Obscure or
  ambiguous tracks may land in the **misses** list — use the provided search link.

## Tests

```bash
python3 test_parse.py
```
